import os, json, time
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"

# init
genai.configure(api_key=KEY)
_model = genai.GenerativeModel(MODEL)

def _fallback(persona: str, top_event: dict) -> str:
    sav = (top_event or {}).get("savings", {}) or {}
    kwh = sav.get("kwh", 0.0)
    co2 = sav.get("co2_g", 0)
    usd = sav.get("cost_usd", 0.0)
    if persona == "budget":  return f"Peak rates—shift a cycle and save ${usd:.2f}."
    if persona == "comfort": return "Raise thermostat ~2°F to trim the peak without losing comfort."
    return f"Small changes now could avoid ~{co2} g CO₂."

def build_nudge(persona: str, context: dict) -> str:
    """
    persona: 'eco' | 'budget' | 'comfort'
    context: {
      'top_event': { 'savings': {'kwh','co2_g','cost_usd'}, 'type', 'suggestion', 'reason', 'at' },
      'summary': {'todayKwh','potentialSavingsKwh'},
      'tariff': {'is_peak': bool, 'cents_per_kwh': float},
      'location': {'city': str}
    }
    """
    if not KEY:
        return _fallback(persona, context.get("top_event", {}))

    # Keep payload minimal—reduces chance of hallucination.
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
        "tariff": context.get("tariff", {}),
        "location": context.get("location", {}),
    }

    system = (
        "You are PowerPulse, a concise energy coach.\n"
        "Write ONE suggestion (<= 180 characters).\n"
        "Use ONLY numbers from the JSON. Do not invent values. No emojis, no disclaimers."
    )
    user = 'Return JSON like {"message":"..."}.\nAnalytics JSON:\n' + json.dumps(payload)

    try:
        resp = _model.generate_content(
            [{"role":"system","parts":[system]},
             {"role":"user","parts":[user]}],
            generation_config={"temperature":0.2, "max_output_tokens":120},
            request_options={"timeout": 20}
        )
        text = (resp.text or "").strip()
        if text.startswith("{"):
            try:
                msg = json.loads(text).get("message","").strip()
            except Exception:
                msg = text
        else:
            msg = text
        msg = " ".join(msg.split())
        return (msg[:177] + "...") if len(msg) > 180 else (msg or _fallback(persona, payload["top_event"]))
    except Exception:
        return _fallback(persona, payload["top_event"])
