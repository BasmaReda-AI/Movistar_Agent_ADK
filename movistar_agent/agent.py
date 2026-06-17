"""Movistar outbound multi-agent — HAPPY PATH (Scenarios A-01, A-02, A-03, A-04).

    greeting_agent (root)                sales_specialist (sub-agent)
    ───────────────────────              ──────────────────────────────────────────
    Identity confirmation                Phase 0: Engagement hook
    Availability check                     ↳ [A-04] Objection Matrix rebuttal
        │                                Phase 1: Primary offer pitch
        └── transfer_to_agent ─────────▶ Phase 5A: Value build rebuttal
                                         Phase 5B: Downsell pitch (trigger_oferta_alterna)
                                         Phase 2:  Warm handoff + CRM logging
"""

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from dotenv import load_dotenv

from .config import MODEL, LITELLM_API_BASE, LITELLM_API_KEY, CALL_SESSION_ID, SYSTEM_STATE
from .prompts import GREETING_INSTRUCTION, SALES_INSTRUCTION
from .tools import (
    query_offers_kb,
    query_objection_matrix,
    trigger_oferta_alterna,
    transfer_to_human_agent,
    end_call,
)

load_dotenv()


sales_specialist = Agent(
    name="sales_specialist",
    model=LiteLlm(
        model=MODEL,
        api_base=LITELLM_API_BASE,
        api_key=LITELLM_API_KEY,
        metadata={
            "tags": ["ADK"],
            "langfuse_trace_name": "Movistar Sales Specialist Phase",
            "session_id": CALL_SESSION_ID,
            "user_id": SYSTEM_STATE["CELULAR_CONTACTO"],
        },
    ),
    description=(
        "Movistar sales specialist. Receives customers who confirmed identity and "
        "availability. Runs the engagement hook (with Objection Matrix rebuttal if "
        "needed), pitches the primary offer, handles price objections with a value build "
        "rebuttal (Phase 5A), falls back to the downsell offer (Phase 5B), and transfers "
        "accepting customers to a human advisor."
    ),
    instruction=SALES_INSTRUCTION,
    tools=[
        query_offers_kb,
        query_objection_matrix,
        trigger_oferta_alterna,
        transfer_to_human_agent,
        end_call,
    ],
)


greeting_agent = Agent(
    name="greeting_agent",
    model=LiteLlm(
        model=MODEL,
        api_base=LITELLM_API_BASE,
        api_key=LITELLM_API_KEY,
        metadata={
            "tags": ["ADK"],
            "langfuse_trace_name": "Movistar Greeting Phase",
            "session_id": CALL_SESSION_ID,
            "user_id": SYSTEM_STATE["CELULAR_CONTACTO"],
        },
    ),
    description=(
        "Movistar outbound greeting agent. Verifies the customer's identity, "
        "checks availability, and hands ready customers to the sales specialist."
    ),
    instruction=GREETING_INSTRUCTION,
    tools=[end_call],
    sub_agents=[sales_specialist],  # enables ADK's built-in transfer_to_agent
)


root_agent = greeting_agent
