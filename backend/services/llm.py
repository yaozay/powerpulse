# services/llm.py
import os
import json
import re
from typing import Optional, Dict, Any

from dotenv import load_dotenv
import google.generativeai as genai

# -----------------------------
# Setup
# -----------------------------
load_dotenv()

KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not KEY:
    raise RuntimeError("Missing GOOGLE_API_KEY (or GEMINI_API_KEY)")

MODEL = os.getenv("GEMINI_MODEL") or "gemini-1.5-flash"  # stable default

genai.configure(api_key=KEY)
_model = genai.GenerativeModel(MODEL)

# -----------------------------
# Helpers
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
    # Direct JSON?
    if t.startswith("{"):
        try:
            return (json.loads(t).get("message") or "").strip()
        except Exception:
            pass
    # JSON somewhere inside
    m = re.search(r"\{.*\}", t, flags=re.DOTALL)
    if m:
        try:
            return (json.loads(m.group(0)).get("message") or "").strip()
        except Exception:
            pass
    return t.strip()

def _fallback(persona: str, top_event: Optional[Dict[str, Any]], context: Optional[Dict[str, Any]]) -> str:
    """
    Safer fallback that avoids '~0 g CO₂' and uses persona.
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
        if ek: parts.append(f"Evening usage: {ek}")
        ec = _fmt_money(ev_usd)
        if ec: parts.append(f"Cost: {ec}")
        eC = _fmt_co2(ev_co2)
        if eC: parts.append(f"Emissions: {eC}")
        headline = " • ".join(parts) if parts else "Evening usage detected."
    else:
        # try top_event savings
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
        return f"{headline} Run dishwasher and laundry after 10 pm; avoid oven—use air fryer/microwave. Turn off unused lights."
    if persona == "comfort":
        return f"{headline} Nudge thermostat +2 °F and use a fan. Delay heat-dry on dishwasher; keep only task lighting on."
    # default
    return f"{headline} Shift laundry/dishwasher later, use task lighting, and avoid oven in peak—prefer air fryer or microwave."

# -----------------------------
# Public: build_nudge
# -----------------------------
def build_nudge(persona: str, context: dict) -> str:
    """
    Short, single-sentence(ish) nudge.
    Uses numbers ONLY if provided and non-zero; otherwise gives a sensible generic tip.
    Returns <= 180 chars when possible.
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
        # direct metrics
        "evening_kwh": context.get("evening_kwh"),
        "evening_cost_usd": context.get("evening_cost_usd"),
        "evening_co2_kg": context.get("evening_co2_kg"),
    }

    # Build a compact, numbers-only facts line (only when non-zero)
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
        "If no non-zero numbers exist, DO NOT invent numbers; give a generic, practical tip. "
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
        msg = _extract_json_message(resp.text)
        msg = " ".join((msg or "").split())
        if not msg:
            return _fallback(persona, payload["top_event"], context)
        return (msg[:177] + "...") if len(msg) > 180 else msg
    except Exception:
        return _fallback(persona, payload["top_event"], context)

# -----------------------------
# Public: chat_with_energy_data
# -----------------------------
def chat_with_energy_data(context: dict) -> str:
    """
    Interactive chat for the Energy Coach.

    Expects context keys (optional):
    - home_id: int
    - current_power_kw: float
    - today_usage_kwh: float
    - today_cost_usd: float
    - today_co2_kg: float
    - evening_kwh / evening_cost_usd / evening_co2_kg: floats
    - tariff_usd_per_kwh: float
    - grid_intensity_kg_per_kwh: float
    - weather: dict
    - user_message: str
    - conversation_history: list[str]
    - potentials: list[{"name":str, "shift_kwh"?:float, "save_kwh"?:float, "note"?:str}]
    """
    system_lines = [
        "You are an AI Energy Coach for PowerPulse.",
        f"Home ID: {context.get('home_id', 'Unknown')}",
        f"Current Power: {float(context.get('current_power_kw') or 0):.1f} kW",
        f"Today Usage: {float(context.get('today_usage_kwh') or 0):.1f} kWh",
        f"Today Cost: {float(context.get('today_cost_usd') or 0):.2f} USD",
        f"Today CO₂: {float(context.get('today_co2_kg') or 0):.1f} kg",
    ]

    # Optional weather
    weather = context.get("weather") or {}
    if weather:
        ot = weather.get("temperature_f")
        it = weather.get("indoor_temperature_c")
        if ot is not None:
            system_lines.append(f"Outdoor Temp: {ot} °F")
        if it is not None:
            system_lines.append(f"Indoor Temp: {it} °C")

    # Evening facts (only if non-zero)
    ek = _fmt_energy(context.get("evening_kwh"))
    ec = _fmt_money(context.get("evening_cost_usd"))
    eC = _fmt_co2(context.get("evening_co2_kg"))
    evening_bits = [x for x in (ek, ec, eC) if x]
    if evening_bits:
        system_lines.append("Evening window (5–10 pm): " + " | ".join(evening_bits))

    system_lines += [
        "",
        "Your role:",
        "1) Analyze the user's energy data when they ask questions.",
        "2) Provide specific, actionable recommendations using ONLY provided numbers; do not invent.",
        "3) Be helpful and concise (2–4 sentences).",
        "4) Quantify kWh, $, and CO₂ (kg) when inputs are non-zero; if negligible (<0.05 kWh or <$0.01), say 'negligible'.",
        "5) Prioritize practical household actions (thermostat, laundry/dishwasher timing, cooking method, lighting, phantom loads).",
    ]

    # Potentials (optional guide for the LLM)
    pots = context.get("potentials") or []
    if pots:
        lines = []
        for p in pots[:8]:
            name = p.get("name", "Device")
            if "shift_kwh" in p:
                lines.append(f"- {name}: shift ~{p['shift_kwh']} kWh. {p.get('note','')}")
            elif "save_kwh" in p:
                lines.append(f"- {name}: save ~{p['save_kwh']} kWh. {p.get('note','')}")
        if lines:
            system_lines += ["", "Reference potentials:", *lines]

    system_prompt = "\n".join(system_lines).strip()

    # Conversation history
    conversation = ""
    if context.get("conversation_history"):
        conversation = "Recent conversation:\n" + "\n".join(context["conversation_history"][-4:]) + "\n\n"

    user_prompt = conversation + f"User: {context.get('user_message', '').strip()}"

    try:
        # Use system + user roles; more reliable than concatenating both in a single user part
        response = _model.generate_content(
            [
                {"role": "system", "parts": [system_prompt]},
                {"role": "user", "parts": [user_prompt]},
            ],
            generation_config={"temperature": 0.5, "max_output_tokens": 500, "top_p": 0.95},
            request_options={"timeout": 30}
        )
        text = (response.text or "").strip()
        if not text:
            # graceful fallback if model returns empty
            return build_nudge(persona="friendly", context=context)
        return text

    except Exception as e:
        print(f"Gemini chat error: {e}")
        # graceful fallback to a short nudge instead of an apology
        try:
            return build_nudge(persona="friendly", context=context)
        except Exception:
            return "Here are quick steps: use task lighting, delay laundry/dishwasher to off-peak, and avoid the oven—prefer air fryer or microwave."
