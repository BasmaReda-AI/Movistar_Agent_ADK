# Code Review — ElevenLabs + ADK Integration

**Reviewer:** Jimmy (Code Review Subagent)  
**Date:** 2026-06-17  
**Verdict:** **FAIL** — 3 HIGH-severity issues, 7 MEDIUM-severity issues found

---

## Verdict

**FAIL** — This codebase has a hardcoded API key in `.env`, an insecure default CORS configuration (credentials + wildcard origin), and a `google-adk` dependency with no version pin that risks breaking on upstream changes. Several medium-severity issues around shared mutable state and race conditions across concurrent voice sessions also need attention before production use.

---

## Issues by File

---

### 1. `agent_adapter.py`

| Line(s) | Severity | Description |
|---------|----------|-------------|
| 113–119 | **MEDIUM** | **Race condition in `reset_session()`:** Replaces `_session_service` and `_runner` in two separate assignments. If two coroutines call `reset_session()` simultaneously (e.g., two concurrent voice sessions), they can interleave — one reads the old runner while the other has already replaced the session service, causing state corruption. **Fix:** Use `asyncio.Lock` to guard the swap, or make the adapter fully stateless. |
| 58–64, 96–101 | **MEDIUM** | **No timeout on `run_async()`:** The `async for` loop can hang indefinitely if the ADK agent stalls or enters an infinite tool loop. The caller has no way to cancel. **Fix:** Use `asyncio.wait_for(..., timeout=30)` around the async iteration, or pass a timeout to the runner. |
| 90 | **MEDIUM** | **Unvalidated `role` value in `set_context()`:** The `role` from the history dict is passed directly to `types.Content(role=role)`. If the history contains `"assistant"` instead of `"model"`, the ADK / google-genai SDK may reject it (the genai SDK uses `"user"` / `"model"` roles). **Fix:** Map `"assistant"` → `"model"` and validate before constructing Content. |
| 133 | **LOW** | **Bare `except Exception: pass` in `_create_session_if_not_exists()`:** Swallows ALL exceptions including `TypeError`, `ValueError`, etc. If `create_session()` fails for a reason other than "session exists" (e.g., invalid `app_name`), it's silently ignored. **Fix:** Catch only the specific expected exception (e.g., `ValueError` or inspect the error message from the ADK). |
| 71 | **LOW** | **Empty string returned on error in `chat()`:** The caller cannot distinguish between "agent produced no final response" and "exception occurred." The voice server already has a fallback message, but this makes debugging harder. **Fix:** Either log with more detail or raise a custom exception. |

---

### 2. `api.py`

| Line(s) | Severity | Description |
|---------|----------|-------------|
| 66–72 | **HIGH** | **`allow_origins=["*"]` with `allow_credentials=True` is invalid CORS:** Per the Fetch spec, when the origin is `*`, the `Access-Control-Allow-Credentials` header must be `false`. Browsers will reject the response if credentials (cookies, auth headers) are attempted. **Fix:** Either set `allow_credentials=False` or specify explicit origins (e.g., `["http://localhost:8501", "https://*.ngrok-free.app"]`). |
| 144–147 | **MEDIUM** | **No file locking on `voice_context.json`:** This endpoint writes to a shared file that `speech_engine_server.py` reads concurrently. Two rapid calls (or a write + read race) can cause lost updates or partial reads. **Fix:** Use a file-based lock (`portalocker` on Windows) or switch to an in-memory store (e.g., a dict in a shared subprocess or Redis). |
| 93, 122, 135, 149 | **LOW** | **Internal exception details leaked in HTTP 500 responses:** `raise HTTPException(status_code=500, detail=str(e))` can expose internal stack traces or implementation details to the client. **Fix:** Log the full exception server-side and return a generic message like `"Internal server error"`. |
| 108 | **LOW** | **Placeholder API key not detected:** The code checks `if not ELEVENLABS_API_KEY` but the default `.env` value is `sk-your-key-here` — which is truthy but invalid. **Fix:** Add a check for placeholder values or validate the key format. |
| — | **LOW** | **No rate limiting:** The `/api/chat` endpoint has no rate limiting, making it trivially abusable. **Fix:** Add `slowapi` or FastAPI middleware rate limiting for a production deployment. |

---

### 3. `speech_engine_server.py`

| Line(s) | Severity | Description |
|---------|----------|-------------|
| 42 | **MEDIUM** | **Shared mutable singleton across voice sessions:** `adapter = AgentAdapter()` is a module-level singleton. If multiple concurrent voice calls hit `on_transcript`, they share the same `InMemorySessionService` and `Runner`. Combined with the race in `reset_session()`, this can cause cross-talk between different callers. **Fix:** Use a pool of adapters or a per-session adapter — see also the race condition in `agent_adapter.py:113-119`. |
| 109 | **MEDIUM** | **Fixed `session_id="voice"` for all sessions:** All voice conversations use the same session ID. Two simultaneous calls will share ADK conversation state, causing users to hear each other's context. **Fix:** Use a unique session ID per voice session (e.g., derived from `conversation_id` in `on_init`). |
| 48–64 | **MEDIUM** | **`_load_voice_context()` reads file without locking:** This reads `voice_context.json` while `api.py`'s `/api/set-voice-context` writes it. No synchronization between processes. The race window is small but real. **Fix:** Same as `api.py:144-147` — use locking or in-memory sharing. |
| 102 | **LOW** | **Assumes last message in transcript is from user:** `messages[-1]["content"]` is used as the user's utterance, but if the transcript structure ever places an agent message last (e.g., in edge cases), the wrong text gets sent to the LLM. **Fix:** Filter for `role == "user"` explicitly. |
| 113–115 | **LOW** | **Fallback message is in English for a Spanish-use-case project:** The error fallback says `"I'm sorry, I didn't quite catch that..."` but the entire Movistar flow is in Spanish. **Fix:** Use Spanish: `"Lo siento, no entendí bien. ¿Podrías repetirlo?"` |
| 70 | **LOW** | **`on_init` not async:** All other callbacks are async but `on_init` is sync. While this may match the SDK signature, it's inconsistent and could block the event loop if `on_init` is ever extended to do I/O. **Fix:** Make it `async def` for consistency. |

---

### 4. `test_adapter.py`

| Line(s) | Severity | Description |
|---------|----------|-------------|
| 14 | **LOW** | **Fixed session ID prevents clean test isolation:** If a previous test run crashed without calling `reset_session()`, the session may already contain stale history. The test relies on its own ordering. **Fix:** Use a random `session_id` per test run or always call `reset_session()` at setup. |
| 24, 31, 46 | **LOW** | **Brittle assertions on exact agent wording:** Tests check for substrings like `"Good morning"`, `"moment"`, `"available"`, `"Natalie"`. These will break if the agent prompts are tweaked. **Fix:** Assert on structural properties instead (e.g., `len(r1) > 20`, `"Mauricio" in r1`) or use regex patterns for greeting-like content. |
| — | **LOW** | **No teardown / cleanup between runs:** If the test is stopped mid-way, the session remains in a dirty state. **Fix:** Use `try/finally` or a fixture that calls `reset_session()`. |

---

### 5. `requirements.txt` (in `elevenlabs_integration/`)

| Line(s) | Severity | Description |
|---------|----------|-------------|
| 7 | **HIGH** | **`google-adk` has no version pin:** Any breaking ADK release will silently break the deployment. The ADK is actively developed. **Fix:** Pin to a specific version range, e.g., `google-adk>=0.1.0,<1.0.0` (or whatever the current stable version is). |
| 1 | **LOW** | **`elevenlabs>=1.0.0` is very broad:** Breaking changes in the SDK could break `speech_engine.create()` or `serve()` call patterns. **Fix:** Pin to the known-working version (e.g., `elevenlabs>=1.0.0,<2.0.0`). |
| — | **LOW** | **Missing `google-genai` dependency:** `agent_adapter.py` imports `from google.genai import types` but `google-genai` is not listed here (it is pulled transitively by `google-adk`). For reproducibility it should be explicit. **Fix:** Add `google-genai>=1.0.0`. |

---

### 6. `run_demo.ps1`

| Line(s) | Severity | Description |
|---------|----------|-------------|
| 10 | **LOW** | **Absolute hardcoded path to user's personal folder:** `$ProjectDir = "C:\Users\Peter\..."` — This script will not work on another developer's machine without manual editing. **Fix:** Use `$PSScriptRoot` to derive the path relative to the script location: `$ProjectDir = $PSScriptRoot`. |
| 69 | **LOW** | **ngrok API URL is hardcoded:** `http://127.0.0.1:4040/api/tunnels` is the default but version-specific. **Fix:** Consider making the ngrok API endpoint configurable or checking multiple known versions. |

---

### 7. `cleanup.ps1`

| Line(s) | Severity | Description |
|---------|----------|-------------|
| 11 | **LOW** | **Same absolute path issue as `run_demo.ps1`.** **Fix:** Use `$PSScriptRoot`. |
| 47–52 | **MEDIUM** | **Kills ALL ngrok processes on the system, not just the demo's:** `Get-Process -Name "ngrok" ... | Stop-Process -Force` will terminate any other ngrok tunnel the user may be running independently. **Fix:** Only kill the PID saved in the pid file, or use a filter (e.g., check the command line). |

---

### 8. `static/index.html`

| Line(s) | Severity | Description |
|---------|----------|-------------|
| 8 | **LOW** | **SDK loaded from unpkg CDN with fixed version pin is acceptable** but introduces external dependency. No blocking issue. Consider bundling locally for production. |

---

### 9. `static/app.js`

| Line(s) | Severity | Description |
|---------|----------|-------------|
| 182 | **LOW** | **`voiceTranscript.textContent` is safe** (uses textContent, not innerHTML). Good. |
| 235 | **MEDIUM** | **`messagesContainer.innerHTML = ...` replaces all DOM on every render:** Destroys and recreates every message element each time a new message arrives. This removes scroll position (mitigated by `scrollToBottom`), breaks CSS transitions on existing elements, and is inefficient for long conversations. **Fix:** Either inline-render only new messages using `insertAdjacentHTML` or use a virtual-DOM approach. |
| 37 | **LOW** | **Unbounded `messageCount` counter:** `state.messageCount` increments indefinitely with every message. For a long-running session this will overflow JavaScript's safe integer range eventually (though practically not a concern). **Fix:** Use `Date.now()` + random suffix or UUID-based IDs. |
| 102–105 | **LOW** | **History sent to API includes full message content but is sliced to 20:** Reasonable default, but no client-side max length on a single message. Could send very long messages. **Fix:** Add a max-length check on `messageInput.value` before sending. |
| 99 | **LOW** | **No trailing space in `session_id` value:** The constant `'default'` is hardcoded. Reasonable for a demo but means no session isolation across browser tabs. Fine for demo scope. |

---

### 10. `static/style.css`

No issues found. The CSS is well-structured with semantic variable names, proper responsive breakpoints, and clean animations.

---

### 11. `.env`

| Line(s) | Severity | Description |
|---------|----------|-------------|
| 4 | **HIGH** | **Hardcoded real API key:** `LITELLM_API_KEY=sk-gVEldC88JMLTMn26nzmmcA` — This appears to be a live credential (not a placeholder). It should be replaced with a placeholder like `sk-your-litellm-key` and the real key managed via environment variables or a secrets manager. **Fix:** Replace with a placeholder and ensure `.env` is in `.gitignore`. |
| 2 | **LOW** | **Model prefix mismatch:** `MODEL=openai/gemini-2.5-flash` uses the `openai/` provider prefix for a Gemini model. LiteLLM expects `gemini/gemini-2.5-flash` for proper routing. **Fix:** Change to `gemini/gemini-2.5-flash`. |

---

## Summary of Critical Issues

| # | File | Severity | Issue |
|---|------|----------|-------|
| 1 | `.env:4` | **HIGH** | Real LiteLLM API key committed to codebase |
| 2 | `api.py:66-72` | **HIGH** | Invalid CORS: wildcard origin with credentials |
| 3 | `requirements.txt:7` | **HIGH** | `google-adk` unpinned — risk of breaking on upgrade |
| 4 | `agent_adapter.py:113-119` | **MEDIUM** | Race condition in `reset_session()` |
| 5 | `agent_adapter.py:58-64` | **MEDIUM** | No timeout on ADK runner calls |
| 6 | `speech_engine_server.py:109` | **MEDIUM** | Fixed `session_id="voice"` causes cross-talk between callers |
| 7 | `speech_engine_server.py:42` | **MEDIUM** | Shared singleton adapter across concurrent voice sessions |
| 8 | `api.py:144-147` / `speech_engine_server.py:48-64` | **MEDIUM** | Race on `voice_context.json` between two processes |
| 9 | `cleanup.ps1:47-52` | **MEDIUM** | Kills all ngrok processes, not just demo's |
| 10 | `app.js:235` | **MEDIUM** | Full DOM replacement on every render |

## Positive Observations

- **XSS prevention is correct** in `app.js:41-44` (uses `textContent`/`innerHTML` properly via `escapeHtml()`).
- **Good error handling** in voice server with fallback messages for the user and detailed logging.
- **Well-structured CSS** with CSS variables, responsive design, and smooth animations.
- **Clean separation of concerns** between the three Python modules (adapter, API, engine server).
- **Good use of `asyncio` throughout** the Python backend.
- **Typing hints** and docstrings are well maintained.

---

## Recommendation

The code is **functional for a demo** but needs the HIGH-severity items addressed before any production or shared deployment:

1. **Immediately:** Rotate the exposed LiteLLM API key (`sk-gVEldC88JMLTMn26nzmmcA`) and replace with a placeholder in `.env`.
2. **Before staging:** Fix CORS credentials conflict, pin `google-adk` version, and add the `google-genai` dependency.
3. **Before multi-user use:** Fix the shared session ID for voice mode and add file-locking or in-memory sharing for voice context.
