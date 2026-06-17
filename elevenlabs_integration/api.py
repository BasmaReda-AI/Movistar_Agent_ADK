"""
FastAPI backend for ADK-powered ElevenLabs Speech Engine integration.

Provides REST API endpoints for:
  - Text chat (via AgentAdapter → ADK multi-agent system)
  - Voice engine signed URLs (for ElevenLabs Speech Engine)
  - Engine ID retrieval (for debugging)
  - Voice context bridging (text → voice session continuity)
"""

import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from elevenlabs import ElevenLabs
from agent_adapter import AgentAdapter

# Load environment variables
load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Engine ID and context files
ENGINE_DIR = Path(__file__).parent
ENGINE_ID_FILE = ENGINE_DIR / ".engine_id"
VOICE_CONTEXT_FILE = ENGINE_DIR / "voice_context.json"

# Singleton AgentAdapter (shared across requests)
adapter = AgentAdapter()

# ── Models ──────────────────────────────────────────────────────────


class ChatRequest(BaseModel):
    message: str
    history: list = []  # [{role: "user"|"assistant", content: str}]
    session_id: str = "default"


class ChatResponse(BaseModel):
    response: str


class EngineIdResponse(BaseModel):
    engine_id: str


class VoiceContextRequest(BaseModel):
    history: list = []  # [{role: str, content: str}]


# ── FastAPI App ────────────────────────────────────────────────────

app = FastAPI(title="ElevenLabs + ADK Integration", version="1.0.0")

# CORS — allow any origin (local frontends, ngrok, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ──────────────────────────────────────────────────────────


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Chat endpoint: accepts a user message, optional conversation history,
    and a session_id. Uses AgentAdapter to route the message through the
    ADK multi-agent system and returns the agent's response.
    """
    try:
        # The ADK InMemorySessionService already maintains conversation
        # state internally. We only need to send the latest user message.
        # The `history` from the frontend is used only for the initial
        # page-load context seeding (via the set-voice-context endpoint).
        response_text = await adapter.chat(request.message, request.session_id)
        return ChatResponse(response=response_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/signed-url")
async def get_signed_url():
    """
    Get a WebRTC conversation token for the ElevenLabs Speech Engine.
    The frontend uses this token to start a WebRTC voice session.

    Reads the engine_id from .engine_id file (created by speech_engine_server.py).
    """
    if not ENGINE_ID_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="Engine ID not found. Start speech_engine_server.py first.",
        )

    if not ELEVENLABS_API_KEY:
        raise HTTPException(status_code=500, detail="Missing ELEVENLABS_API_KEY")

    try:
        with open(ENGINE_ID_FILE, "r") as f:
            engine_id = f.read().strip()

        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        result = client.conversational_ai.conversations.get_webrtc_token(
            agent_id=engine_id,
        )
        return {"token": result.token, "engine_id": engine_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/engine-id")
async def get_engine_id():
    """Get the engine ID (for debugging)."""
    if not ENGINE_ID_FILE.exists():
        raise HTTPException(status_code=404, detail="Engine ID not found")
    try:
        with open(ENGINE_ID_FILE, "r") as f:
            engine_id = f.read().strip()
        return EngineIdResponse(engine_id=engine_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/set-voice-context")
async def set_voice_context(request: VoiceContextRequest):
    """
    Save the current text chat history so the voice LLM can see it.
    Called by the frontend just before starting a voice session.
    """
    try:
        with open(VOICE_CONTEXT_FILE, "w") as f:
            json.dump({"messages": request.history}, f)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Serve static files ──────────────────────────────────────────────

static_path = ENGINE_DIR / "static"
if static_path.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(static_path), html=True),
        name="static",
    )

# ── Entry point ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8501"))
    print(f"[API] Starting FastAPI server on http://0.0.0.0:{port}")
    print(f"[API] Engine dir: {ENGINE_DIR}")
    uvicorn.run(app, host="0.0.0.0", port=port)
