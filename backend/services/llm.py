# services/llm.py
from __future__ import annotations

import os
import json
import re
from typing import Optional, Dict, Any, List

from dotenv import load_dotenv
import google.generativeai as genai

# -----------------------------
# Exceptions
# -----------------------------
class LLMUnavailable(RuntimeError):
    """Raised when an endpoint requires the LLM but it's not configured/available."""


# -----------------------------
# Setup
# -----------------------------
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL") or "gemini-1.5-flash"

if API_KEY:
    genai.configure(api_key=API_KEY)
    _model = genai.GenerativeModel(MODEL_NAME)
else:
    _model = None  # build_nudge will fallback; chat_reply will raise LLMUnavailable


# -----------------------------
# Small helpers (formatting + parsing)
# -----------------------------
def _nz(x) -> bool:
    """True if x is a positive number."""
    try:
        return float(x) > 0
    except Exception:
        return False

def _fmt_energy(kwh):
    try:
        kwh = float(kwh)
    except (TypeError, ValueError):
        return ""
    if kwh <= 0:
        return ""
    return f"{kwh:.2f} kWh" if kwh < 0.1 else f"{kwh:.1f} kWh"

def _fmt_money(usd):
    try:
        usd = float(usd)
    except (TypeError, ValueError):
        return ""
    return "" if usd <= 0 else f"${usd:.2f}"

def _fmt_co2(kg):
    try:
        kg = float(kg)
    except (TypeError, ValueError):
        return ""
    if kg <= 0:
        return ""
    return f"{kg*1000:.0f} g CO₂" if kg < 0.1 else f"{kg:.2f} kg CO₂"

def _extract_json_message(text: str) -> str:
    """
    Try to extract {"message": "..."} from LLM output.
    Falls back to the raw text if parsing fails.
    """
    t = (text or "").strip()
    if not t:
        return ""
    if t.startswith("{"):
        try:
            return (json.loads(t).get("message") or "").strip()
        except Exception:
            pass
    m = re.search(r"\{.*\}", t, flags=re.DOTALL)
    if m:
        try:
            return (json.loads(m.group(0)).get("message") or "").strip()
        except Exception:
            pass
    return t.strip()

def _fallback(persona: str,
              top_event: Optional[Dict[str, Any]],
              context: Optional[Dict[str, Any]]) -> str:
    """
    Safe, local nudge builder (no LLM). Uses available non-zero numbers when possible.
    """
    top_event = top_event or {}
    context = context or {}

    # Prefer evening metrics if present & non-zero
    ev_kwh = context.get("evening_kwh")
    ev_usd = context.get("evening_cost_usd")
    ev_co2 = context.get("evening_co2_kg")

    if _nz(ev_kwh) or _nz(ev_usd) or _nz(ev_co2):
        parts = []
        ek = _fmt_energy(ev_kwh)
        if ek: parts.append(f"Evening: {ek}")
        ec = _fmt_money(ev_usd)
        if ec: parts.append(f"Cost: {ec}")
        eC = _fmt_co2(ev_co2)
        if eC: parts.append(f"CO₂: {eC}")
        headline = " • ".join(parts) if parts else "Evening usage detected."
    else:
        sav = (top_event or {}).get("savings") or {}
        kwh = sav.get("kwh", 0)
        usd = sav.get("cost_usd", 0)
        co2_g = sav.get("co2_g", 0)
        parts = []
        if _nz(kwh): parts.append(_fmt_energy(kwh))
        if _nz(usd): parts.append(_fmt_money(usd))
        if _nz(co2_g): parts.append(f"{int(co2_g)} g CO₂")
        headline = "Potential impact: " + " • ".join(parts) if parts else "Quick energy tip:"

    if persona == "budget":
        tip = "Run dishwasher/laundry after 10 pm; avoid oven—use air fryer/microwave; turn off unused lights."
    elif persona == "comfort":
        tip = "Nudge thermostat +2 °F and use a fan; delay dishwasher heat-dry; keep only task lighting on."
    else:
        tip = "Shift laundry/dishwasher later, use task lighting, and avoid oven in peak—prefer air fryer or microwave."

    msg = f"{headline} {tip}"
    return (msg[:177] + "...") if len(msg) > 180 else msg


# -----------------------------
# Public: build_nudge
# -----------------------------
def build_nudge(persona: str, context: Dict[str, Any]) -> str:
    """
    Short, single nudge (<= ~180 chars). Uses non-zero numbers when present.
    If the LLM is available, uses it; otherwise falls back locally.
    """
    payload = {
        "persona": persona,
        "top_event": {
            "type": (context.get("top_event") or {}).get("type"),
            "suggestion": (context.get("top_event") or {}).get("suggestion"),
            "savings": (context.get("top_event") or {}).get("savings"),
            "reason": (context.get("top_event") or {}).get("reason"),
            "at": (context.get("top_event") or {}).get("at"),
        },
        "summary": context.get("summary", {}),
        "tariff": context.get("tariff", {}) or {"usd_per_kwh": context.get("tariff_usd_per_kwh")},
        "location": context.get("location", {}),
        # direct metrics (optional)
        "evening_kwh": context.get("evening_kwh"),
        "evening_cost_usd": context.get("evening_cost_usd"),
        "evening_co2_kg": context.get("evening_co2_kg"),
    }

    # If no LLM, return a strong local fallback
    if _model is None:
        return _fallback(persona, payload["top_event"], context)

    # Build a compact facts line
    facts = []
    ek = _fmt_energy(payload.get("evening_kwh"))
    if ek: facts.append(f"Evening: {ek}")
    ec = _fmt_money(payload.get("evening_cost_usd"))
    if ec: facts.append(f"Cost: {ec}")
    eC = _fmt_co2(payload.get("evening_co2_kg"))
    if eC: facts.append(f"CO₂: {eC}")
    facts_line = " | ".join(facts)

    system = (
        "You are PowerPulse, a concise energy coach.\n"
        "Write ONE actionable tip (<= 180 characters). "
        "If numeric facts are provided and non-zero, include ONE numeric impact (kWh, $, or CO₂). "
        "If no non-zero numbers exist, DO NOT invent numbers; give a practical tip. "
        "No emojis, no disclaimers."
    )

    user_json = {
        "persona": payload["persona"],
        "facts": facts_line,  # may be empty
        "tariff_usd_per_kwh": context.get("tariff_usd_per_kwh"),
        "grid_intensity_kg_per_kwh": context.get("grid_intensity_kg_per_kwh"),
        "top_event": payload["top_event"],
    }
    user = (
        'Return ONLY JSON like {"message":"..."}.\n'
        "Use the facts string only if it is non-empty.\n"
        "Data:\n" + json.dumps(user_json, ensure_ascii=False)
    )

    try:
        resp = _model.generate_content(
            [
                {"role": "system", "parts": [system]},
                {"role": "user", "parts": [user]},
            ],
            generation_config={"temperature": 0.2, "max_output_tokens": 120},
            request_options={"timeout": 20}
        )
        msg = _extract_json_message(getattr(resp, "text", "") or "")
        msg = " ".join((msg or "").split())
        if not msg:
            return _fallback(persona, payload["top_event"], context)
        return (msg[:177] + "...") if len(msg) > 180 else msg
    except Exception:
        return _fallback(persona, payload["top_event"], context)


# -----------------------------
# Public: chat_reply  (requires LLM)
# -----------------------------
def chat_reply(
    messages: List[Dict[str, str]],
    persona: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Next assistant reply given short chat history.
    Raises LLMUnavailable if the model isn't configured.
    """
    if _model is None:
        raise LLMUnavailable(
            "Gemini client is not configured. Set GOOGLE_API_KEY or GEMINI_API_KEY (and optionally GEMINI_MODEL)."
        )

    persona = persona or "eco"
    context = context or {}

    history = [
        {"role": m.get("role", "user"), "content": m.get("content", "")}
        for m in (messages or [])[-10:]
    ]

    system_lines = [
        "You are PowerPulse, a concise residential energy coach.",
        "Respond in 2–4 sentences, practical and supportive.",
        "Use ONLY provided numbers; do not invent. If negligible, say 'negligible'.",
        "Prioritize actions: thermostat, laundry/dishwasher timing, cooking method, lighting, phantom loads.",
        f"Persona: {persona}",
    ]

    # Optional facts
    ek = _fmt_energy(context.get("evening_kwh"))
    ec = _fmt_money(context.get("evening_cost_usd"))
    eC = _fmt_co2(context.get("evening_co2_kg"))
    evening_bits = [x for x in (ek, ec, eC) if x]
    if evening_bits:
        system_lines.append("Evening window (5–10 pm): " + " | ".join(evening_bits))

    system_prompt = "\n".join(system_lines).strip()

    payload = {
        "persona": persona,
        "context": context,
        "history": history,
    }
    user_prompt = "Chat history JSON (latest last). Provide the next assistant reply.\n" + json.dumps(payload, ensure_ascii=False)

    resp = _model.generate_content(
        [
            {"role": "system", "parts": [system_prompt]},
            {"role": "user", "parts": [user_prompt]},
        ],
        generation_config={"temperature": 0.4, "max_output_tokens": 400},
        request_options={"timeout": 25},
    )
    text = (getattr(resp, "text", "") or "").strip()
    if not text:
        # Let caller decide fallback behavior
        raise LLMUnavailable("Empty reply from LLM")
    return " ".join(text.split())


# -----------------------------
# Back-compat wrapper
# -----------------------------
def chat_with_energy_data(context: Dict[str, Any]) -> str:
    """
    Legacy wrapper used by older code paths.
    """
    try:
        return chat_reply(messages=[], persona="friendly", context=context)
    except LLMUnavailable:
        return build_nudge(persona="friendly", context=context)
