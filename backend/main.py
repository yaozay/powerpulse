import yaml
from pathlib import Path
from fastapi import FastAPI, HTTPException
from datetime import datetime
from app.schemas import AnalyzeReq, AnalyzeResp, PredictRequest, PredictResponse, SeriesItem, Event, Savings, AnalyzeSummary
from app.weather import fetch_hourly
from app.tariff import is_peak, tariff_cents
from app.analytics import (
    baseline_by_size, predict_kwh_rule, deviation,
    savings_raise_thermostat, savings_shift_appliance,
    co2_g, cost_usd
)
from app.ridge_adapter import predict_batch


CFG = yaml.safe_load(Path("config.yaml").read_text())
MODEL_PATH = CFG["model"]["path"]

TZ = CFG["location"]["timezone"]

app = FastAPI(title="PowerPulse Backend", version="1.0")

@app.get("/health")
def health():
    ok = Path(MODEL_PATH).exists()
    return {"ok": True, "model_present": ok, "model_path": MODEL_PATH}

@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    try:
        preds = predict_batch([r.model_dump() for r in req.rows], MODEL_PATH)
        return PredictResponse(predictions_kwh_next=[float(x) for x in preds])
    except FileNotFoundError:
        raise HTTPException(status_code=400, detail="Model not found. Train first (training/train.py).")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"predict_failed: {e}")

@app.post("/analyze", response_model=AnalyzeResp)
def analyze(req: AnalyzeReq):
    # 1) resolve location & persona
    loc = (req.location or {}) or {}
    lat = loc.get("lat", CFG["location"]["lat"])
    lng = loc.get("lng", CFG["location"]["lng"])
    home_size = (req.home or {}).get("size", "medium")

    # 2) weather horizon (12h)
    try:
        hourly = fetch_hourly(lat, lng, hours=12, tz=TZ)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"weather_unavailable: {e}")

    if not hourly:
        empty = AnalyzeResp(
            horizon_minutes=0,
            series=[],
            events=[],
            summary=AnalyzeSummary.model_validate({"todayKwh":0.0,"potentialSavingsKwh":0.0}),
            nudge="No weather data; unable to analyze."
        )
        return empty

    # 3) baseline & predictions (use trained model if present, else rule-based)
    base = baseline_by_size(home_size)
    series = []
    events = []

    # Build rows for model inference (if model exists)
    model_ready = Path(MODEL_PATH).exists()
    if model_ready:
        rows = []
        for h in hourly:
            ts = h["ts"]
            row = dict(
                timestamp=ts.isoformat(),
                kwh=base,  # simple prior
                temp_out_c=float(h["tempC"]),
                humidity=float(h.get("rh", 50.0)),
                hour=ts.hour,
                dayofweek=ts.weekday(),
                is_peak=int(is_peak(ts, *CFG["model"]["peak_hours"])),
                baseline_kwh_per_hour=base,
                tariff_usd_per_kwh=0.26,
                home_size_sqft=1200,
                occupants=2,
                ma3=base, ma12=base, lag1=base, lag2=base,
                season="summer", hvac_type="central_ac", comfort_level="2",
            )
            rows.append(row)
        yhat = predict_batch(rows, MODEL_PATH)
        for h, pred in zip(hourly, yhat):
            series.append(SeriesItem(ts=h["ts"], predicted_kwh=float(pred), baseline_kwh=round(base,4)))
    else:
        for h in hourly:
            pred = predict_kwh_rule(base, h["tempC"])
            series.append(SeriesItem(ts=h["ts"], predicted_kwh=float(pred), baseline_kwh=round(base,4)))

    # 4) events & savings
    for p in series:
        peak = is_peak(p.ts, *CFG["model"]["peak_hours"])
        dev  = deviation(p.predicted_kwh, p.baseline_kwh)
        if dev >= 0.20:
            saved = savings_raise_thermostat(p.predicted_kwh, 2.0)
            cents = tariff_cents(peak, CFG["tariff"]["peak_cents_per_kwh"], CFG["tariff"]["offpeak_cents_per_kwh"])
            events.append(Event(
                type="SPIKE", at=p.ts, suggestion="RAISE_THERM",
                savings=Savings(
                    kwh=round(saved,3),
                    co2_g=co2_g(saved),
                    cost_usd=cost_usd(saved, cents)
                ),
                reason=f"Predicted usage {int(dev*100)}% above baseline"
            ))
        elif peak:
            saved = savings_shift_appliance(1.0)
            cents = tariff_cents(True, CFG["tariff"]["peak_cents_per_kwh"], CFG["tariff"]["offpeak_cents_per_kwh"])
            events.append(Event(
                type="PEAK", at=p.ts, suggestion="SHIFT_APPLIANCE",
                savings=Savings(
                    kwh=round(saved,3),
                    co2_g=co2_g(saved),
                    cost_usd=cost_usd(saved, cents)
                ),
                reason="Peak tariff window"
            ))
        else:
            events.append(Event(
                type="NORMAL", at=p.ts, suggestion="NONE",
                savings=Savings(kwh=0.0, co2_g=0, cost_usd=0.0),
                reason="Within expected range"
            ))

    # 5) summary + plain nudge text
    today_kwh = round(sum(s.predicted_kwh for s in series), 3)
    potential = round(sum(e.savings.kwh for e in events if e.type != "NORMAL"), 3)

    # choose top non-normal by savings
    non_normal = [e for e in events if e.type != "NORMAL"]
    top = max(non_normal, key=lambda e: e.savings.kwh) if non_normal else events[0]
    nudge = f"{top.reason}. Estimated savings ~{top.savings.kwh:.2f} kWh (~${top.savings.cost_usd:.2f}, {top.savings.co2_g} g CO₂)."

    resp = AnalyzeResp(
        horizon_minutes=len(series)*60,
        series=series,
        events=events,
        summary=AnalyzeSummary.model_validate({"todayKwh": today_kwh, "potentialSavingsKwh": potential}),
        nudge=nudge
    )
    return resp
