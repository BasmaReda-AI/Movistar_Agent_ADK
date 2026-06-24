"""
ElevenLabs Speech Engine Server — ADK Integration

This server:
  1. Creates a Speech Engine resource with your tunnel URL
  2. Listens for voice transcripts from ElevenLabs
  3. Calls the ADK multi-agent system (via AgentAdapter) to generate responses
  4. Streams the response back as speech

How to run:
  1. cloudflared tunnel --url http://localhost:3001   (in one terminal)
  2. python speech_engine_server.py   (in another terminal, paste the tunnel URL)
  3. The engine_id is printed and saved to .engine_id
"""

import argparse
import asyncio
import json
import os
import sys
import time as _time

from dotenv import load_dotenv
from elevenlabs import AsyncElevenLabs
from agent_adapter import AgentAdapter

# Load API keys from .env
load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

if not ELEVENLABS_API_KEY:
    print("[!] Missing ELEVENLABS_API_KEY in .env file")
    sys.exit(1)

# Shared transcript file for syncing (optional, mirrors reference)
TRANSCRIPT_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "voice_transcript.json"
)

# Voice context file (bridged from text chat by api.py)
VOICE_CONTEXT_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "voice_context.json"
)

# Singleton AgentAdapter (reused across voice sessions)
adapter = AgentAdapter()


# ── Helpers ─────────────────────────────────────────────────────────


def _load_voice_context():
    """Load prior text chat history from voice_context.json (once) then delete it.

    This file is written by api.py's POST /api/set-voice-context endpoint
    when the frontend starts a voice session, bridging text→voice continuity.
    The file is removed after reading so it only affects the first voice turn
    and stale data never leaks across sessions.
    """
    if os.path.exists(VOICE_CONTEXT_FILE):
        try:
            with open(VOICE_CONTEXT_FILE, "r") as f:
                data = json.load(f)
            messages = data.get("messages", [])
            # Remove the file — context is loaded once, never again
            os.remove(VOICE_CONTEXT_FILE)
            print(f"  [voice-context] Loaded {len(messages)} context messages, file deleted")
            return messages
        except Exception as e:
            print(f"  [!] Error loading voice context: {e}")
    return []


# ── Callbacks ──────────────────────────────────────────────────────


async def on_init(conversation_id, session):
    print(f"\n[+] Session started: {conversation_id}")

    # Reset the ADK agent session so it has no memory of prior calls
    adapter.reset_session(session_id="voice")
    print(f"  [on_init] ADK session reset")


async def on_transcript(transcript, session):
    """
    Called when the user speaks and ElevenLabs sends us the transcript.

    The *transcript* is a list of messages (full conversation history).
    Each message has: .role ("user" | "agent") and .content (string).

    This callback:
      1. Loads any text chat context from voice_context.json
      2. Calls AgentAdapter.chat() with the latest user transcript
      3. Streams the agent's response back to ElevenLabs for TTS
    """
    # Load prior text chat history (bridged from text UI)
    text_history = _load_voice_context()

    # Build the voice message list from the transcript
    voice_messages = [
        {"role": "assistant" if m.role == "agent" else "user", "content": m.content}
        for m in transcript
    ]
    messages = text_history + voice_messages

    # The last message should be the user's current utterance
    if not messages:
        print("  [!!] Empty transcript — nothing to respond to.")
        return

    user_message = messages[-1]["content"]
    print(f"  [User] {user_message[:80]}...")
    print(f"  [LLM] Calling ADK agent...")

    try:
        # Use a fixed voice session ID so the agent maintains conversation state
        # across back-and-forth turns within a single voice call.
        response_text = await adapter.chat(user_message, session_id="voice")

        if not response_text:
            print("  [!] Agent returned empty response, sending fallback.")
            response_text = (
                "I'm sorry, I didn't quite catch that. Could you please repeat?"
            )

        print(f"  [Agent] {response_text[:100]}...")

        # Chunk the response into words so ElevenLabs TTS can start
        # speaking immediately instead of waiting for the full text.
        words = response_text.split()
        total_words = len(words)
        print(f"  [+] Streaming {total_words} words to ElevenLabs...")

        async def generate():
            # Yield words in small groups (4-6 words per chunk) for smooth TTS.
            # Each chunk ends with a trailing space so that when the chunks are
            # concatenated downstream the word at a chunk boundary stays
            # separated (otherwise "...how are" + "you?..." fuses to "areyou?").
            chunk_size = 5
            for i in range(0, total_words, chunk_size):
                chunk = " ".join(words[i : i + chunk_size])
                yield chunk + " "
                # Small delay to let TTS engine breathe (non-blocking)
                await asyncio.sleep(0.05)

        await session.send_response(generate())
        print(f"  [+] Response streamed to ElevenLabs")

        # Save transcript to shared file (optional, for debugging)
        try:
            save_messages = [
                {"role": "assistant" if m.role == "agent" else "user", "content": m.content}
                for m in transcript
            ]
            with open(TRANSCRIPT_FILE, "w") as f:
                json.dump({"messages": save_messages, "updated_at": _time.time()}, f)
        except Exception as e:
            print(f"  [!] Failed to save transcript: {e}")

    except Exception as e:
        print(f"  [!] ADK agent error: {e}")
        await session.send_response(
            "Sorry, I had trouble processing that. Could you try again?"
        )


def on_close(session):
    """Called when the conversation ends cleanly."""
    print(f"  [*] Session ended: {session.conversation_id}")


def on_disconnect(session):
    """Called when the WebSocket drops unexpectedly."""
    print(f"  [!] Session disconnected: {session.conversation_id}")


def on_error(err, session):
    """Called on protocol or WebSocket errors."""
    print(f"  [!] Error: {err}")


# ── Main ───────────────────────────────────────────────────────────


async def main(tunnel_url=None):
    elevenlabs = AsyncElevenLabs(api_key=ELEVENLABS_API_KEY)

    # Clear previous transcript file
    if os.path.exists(TRANSCRIPT_FILE):
        os.remove(TRANSCRIPT_FILE)

    # 1. Get the tunnel URL (from argument or prompt)
    if not tunnel_url:
        print("\n" + "=" * 60)
        print("  ElevenLabs Speech Engine Server (ADK Integration)")
        print("=" * 60)
        print("\nMake sure cloudflared is running in another terminal:")
        print("  cloudflared tunnel --url http://localhost:3001")
        print()
        tunnel_url = input("  Paste your tunnel HTTPS URL: ").strip()

    # Convert https:// → wss:// and append /ws
    ws_url = tunnel_url.replace("https://", "wss://").replace("http://", "wss://")
    if not ws_url.endswith("/ws"):
        ws_url = ws_url.rstrip("/") + "/ws"
    print(f"\n  [*] WebSocket URL: {ws_url}")

    # 2. Create a Speech Engine resource
    print(f"\n  [*] Creating Speech Engine resource...")
    try:
        engine = await elevenlabs.speech_engine.create(
            name="ADK Demo Speech Engine",
            speech_engine={"ws_url": ws_url},
            overrides={"first_message": True},
        )
        engine_id = engine.engine_id
        print(f"  [+] Speech Engine created! ID: {engine_id}")

        # Save engine ID for the API server to use
        engine_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(engine_dir, ".engine_id"), "w") as f:
            f.write(engine_id)
        print(f"  [*] Engine ID saved to .engine_id")

    except Exception as e:
        print(f"  [!] Failed to create Speech Engine: {e}")
        print("\n  Possible issues:")
        print("    - Is cloudflared running and pointing to port 3001?")
        print("    - Is the URL correct? (should look like https://xxx.trycloudflare.com)")
        print("    - Is your ElevenLabs API key valid?")
        sys.exit(1)

    # 3. Start the server
    print(f"\n  [*] Starting Speech Engine server on port 3001...")
    print(f"  Press Ctrl+C to stop\n")

    await engine.serve(
        port=3001,
        path="/ws",
        on_init=on_init,
        on_transcript=on_transcript,
        on_close=on_close,
        on_disconnect=on_disconnect,
        on_error=on_error,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ElevenLabs Speech Engine Server (ADK Integration)"
    )
    parser.add_argument(
        "--url", help="Tunnel HTTPS URL (e.g., https://xxx.trycloudflare.com)"
    )
    args = parser.parse_args()

    try:
        asyncio.run(main(tunnel_url=args.url))
    except KeyboardInterrupt:
        print("\n\n[*] Server stopped. See you next time!")
