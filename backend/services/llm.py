from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Mapping, Sequence

from dotenv import load_dotenv
import google.generativeai as genai


class LLMUnavailable(RuntimeError):
    
    DOTENV_PATH =  (
        Path(__file__).resolve().parent.parent / ".env"
    )
    load_dotenv(dotenv_path=DOTENV_PATH, override=True)

KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL")

SYSTEM_INSTRUCTION_NUDGE = (
    "You are PowerPulse, a concise energy coach. "
    "Write ONE suggestion (<= 180 characters). "
    "Use ONLY numbers from the provided JSON. Do not invent values. "
    "No emojis, no disclaimers."
)

SYSTEM_INSTRUCTION_CHAT = (
    "You are PowerPulse, a concise residential energy coach. "
    "Respond with one clear, supportive suggestion (<= 200 characters). "
    "Reference the chat when helpful. No emojis, no disclaimers."
)

if KEY:
    genai.configure(api_key=KEY)
    _nudge_model = genai.GenerativeModel(
        MODEL_NAME,
        system_instruction=SYSTEM_INSTRUCTION_NUDGE,
    )
    _chat_model = genai.GenerativeModel(
        MODEL_NAME,
        system_instruction=SYSTEM_INSTRUCTION_CHAT,
    )
else:
    _nudge_model = None
    _chat_model = None


def _require_model(kind: str = "nudge"):
    model = _nudge_model if kind == "nudge" else _chat_model
    if model is None:
        raise LLMUnavailable(
            "Gemini client is not configured. "
            "Set GEMINI_API_KEY (and optionally GEMINI_MODEL) in your environment."
        )
    return model


def build_nudge(persona: str, context: Mapping[str, object]) -> str:
    """
    persona: 'eco' | 'budget' | 'comfort'
    context: {
      'top_event': { 'savings': {'kwh','co2_g','cost_usd'}, 'type', 'suggestion', 'reason', 'at' },
      'summary': {'todayKwh','potentialSavingsKwh'},
      'tariff': {'is_peak': bool, 'cents_per_kwh': float},
      'location': {'city': str}
    }
    """
    model = _require_model("nudge")

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

    user = (
        'Return JSON like {"message":"..."}.\n'
        "Analytics JSON:\n" + json.dumps(payload, ensure_ascii=False)
    )

    try:
        resp = model.generate_content(
            [{"text": user}],
            generation_config={"temperature": 0.2, "max_output_tokens": 300},
            request_options={"timeout": 20},
        )
    except Exception as exc:
        raise RuntimeError("Gemini build_nudge request failed") from exc

    text = (getattr(resp, "text", "") or "").strip()
    if text.startswith("{"):
        try:
            text = json.loads(text).get("message", "").strip()
        except Exception as exc:
            raise RuntimeError("Gemini build_nudge returned invalid JSON") from exc
    if not text:
        raise RuntimeError("Gemini build_nudge returned empty response")
    return " ".join(text.split())


def chat_reply(
    messages: Sequence[Mapping[str, str]],
    persona: str | None = None,
    context: Mapping[str, object] | None = None,
) -> str:
    model = _require_model("chat")
    persona = persona or "eco"
    context = context or {}

    history = [
        {"role": m.get("role", "user"), "content": m.get("content", "")}
        for m in messages[-10:]
    ]
    payload = {
        "persona": persona,
        "context": context,
        "history": history,
    }

    user_prompt = (
        "Chat history JSON (latest last). Provide the next assistant reply.\n"
        + json.dumps(payload, ensure_ascii=False)
    )

    try:
        resp = model.generate_content(
            [{"text": user_prompt}],
            generation_config={"temperature": 0.3, "max_output_tokens": 350},
            request_options={"timeout": 20},
        )
    except Exception as exc:
        raise RuntimeError("Gemini chat_reply request failed") from exc

    text = (getattr(resp, "text", "") or "").strip()
    if not text:
        raise RuntimeError("Gemini chat_reply returned empty response")
    return " ".join(text.split())