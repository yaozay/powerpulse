import os
from fastapi import FastAPI
from dotenv import load_dotenv
from models import AnalyzeReq, AnalyzeResp
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
from services.llm import build_nudge
from services.ridge_model import load_forecast

load_dotenv()
app = FastAPI(title="PowerPulse Backend")

@app.get("/health")
def health(): return {"ok": True}

@app.post("/analyze", response_model=AnalyzeResp)
def analyze(req: AnalyzeReq):
    lat, lng = req.location["lat"], req.location["lng"]
    home_size = (req.home or {}).get("size", "medium")
    persona   = (req.prefs or {}).get("comfort", "eco")  # eco|budget|comfort

    # 1) Weather (next 12 hours)
    hourly = fetch_hourly(lat, lng)  # [{ts, tempC, rh}...]

    # 2) Model forecast (48h) + baseline projections
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

    # 3) Events (SPIKE/PEAK/NORMAL) + savings
    events = []
    for p in series:
        peak = is_peak(p["ts"])
        dev  = deviation(p["predicted_kwh"], p["baseline_kwh"])
        if dev >= 0.20:
            # SPIKE → RAISE_THERM
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
            # PEAK → SHIFT_APPLIANCE
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

    # 4) Summary + best event
    today_kwh = round(sum(p["predicted_kwh"] for p in series), 2)
    potential = round(sum(e["savings"]["kwh"] for e in events if e["type"] != "NORMAL"), 2)
    top_event = max(events, key=lambda e: (e["savings"]["kwh"], e["type"]!="NORMAL"))

    context = {
    "location": {"city": "Houston"},           # optional
    "tariff": {"is_peak": True},               # or your actual tariff state
    "top_event": top_event,
    "summary": {"todayKwh": today_kwh, "potentialSavingsKwh": potential}
    }
    
    nudge = build_nudge(persona, context)

    return {
        "horizonMinutes": 12*60,
        "series": series,
        "events": events,
        "summary": {"todayKwh": today_kwh, "potentialSavingsKwh": potential},
        "nudge": nudge
    }
