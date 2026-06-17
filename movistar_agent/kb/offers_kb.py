"""Offers KB -- mirror of the ElevenLabs `Offers KB` document.

Keyed by the offer primary key ({{Primary_Key1}} / {{Primary_Key2}} in the
ElevenLabs prompt). Field names match the ones the sales prompt expects:
  - Capacidad_Navegacion_Incluida
  - Apps_Despues_De_Capacidad
  - Descuento_Promocional

NOTE: Descuento_Promocional values below are PLACEHOLDERS -- replace with the
real campaign discounts before any production use.
"""

OFFERS_KB = {
    "POSPAGO_40GB": {
        "offer_name": "Postpaid Plan 40GB",
        "monthly_price": "$49.900",
        "Capacidad_Navegacion_Incluida": "40 GB",
        "Apps_Despues_De_Capacidad": "WhatsApp, Facebook, and Instagram with no limits even after the data cap is reached",
        "Descuento_Promocional": "50% discount for the first 3 months",  # PLACEHOLDER
        "extra_benefits": [
            "Unlimited calls to any carrier within the country",
            "One free month of Amazon Prime",
        ],
    },
    "POSPAGO_25GB": {
        "offer_name": "Postpaid Plan 25GB",
        "monthly_price": "$35.900",
        "Capacidad_Navegacion_Incluida": "25 GB",
        "Apps_Despues_De_Capacidad": "WhatsApp, Facebook, and Instagram with no limits even after the data cap is reached",
        "Descuento_Promocional": "30% discount for the first 3 months",  # PLACEHOLDER
        "extra_benefits": [
            "Unlimited calls to any carrier within the country",
            "Entertainment apps and streaming TV access",
        ],
    },
}
