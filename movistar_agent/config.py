"""Campaign configuration — HAPPY PATH (Scenarios A-01, A-02, A-03, A-04, A-05).

Active scenario: A-05 — Downsell Accepted After Objection Matrix at Pitch Phase.
Customer: Mauricio Ortiz / Primary: POSPAGO_40GB @ $49.900 / Alternate: POSPAGO_25GB @ $35.900

Assumptions baked in for this version:
  - Enriched lead: the customer name is always known.
  - Human agent is always available for the transfer.
Everything else (blind leads, reschedules) lives in the full version.
"""

import os
from datetime import datetime

SYSTEM_STATE = {
    "NOMBRE_CLIENTE": "Mauricio Ortiz",
    "CELULAR_CONTACTO": "3001234567",
    "PRIMARY_KEY1": "POSPAGO_40GB",
    "VLR_OFERTA1": "$49.900",
    "Capacidad_Navegacion": "40GB",
    "SECONDARY_KEY1": "POSPAGO_25GB",
    "VLR_OFERTA2": "$35.900",
    "Capacidad_Alterna": "25GB",
}

MODEL = os.getenv("MODEL", "openai/gemini-2.5-flash")
LITELLM_API_BASE = os.getenv(
    "LITELLM_API_BASE",
    "https://api.dev.ix.konecta-digital.com/litellm-test/v1",
)
LITELLM_API_KEY = os.getenv("LITELLM_API_KEY", "sk-gVEldC88JMLTMn26nzmmcA")
MIGRATION_ADK = os.getenv("MIGRATION_ADK", "movistar-adk")


def system_time() -> str:
    return datetime.now().strftime("%A, %d %B %Y %H:%M")
