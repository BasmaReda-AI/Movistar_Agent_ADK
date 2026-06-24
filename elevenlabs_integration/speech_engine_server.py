"""
ElevenLabs Speech Engine Server — ADK Integration

This server:
  1. Creates a Speech Engine resource with your ngrok URL
  2. Listens for voice transcripts from ElevenLabs
  3. Calls the ADK multi-agent system (via AgentAdapter) to generate responses
  4. Streams the response back as speech

How to run:
  1. ngrok http 3001              (in one terminal)
  2. python speech_engine_server.py   (in another terminal, paste ngrok URL)
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

# ── File logging helper (writes directly to log file, bypassing stdout issues) ──
_ENGINE_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "engine_server.log")

def _file_log(msg):
    """Append a message directly to engine_server.log. Always works."""
    with open(_ENGINE_LOG, "a", buffering=1) as f:
        f.write(msg + "\n")
        f.flush()

_file_log("=== Engine server starting ===")

# ── Monkey-patch SpeechEngineSession to log WebSocket messages ──
import elevenlabs.speech_engine.session as _ses_mod
import websockets.exceptions as _ws_exc

# Patch _handle_message to log incoming message types
_orig_handle_message = _ses_mod.SpeechEngineSession._handle_message

async def _patched_handle_message(self, msg):
    msg_type = msg.get("type", "?")
    msg_eid = msg.get("event_id", "?")
    _file_log(f"[WS RECV] type={msg_type} event_id={msg_eid}")
    print(f"  [WS RECV] type={msg_type} event_id={msg_eid}", flush=True)
    await _orig_handle_message(self, msg)

_ses_mod.SpeechEngineSession._handle_message = _patched_handle_message

# Patch _send to log outgoing messages
_orig_send = _ses_mod.SpeechEngineSession._send

async def _patched_send(self, msg_dict):
    msg_type = msg_dict.get("type", "?")
    content_preview = str(msg_dict.get("content", ""))[:50]
    is_final = msg_dict.get("is_final", "?")
    _file_log(f"[WS SEND] type={msg_type} is_final={is_final} content=\"{content_preview}\"")
    print(f"  [WS SEND] type={msg_type} is_final={is_final} content=\"{content_preview}\"", flush=True)
    await _orig_send(self, msg_dict)

_ses_mod.SpeechEngineSession._send = _patched_send

# Patch the actual recv on the websocket connection to log close codes
# We monkey-patch the wrap function that creates WebSocketLike objects
_orig_wrap = _ses_mod.wrap_websocket

def _patched_wrap(ws):
    """Wrap a WebSocket and intercept recv errors."""
    orig_recv = ws.recv

    async def _patched_recv():
        try:
            return await orig_recv()
        except _ws_exc.ConnectionClosed as e:
            _file_log(f"[!!] WS recv ConnectionClosed: code={e.code} reason=\"{e.reason}\"")
            print(f"  [!!] WS recv ConnectionClosed: code={e.code} reason=\"{e.reason}\"", flush=True)
            raise
        except Exception as e:
            print(f"  [!!] WS recv error: {type(e).__name__}: {e}", flush=True)
            raise

    ws.recv = _patched_recv
    return _orig_wrap(ws)

_ses_mod.wrap_websocket = _patched_wrap

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

# Singleton AgentAdapter (reused across voice sessions)
adapter = AgentAdapter()


# ── Helpers ─────────────────────────────────────────────────────────


def _load_voice_context():
    """Load prior text chat history from voice_context.json (if any).

    This file is written by api.py's POST /api/set-voice-context endpoint
    when the frontend starts a voice session, bridging text→voice continuity.
    """
    context_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "voice_context.json"
    )
    if os.path.exists(context_file):
        try:
            with open(context_file, "r") as f:
                data = json.load(f)
                return data.get("messages", [])
        except Exception:
            pass
    return []


# ── Callbacks ──────────────────────────────────────────────────────


async def on_init(conversation_id, session):
    """Called when a new conversation session starts.
    
    With WebRTC, the first message is sent from the client (frontend)
    via the startSession() `firstMessage` override, so we don't send
    anything here. We just log and wait for the user's first utterance.
    """
    _file_log(f"[+] on_init called! conversation_id={conversation_id}")
    print(f"\n[+] Session started: {conversation_id}")


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
        _file_log("[!!] Empty transcript")
        print("  [!!] Empty transcript — nothing to respond to.")
        return

    user_message = messages[-1]["content"]
    _file_log(f"[on_transcript] User: {user_message[:80]}...")
    print(f"  [User] {user_message[:80]}...")
    print(f"  [LLM] Calling ADK agent...")

    try:
        # Use a fixed voice session ID so the agent maintains conversation state
        # across back-and-forth turns within a single voice call.
        response_text = await adapter.chat(user_message, session_id="voice")

        if not response_text:
            _file_log("[!] Agent returned empty response")
            print("  [!] Agent returned empty response, sending fallback.")
            response_text = (
                "I'm sorry, I didn't quite catch that. Could you please repeat?"
            )

        _file_log(f"[on_transcript] Agent response: {response_text[:100]}...")
        print(f"  [Agent] {response_text[:100]}...")

        # Chunk the response into words so ElevenLabs TTS can start
        # speaking immediately instead of waiting for the full text.
        words = response_text.split()
        total_words = len(words)
        _file_log(f"[on_transcript] Streaming {total_words} words...")
        print(f"  [+] Streaming {total_words} words to ElevenLabs...")

        async def generate():
            # Yield words in small groups (4-6 words per chunk) for smooth TTS
            chunk_size = 5
            for i in range(0, total_words, chunk_size):
                chunk = " ".join(words[i : i + chunk_size])
                # Trailing space keeps the word at a chunk boundary from fusing
                # with the next chunk's first word ("...how are" + "you?..." would
                # otherwise become "areyou?").
                yield chunk + " "
                # Small delay to let TTS engine breathe (non-blocking)
                await asyncio.sleep(0.05)

        await session.send_response(generate())
        _file_log("[on_transcript] Response streamed to ElevenLabs")
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
    _file_log(f"[*] on_close: {session.conversation_id}")
    print(f"  [*] Session ended: {session.conversation_id}")


def on_disconnect(session):
    """Called when the WebSocket drops unexpectedly."""
    _file_log(f"[!] on_disconnect: {session.conversation_id}")
    print(f"  [!] Session disconnected: {session.conversation_id}")


def on_error(err, session):
    """Called on protocol or WebSocket errors."""
    _file_log(f"[!] on_error: {err}")
    print(f"  [!] Error: {err}")


# ── Main ───────────────────────────────────────────────────────────


async def main(ngrok_url=None):
    elevenlabs = AsyncElevenLabs(api_key=ELEVENLABS_API_KEY)

    # Clear previous transcript file
    if os.path.exists(TRANSCRIPT_FILE):
        os.remove(TRANSCRIPT_FILE)

    # 1. Get the ngrok URL (from argument or prompt)
    if not ngrok_url:
        print("\n" + "=" * 60)
        print("  ElevenLabs Speech Engine Server (ADK Integration)")
        print("=" * 60)
        print("\nMake sure ngrok is running in another terminal:")
        print("  ngrok http 3001")
        print()
        ngrok_url = input("  Paste your ngrok HTTPS URL: ").strip()

    # Convert https:// → wss:// and append /ws
    ws_url = ngrok_url.replace("https://", "wss://").replace("http://", "wss://")
    if not ws_url.endswith("/ws"):
        ws_url = ws_url.rstrip("/") + "/ws"
    _file_log(f"[main] WebSocket URL: {ws_url}")
    print(f"\n  [*] WebSocket URL: {ws_url}")

    # 2. Create a Speech Engine resource
    _file_log("[main] Creating Speech Engine resource...")
    print(f"\n  [*] Creating Speech Engine resource...")
    try:
        engine = await elevenlabs.speech_engine.create(
            name="ADK Demo Speech Engine",
            speech_engine={"ws_url": ws_url},
            overrides={"first_message": True},
        )
        engine_id = engine.engine_id
        _file_log(f"[main] Engine created: {engine_id}")
        print(f"  [+] Speech Engine created! ID: {engine_id}")

        # Save engine ID for the API server to use
        engine_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(engine_dir, ".engine_id"), "w") as f:
            f.write(engine_id)
        print(f"  [*] Engine ID saved to .engine_id")

    except Exception as e:
        print(f"  [!] Failed to create Speech Engine: {e}")
        print("\n  Possible issues:")
        print("    - Is ngrok running and pointing to port 3001?")
        print("    - Is the URL correct? (should look like https://xxx.ngrok-free.app)")
        print("    - Is your ElevenLabs API key valid?")
        sys.exit(1)

    # 3. Start the server
    _file_log("[main] Starting server on port 3001 with overrides.first_message=True")
    print(f"\n  [*] Starting Speech Engine server on port 3001...")
    print(f"  Press Ctrl+C to stop\n")

    await engine.serve(
        port=3001,
        path="/ws",
        debug=True,
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
        "--url", help="ngrok HTTPS URL (e.g., https://xxx.ngrok-free.app)"
    )
    args = parser.parse_args()

    try:
        asyncio.run(main(ngrok_url=args.url))
    except KeyboardInterrupt:
        print("\n\n[*] Server stopped. See you next time!")
