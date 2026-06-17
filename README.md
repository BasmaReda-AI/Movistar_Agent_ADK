# Movistar Outbound Sales — ElevenLabs Voice + Google ADK

Voice-powered outbound sales agent for Movistar Mexico. Uses **ElevenLabs Conversational AI** for real-time speech and **Google ADK** for multi-agent orchestration (greeting → sales pitch with full 22-category objection matrix).

```
Customer speaks
  → ElevenLabs ASR → WebSocket → speech_engine_server
  → agent_adapter (ADK Runner) → root_agent (greeting)
     → identity confirmation + availability check
     → transfer_to_agent (ADK built-in) ──▶ sales_specialist
        → engagement hook
           ↳ Objection Matrix rebuttal (if objection raised)
        → primary offer pitch
           ↳ Objection Matrix rebuttal (if pitch-phase objection)
           ↳ value build rebuttal (price hesitation)
           ↳ downsell pitch (primary rejected)
        → explicit acceptance → warm handoff → transfer_to_human_agent → end_call
```

## Scenarios covered

| ID | Path |
|---|---|
| A-01 | Primary offer accepted on first pitch |
| A-02 | Primary offer accepted after value build rebuttal |
| A-03 | Downsell accepted (primary + value build both rejected) |
| A-04 | Offer accepted after hook-phase objection (Phase 0) |
| A-05 | Downsell accepted after pitch-phase objection (Phase 1) |

Off-path replies (wrong number, busy, any final decline) each get one polite closing line + `end_call` so the session never gets stuck.

## Structure

```
ADK-Migration/
├── elevenlabs_integration/
│   ├── .env                       # ElevenLabs + LiteLLM credentials (not committed)
│   ├── requirements.txt
│   ├── run_demo.ps1               # One-click launcher (ngrok → engine → FastAPI)
│   ├── cleanup.ps1                # Stops all processes
│   ├── agent_adapter.py           # Wraps ADK Runner for voice pipeline
│   ├── speech_engine_server.py    # ElevenLabs Speech Engine server
│   ├── api.py                     # FastAPI backend (chat, signed-url, voice context)
│   ├── test_adapter.py            # AgentAdapter unit test
│   └── static/
│       ├── index.html             # Main page (loads ElevenLabs SDK + UI)
│       ├── app.js                 # Voice chat UI with ElevenLabs SDK
│       ├── elevenlabs-error-shim.js  # Crash guard for malformed SDK error frames
│       └── style.css
├── movistar_agent/
   ├── __init__.py                # exports root_agent
   ├── agent.py                   # greeting_agent (root) + sales_specialist sub-agent
   ├── config.py                  # SYSTEM_STATE: customer CRM data, offer keys, model
   ├── prompts.py                 # GREETING_INSTRUCTION + SALES_INSTRUCTION (full happy path)
   ├── tools.py                   # query_offers_kb, query_objection_matrix,
   │                              # trigger_oferta_alterna, transfer_to_human_agent, end_call
   └── kb/
       ├── offers_kb.py           # primary (40 GB) and downsell (25 GB) plan data
       └── objection_matrix.py    # 22-category rebuttal matrix with verbatim scripts

```

## Setup

### 1. Environment

Create a `.env` file in `elevenlabs_integration/`:

```env
ELEVENLABS_API_KEY=sk-your-elevenlabs-key
LITELLM_API_KEY=sk-your-litellm-key
LITELLM_API_BASE=https://your-litellm-proxy/v1
MODEL=gemini/gemini-2.5-flash
```

### 2. Install

```powershell
pip install -r elevenlabs_integration\requirements.txt
```

### 3. Run

> **Note:** Use `run_demo.ps1` inside `elevenlabs_integration/`. The old `run.bat` and `run.ps1` at the project root are from the original ADK-only setup and are obsolete — they launch the text-based `adk web` interface instead of the voice pipeline.

```powershell
.\elevenlabs_integration\run_demo.ps1
```

This starts:
1. **ngrok** — public tunnel to the local server
2. **Speech Engine** — ElevenLabs Conversational AI agent pointing to the ngrok URL
3. **FastAPI** server at `http://localhost:8501`

Your browser opens automatically. Click **Voz** to start a voice session.

### 4. Cleanup

```powershell
.\elevenlabs_integration\cleanup.ps1
```

## Demo script — voice

| You say | Agent should |
|---|---|
| *hello* | Greeting agent asks: *"Good morning, am I speaking with \[Name\]?"* |
| *yes, speaking* | Asks for availability |
| *sure, go ahead* | Transfers to `sales_specialist` → engagement hook |
| *yes, tell me* | Queries Offers KB → full pitch |
| *sounds good, let's do it* | Warm handoff → `transfer_to_human_agent` → `end_call` |

**Objection during hook (A-04 path):**

| You say | Agent should |
|---|---|
| *I had a bad experience with Movistar* | Calls `query_objection_matrix(BAD_PAST_EXPERIENCE)` → rebuttal |
| *ok, tell me more* | Proceeds to pitch → acceptance → handoff |

## Objection Matrix

22 categories covering the most common prepaid customer objections:

| Key | Triggers |
|---|---|
| `TOO_EXPENSIVE` | costly, high price, can't afford it |
| `NO_MONTHLY_BILL` | don't want bills, no commitments |
| `PREFER_PREPAID_CONTROL` | prefer prepaid, control spending |
| `BAD_PAST_EXPERIENCE` | bad experience, overcharged, complaint |
| `NO_COMMITMENT` | no contracts, no permanence |
| `NO_TIME` | busy, driving, in a meeting |
| `SATISFIED_WITH_RECHARGES` | happy with prepaid, don't want to change |
| `ONLY_USES_MINUTES` | only calls, no data needed |
| `UNEMPLOYED` | no income, looking for work |
| `PREPAID_COMPARISON` | package duration, number ownership |
| `GOING_ON_TRIP` | traveling, going abroad |
| `KEYPAD_PHONE` | basic phone, no smartphone |
| `BAD_COVERAGE` | bad signal, calls drop, Ookla |
| `BAD_SIGNAL_ROAMING` | rural/indoor signal, roaming |
| `LINE_FOR_MINOR` | line for a child or minor |
| `OCCASIONAL_USE` | rarely uses it, emergencies only |
| `CLOSING_TRUST` | suspicious of call, SUBTEL |
| `NOT_LEGAL_OWNER` | not the account holder |
| `DISTRUST_FRAUD` | fears scam, won't give info |
| `PROCESS_HESITATION` | doesn't understand activation |
| `RECHARGE_18500` | $18,500 prepaid package |
| `FEAR_OF_BILL_INCREASES` | hidden charges, price hikes |

Each category has 1–4 arguments. `query_objection_matrix(key, argument=N)` returns the verbatim rebuttal with the customer name already substituted.

## Architecture

```
┌─────────────┐     ElevenLabs SDK      ┌──────────────────────┐
│  Browser    │ ◄──── WebRTC ─────────► │ ElevenLabs Convers.  │
│  (voice UI) │                         │  AI (Speech Engine)  │
└─────────────┘                         └──────────┬───────────┘
                                                    │ WebSocket
                                                    ▼
┌───────────────────────────────────────────────────────────────┐
│  speech_engine_server.py   (port 3001, ngrok-tunneled)        │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  agent_adapter.py  →  ADK Runner  →  movistar_agent/   │  │
│  │                       (multi-agent)   (root + sub-agent)│  │
│  └─────────────────────────────────────────────────────────┘  │
│  ▲ FastAPI  (port 8501) — chat history, signed URLs           │
└───────────────────────────────────────────────────────────────┘
```
