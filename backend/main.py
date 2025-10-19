import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from models import AnalyzeReq, AnalyzeResp, CoachChatReq, CoachChatResp
from services.weather import fetch_hourly
from services.tariff import is_peak, tariff_cents
from services.analytics import (
    baseline_by_size,
    predict_kwh,
    deviation,
    savings_raise_thermostat,
    savings_shift_appliance,
    co2_g,
    cost_usd,
)
from services.llm import build_nudge, chat_reply, LLMUnavailable
from services.ridge_model import load_forecast

load_dotenv()
app = FastAPI(title="PowerPulse Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGIN", "*")],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health(): return {"ok": True}

@app.post("/analyze", response_model=AnalyzeResp)
def analyze(req: AnalyzeReq):
    lat, lng = req.location["lat"], req.location["lng"]
    home_size = (req.home or {}).get("size", "medium")
    persona   = (req.prefs or {}).get("comfort", "eco")
    hourly = fetch_hourly(lat, lng)
    try:
        forecast = load_forecast()
    except Exception:
        forecast = []

    base = baseline_by_size(home_size)
    series = []
    for idx, h in enumerate(hourly):
        if idx < len(forecast):
            pred = float(forecast[idx].get("predicted_kwh", base))
        else:
            pred = predict_kwh(base, h["tempC"])
        series.append({
            "ts": h["ts"],
            "predicted_kwh": round(pred, 3),
            "baseline_kwh": round(base, 3)
        })

    events = []
    for p in series:
        peak = is_peak(p["ts"])
        dev  = deviation(p["predicted_kwh"], p["baseline_kwh"])
        if dev >= 0.20:
            saved = savings_raise_thermostat(p["predicted_kwh"], 2.0)
            cents = tariff_cents(peak)
            events.append({
                "type": "SPIKE", "at": p["ts"],
                "suggestion": "RAISE_THERM",
                "savings": {
                    "kwh": saved,
                    "co2_g": co2_g(saved),
                    "cost_usd": cost_usd(saved, cents),
                },
                "reason": f"Predicted usage {int(dev*100)}% above baseline"
            })
        elif peak:
            saved = savings_shift_appliance(1.0)
            cents = tariff_cents(True)
            events.append({
                "type": "PEAK", "at": p["ts"],
                "suggestion": "SHIFT_APPLIANCE",
                "savings": {
                    "kwh": saved,
                    "co2_g": co2_g(saved),
                    "cost_usd": cost_usd(saved, cents),
                },
                "reason": "Peak tariff window"
            })
        else:
            events.append({
                "type": "NORMAL", "at": p["ts"],
                "suggestion": "NONE",
                "savings": {"kwh": 0.0, "co2_g": 0, "cost_usd": 0.0},
                "reason": "Within expected range"
            })

    today_kwh = round(sum(p["predicted_kwh"] for p in series), 2)
    potential = round(sum(e["savings"]["kwh"] for e in events if e["type"] != "NORMAL"), 2)
    top_event = max(events, key=lambda e: (e["savings"]["kwh"], e["type"]!="NORMAL"))

    context = {
    "location": {"city": "Houston"},
    "tariff": {"is_peak": True},
    "top_event": top_event,
    "summary": {"todayKwh": today_kwh, "potentialSavingsKwh": potential}
    }
    
    try:
        nudge = build_nudge(persona, context)
    except LLMUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Gemini nudge failed: {exc}") from exc

    return {
        "horizonMinutes": 12*60,
        "series": series,
        "events": events,
        "summary": {"todayKwh": today_kwh, "potentialSavingsKwh": potential},
        "nudge": nudge
    }


@app.post("/coach/chat", response_model=CoachChatResp)
def coach_chat(req: CoachChatReq):
    history = [msg.model_dump() for msg in req.messages]
    try:
        reply = chat_reply(history, persona=req.persona, context=req.context or {})
    except LLMUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Gemini chat failed: {exc}") from exc
    return {"message": reply}
