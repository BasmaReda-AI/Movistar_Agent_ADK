"""Tools — HAPPY PATH (Scenarios A-01, A-02, A-03, A-04).

  query_offers_kb         → fetch the primary offer before the Phase 1 pitch
  query_objection_matrix  → retrieve rebuttal for a hook-phase objection (A-04)
  trigger_oferta_alterna  → shift context to the alternate offer (Phase 5B downsell)
  transfer_to_human_agent → warm handoff after explicit acceptance
  end_call                → terminate + simulated CRM logging

The AI→AI handoff (greeting → sales specialist) is ADK's built-in
`transfer_to_agent`, injected automatically via `sub_agents` — do not define
a tool with that name.
"""

import json
from datetime import datetime

from .config import SYSTEM_STATE
from .kb.offers_kb import OFFERS_KB
from .kb.objection_matrix import OBJECTION_MATRIX


def query_offers_kb(offer_key: str) -> dict:
    """Query the Offers KB for the full details of the primary plan.

    Call with offer_key="PRIMARY" right before delivering the pitch.
    Returns plan name, monthly price, included data capacity, apps available
    after the capacity is consumed, the promotional discount, and extra benefits.
    """
    resolved = SYSTEM_STATE["PRIMARY_KEY1"] if offer_key.upper() == "PRIMARY" else offer_key
    offer = OFFERS_KB.get(resolved)
    print(f"\n[SYSTEM] OFFERS KB query: {offer_key} -> {resolved}")
    if offer is None:
        return {"error": f"Offer '{offer_key}' not found", "available_keys": list(OFFERS_KB)}
    return {"offer_key": resolved, **offer}


def query_objection_matrix(objection_type: str, argument: int = 1) -> dict:
    """Retrieve the rebuttal script for a customer objection at any phase.

    Call this when the customer raises a specific objection. Identify the
    best-matching category from the customer's words, select the argument number
    that fits their specific concern, and deliver the returned 'rebuttal' verbatim
    (personalizing with the customer's name). Store the 'category' field as
    Argumentation_Used for all subsequent end_call / transfer_to_human_agent calls.

    Args:
        objection_type: One of the recognized category keys listed below.
        argument: Which argument to use (1 = primary/default, 2 or 3 = targeted).
                  The returned 'use_when' field describes the ideal context for each
                  number. When in doubt, always use argument=1.

    Hook-phase category keys (Phase 0 — engagement hook):
      TOO_EXPENSIVE           — too costly, high price, budget concerns, can't afford it
      NO_MONTHLY_BILL         — doesn't want bills, debt, or monthly commitments
      PREFER_PREPAID_CONTROL  — prefers prepaid, wants to control spending
      BAD_PAST_EXPERIENCE     — past bad experience, complaint, overcharged, terrible service
      NO_COMMITMENT           — doesn't want contracts, permanence, clauses, or penalties
      NO_TIME                 — busy, working, driving, in a meeting, asks to call later
      SATISFIED_WITH_RECHARGES — happy with recharges, content with current plan
      ONLY_USES_MINUTES       — only uses calls, doesn't need data
      UNEMPLOYED              — no job, no income, difficult financial situation
      PREPAID_COMPARISON      — compares prepaid packages, mentions number ownership/validity
      GOING_ON_TRIP           — traveling, leaving the city, going abroad, on vacation
      KEYPAD_PHONE            — has a basic/keypad phone, no smartphone, no apps
      BAD_COVERAGE            — bad signal, calls drop, poor coverage, Ookla comparison
      BAD_SIGNAL_ROAMING      — rural/indoor signal issues, asks about roaming
      LINE_FOR_MINOR          — line is for a child, son, daughter, or grandson
      OCCASIONAL_USE          — rarely uses the phone, only for emergencies, uses Wi-Fi
      CLOSING_TRUST           — mentions SUBTEL, suspicious of why Movistar is calling
      NOT_LEGAL_OWNER         — not the account holder, line belongs to someone else
      DISTRUST_FRAUD          — fears the call is a scam, won't give information
      PROCESS_HESITATION      — doesn't understand the activation, fears paperwork
      RECHARGE_18500          — mentions the $18,500 prepaid package
      NOT_INTERESTED          — flat 'not interested' with no specific reason given
      HAPPY_WITH_PREPAID      — legacy alias; prefer SATISFIED_WITH_RECHARGES

    Pitch-phase category keys (Phase 1 — after hearing the offer):
      FEAR_OF_BILL_INCREASES  — worries about hidden charges or being overcharged
      DISTRUST_FRAUD          — fears the offer is a scam or demands official verification
      PROCESS_HESITATION      — doubts about how the activation process works

    Returns dict with keys: category, use_when, rebuttal.
    """
    result = OBJECTION_MATRIX.get(objection_type.upper())
    print(f"\n[SYSTEM] OBJECTION MATRIX query: {objection_type} (argument {argument})")
    if result is None:
        return {
            "error": f"Objection type '{objection_type}' not recognized",
            "available_types": list(OBJECTION_MATRIX),
        }
    arguments = result.get("arguments", [])
    idx = max(0, min(argument - 1, len(arguments) - 1))
    selected = arguments[idx]
    # Substitute {{CUSTOMER_NAME}} with the actual customer name from CRM.
    # If name is absent, strip the placeholder and any preceding ", " to avoid
    # awkward punctuation (e.g. "I understand, . However" → "I understand. However").
    customer_name = SYSTEM_STATE.get("NOMBRE_CLIENTE", "")
    if customer_name:
        rebuttal = selected["rebuttal"].replace("{{CUSTOMER_NAME}}", customer_name)
    else:
        import re
        rebuttal = re.sub(r",?\s*\{\{CUSTOMER_NAME\}\},?\s*", " ", selected["rebuttal"]).strip()
    print(f"  Category       : {result['category']}")
    print(f"  Argument       : {argument} — {selected['use_when']}")
    print(f"  Argumentation  : {result['category']} rebuttal loaded")
    return {
        "category": result["category"],
        "use_when": selected["use_when"],
        "rebuttal": rebuttal,
    }


def trigger_oferta_alterna() -> dict:
    """Switch context to the alternate (downsell) offer after the customer declines
    the primary offer AND the value build rebuttal.

    Call this ONCE at the start of Phase 5B, silently before speaking. Returns the
    alternate offer details (price, capacity, apps, extra benefits) for use in the
    downsell pitch.
    """
    resolved = SYSTEM_STATE.get("SECONDARY_KEY1", "POSPAGO_25GB")
    offer = OFFERS_KB.get(resolved)
    print(f"\n[SYSTEM] TRIGGER_OFERTA_ALTERNA")
    print(f"  Context shift  : PRIMARY -> ALTERNATE ({resolved})")
    print(f"  VLR_OFERTA2    : {SYSTEM_STATE.get('VLR_OFERTA2', 'N/A')}")
    if offer is None:
        return {"error": f"Alternate offer '{resolved}' not found", "available_keys": list(OFFERS_KB)}
    return {"offer_key": resolved, "context": "ALTERNATE", **offer}


def transfer_to_human_agent(
    call_status: str,
    product_offered: str,
    notes: str = "",
    argumentation_used: str = "N/A",
) -> dict:
    """Transfer the live call to a human Movistar advisor for contract closing.

    Call ONLY after the customer gives an explicit acceptance signal
    (e.g. "sí", "listo", "dale", "me interesa") AND confirms they can stay
    on the line.

    This function also fires the CRM logging pipeline (interaction log +
    customer profile update), replacing the need for a separate end_call
    in the handoff phase.

    Args:
        call_status: Outcome label, e.g. "Interested and Transferred".
        product_offered: Monthly price of the accepted plan, e.g. "$49.900".
        notes: One-sentence summary of the interaction path.
        argumentation_used: Objection category handled at hook phase (from
            query_objection_matrix 'category' field), or "N/A" if no objection arose.
    """
    timestamp = datetime.utcnow().isoformat()

    # Fire CRM interaction log
    interaction_payload = {
        "customer_name": SYSTEM_STATE["NOMBRE_CLIENTE"],
        "phone": SYSTEM_STATE["CELULAR_CONTACTO"],
        "call_status": call_status,
        "product_offered": product_offered,
        "human_escalation_flag": True,
        "argumentation_used": argumentation_used,
        "notes": notes,
        "timestamp": timestamp,
    }
    profile_payload = {
        "customer_name": SYSTEM_STATE["NOMBRE_CLIENTE"],
        "phone": SYSTEM_STATE["CELULAR_CONTACTO"],
        "last_outcome": call_status,
        "last_product_offered": product_offered,
        "timestamp": timestamp,
    }

    print("\n[SYSTEM] TRANSFER_TO_HUMAN_AGENT")
    print(f"  Call Status      : {call_status}")
    print(f"  Product Offered  : {product_offered}/mes")
    print(f"  Human Escalation : True")
    print(f"  Argumentation    : {argumentation_used}")
    print(f"  Routing to       : Movistar live agent queue (Twilio)")
    print(f"[SYSTEM] API POST -> Interaction Log Table\n{json.dumps(interaction_payload, indent=2, ensure_ascii=False)}")
    print(f"[SYSTEM] API POST -> Customer Profile Table\n{json.dumps(profile_payload, indent=2, ensure_ascii=False)}")
    print("[SYSTEM] Flow ends — FIN\n")

    return {
        "status": "transferred",
        "call_status": call_status,
        "product_offered": product_offered,
        "human_escalation_flag": True,
        "argumentation_used": argumentation_used,
        "timestamp": timestamp,
    }


def end_call(
    call_status: str,
    product_offered: str,
    notes: str,
    argumentation_used: str = "N/A",
) -> dict:
    """Formally terminate the call and fire the CRM logging pipeline.

    In the happy path this is called once, right after transfer_to_human_agent.
    If the customer ever deviates from the happy path (denies identity, is busy,
    declines), close politely and call this with the appropriate status instead.

    Args:
        call_status: e.g. "Interested and Transferred", "Not Interested",
            "Wrong Number".
        product_offered: Final price quoted, or "N/A" if the pitch never happened.
        notes: One-sentence summary of the interaction.
        argumentation_used: Objection category handled at hook phase (from
            query_objection_matrix 'category' field), or "N/A" if no objection arose.
    """
    interaction_payload = {
        "customer_name": SYSTEM_STATE["NOMBRE_CLIENTE"],
        "phone": SYSTEM_STATE["CELULAR_CONTACTO"],
        "call_status": call_status,
        "product_offered": product_offered,
        "human_escalation_flag": call_status == "Interested and Transferred",
        "argumentation_used": argumentation_used,
        "notes": notes,
        "timestamp": datetime.utcnow().isoformat(),
    }
    profile_payload = {
        "customer_name": SYSTEM_STATE["NOMBRE_CLIENTE"],
        "phone": SYSTEM_STATE["CELULAR_CONTACTO"],
        "last_outcome": call_status,
        "last_product_offered": product_offered,
        "timestamp": datetime.utcnow().isoformat(),
    }
    print("\n[SYSTEM] END_CALL — CRM pipeline fired")
    print(f"[SYSTEM] API POST -> Interaction Log Table\n{json.dumps(interaction_payload, indent=2, ensure_ascii=False)}")
    print(f"[SYSTEM] API POST -> Customer Profile Table\n{json.dumps(profile_payload, indent=2, ensure_ascii=False)}")
    print("[SYSTEM] Flow ends — FIN\n")
    return {"status": "call_ended", "crm_logged": True}
