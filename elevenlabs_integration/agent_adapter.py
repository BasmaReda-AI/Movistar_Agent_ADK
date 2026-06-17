"""
AgentAdapter — wraps the ADK Runner API so the ElevenLabs integration
can call the Movistar multi-agent system programmatically.

Usage:
    adapter = AgentAdapter()
    response = await adapter.chat("hi")
    # => "Good morning, am I speaking with Mauricio Ortiz?..."
"""

import os
import sys

# Ensure the parent directory (where movistar_agent lives) is on sys.path
_parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent not in sys.path:
    sys.path.insert(0, _parent)

from movistar_agent import root_agent
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types


class AgentAdapter:
    """Adapter that wraps the ADK Runner for programmatic multi-agent calls."""

    def __init__(self):
        self._session_service = InMemorySessionService()
        self._runner = Runner(
            agent=root_agent,
            app_name="movistar_agent",
            session_service=self._session_service,
        )

    # ── Public API ──────────────────────────────────────────────────

    async def chat(self, message: str, session_id: str = "default") -> str:
        """Send a user message to the agent and return the final response text.

        Args:
            message: The user's text input.
            session_id: An identifier for the conversation session. Use the
                        same session_id to maintain conversation continuity.

        Returns:
            The agent's final response text, or an empty string on failure.
        """
        # Ensure the session exists (no-op if already created)
        self._create_session_if_not_exists(session_id)

        try:
            content = types.Content(
                role="user",
                parts=[types.Part.from_text(text=message)],
            )

            async for event in self._runner.run_async(
                user_id="user",
                session_id=session_id,
                new_message=content,
            ):
                if event.is_final_response():
                    return event.content.parts[0].text

            # No final response event yielded
            return ""

        except Exception as e:
            print(f"[AgentAdapter] Error in chat (session={session_id}): {e}")
            return ""

    async def set_context(self, history: list[dict], session_id: str = "default"):
        """Seed a session with conversation history for voice context.

        Each message in history is fed through the agent so the session
        state reflects the prior text chat.

        Args:
            history: List of dicts with ``role`` ("user" | "assistant") and
                     ``content`` keys.
            session_id: The session to seed.
        """
        self._create_session_if_not_exists(session_id)

        for msg in history:
            try:
                role = msg.get("role", "user")
                content_text = msg.get("content", "")
                content = types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=content_text)],
                )

                # Consume all events to advance session state
                async for _event in self._runner.run_async(
                    user_id="user",
                    session_id=session_id,
                    new_message=content,
                ):
                    pass  # We only need to seed context, not capture output

            except Exception as e:
                print(f"[AgentAdapter] Error seeding context message: {e}")

    def reset_session(self, session_id: str = "default"):
        """Reset a session by creating a fresh InMemorySessionService.

        Because the session service is entirely in-memory, the simplest
        way to clear all state is to replace it with a new instance and
        rebuild the Runner.
        """
        try:
            self._session_service = InMemorySessionService()
            self._runner = Runner(
                agent=root_agent,
                app_name="movistar_agent",
                session_service=self._session_service,
            )
        except Exception as e:
            print(f"[AgentAdapter] Error resetting session: {e}")

    # ── Internals ───────────────────────────────────────────────────

    def _create_session_if_not_exists(self, session_id: str):
        """Create a session if it doesn't already exist (swallow duplicates)."""
        try:
            self._session_service.create_session(
                app_name="movistar_agent",
                user_id="user",
                session_id=session_id,
            )
        except Exception:
            pass  # Session already exists — that's fine
