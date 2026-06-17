# Movistar Colombia — Prepaid-to-Postpaid Migration Agent (Google ADK)

Two-agent outbound sales system covering the full happy path (Scenarios A-01 → A-05),
built with **Google ADK** and routed through a **LiteLLM proxy**.

```
Customer picks up
  → greeting_agent  : identity confirmation + availability check
  → transfer_to_agent (ADK built-in) ──▶ sales_specialist
  → sales_specialist: engagement hook                          [Phase 0]
      ↳ Objection Matrix rebuttal (if objection raised)       [A-04]
  → primary offer pitch                                        [Phase 1]
      ↳ Objection Matrix rebuttal (if pitch-phase objection)  [A-05]
      ↳ value build rebuttal (price hesitation)               [Phase 5A]
      ↳ downsell pitch (primary rejected)                     [Phase 5B]
  → explicit acceptance → warm handoff → transfer_to_human_agent → end_call (CRM)
```

## Scenarios covered

| ID | Path |
|---|---|
| A-01 | Primary offer accepted on first pitch |
| A-02 | Primary offer accepted after value build rebuttal |
| A-03 | Downsell accepted (primary + value build both rejected) |
| A-04 | Offer accepted after hook-phase objection (Phase 0) |
| A-05 | Downsell accepted after pitch-phase objection (Phase 1) |

Off-path replies (wrong number, busy, any final decline) each get one polite
closing line + `end_call` so the session never gets stuck.

## Structure

```
movistar/
├── .env                    # LiteLLM credentials (not committed)
├── requirements.txt
├── run.bat / run.ps1
└── movistar_agent/
    ├── __init__.py             # exports root_agent
    ├── agent.py                # greeting_agent (root) + sales_specialist (sub-agent)
    ├── config.py               # SYSTEM_STATE: customer CRM data, offer keys, model
    ├── prompts.py              # GREETING_INSTRUCTION + SALES_INSTRUCTION (full happy path)
    ├── tools.py                # query_offers_kb, query_objection_matrix,
    │                           # trigger_oferta_alterna, transfer_to_human_agent, end_call
    └── kb/
        ├── offers_kb.py        # primary (40 GB) and downsell (25 GB) plan data
        └── objection_matrix.py # 22-category rebuttal matrix with verbatim scripts
```

## Setup

### 1. Environment

Create a `.env` file in the project root:

```env
LITELLM_API_BASE=https://<your-litellm-proxy>/v1
LITELLM_API_KEY=sk-...
MODEL=openai/gemini-2.5-flash   # any model available on your proxy
MIGRATION_ADK=movistar-adk      # Langfuse trace tag (optional)
```

### 2. Install & run

```bash
pip install -r requirements.txt

# Windows
run.bat

# or manually
adk web
```

Open **http://127.0.0.1:8000**, select **movistar_agent**, and send any message
(it simulates the customer picking up the phone).

## Demo script

| You type | Agent does |
|---|---|
| `hello` | Greeting agent asks for identity: *"Good morning, am I speaking with [Name]?"* |
| `yes, speaking` | Asks for availability |
| `sure, go ahead` | Transfers to `sales_specialist` → engagement hook |
| `yes, tell me` | Queries Offers KB → full pitch |
| `sounds good, let's do it` | Warm handoff → `transfer_to_human_agent` → `end_call` + CRM logs |

**Objection during hook (A-04 path):**

| You type | Agent does |
|---|---|
| `I had a bad experience with Movistar` | Calls `query_objection_matrix(BAD_PAST_EXPERIENCE)` → rebuttal |
| `ok, tell me more` | Proceeds to pitch → acceptance → handoff |

Watch the terminal for `[SYSTEM]` logs — KB query, objection matrix lookup,
human transfer, and the two simulated CRM API POSTs.

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

Each category has 1–4 arguments. `query_objection_matrix(key, argument=N)` returns
the verbatim rebuttal with the customer name already substituted.
