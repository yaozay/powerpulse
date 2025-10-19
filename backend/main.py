import os
from pathlib import Path
from datetime import datetime
from typing import List, Literal, Dict, Any, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel

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
from services.csv_processor import EnergyDataProcessor

load_dotenv()

app = FastAPI(title="PowerPulse Backend")

# --------------------------
# CORS (env override + localhost defaults)
# --------------------------
frontend_origin = os.getenv("FRONTEND_ORIGIN")
default_origins = [
    "http://localhost:3000", "http://127.0.0.1:3000",
    "http://localhost:5173", "http://127.0.0.1:5173",
]
allow_origins = [frontend_origin] if frontend_origin else default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,   # allow cookies/tokens if you need them
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------
# Request models for chat
# --------------------------
class ChatMsg(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ChatReq(BaseModel):
    message: str
    home_id: Optional[int] = 1
    history: List[Dict[str, Any]] = []  # e.g., [{role, content}, ...]

# --------------------------
# CSV init
# --------------------------
csv_path_env = os.getenv("CSV_DATA_PATH")
if csv_path_env is None:
    base_dir = Path(__file__).parent
    csv_path = base_dir / "data" / "powerpulse-datas.csv"
    print(f"📁 Using default CSV path: {csv_path}")
else:
    csv_path = Path(csv_path_env)
    print(f"📁 Using CSV path from .env: {csv_path}")

csv_processor = EnergyDataProcessor(str(csv_path))
try:
    csv_processor.load_data()
    print(f"✓ CSV loaded: {len(csv_processor.df)} rows")
except Exception as e:
    print(f"⚠ CSV not loaded: {e}")

# --------------------------
# Helpers
# --------------------------
def _find_datetime_col(df: pd.DataFrame) -> Optional[str]:
    for c in ["DateTime", "Datetime", "Timestamp", "Time", "Date"]:
        if c in df.columns:
            return c
    return None

def _find_kwh_col(df: pd.DataFrame) -> Optional[str]:
    for c in ["Energy Consumption (kWh)", "kWh", "Usage (kWh)", "Energy_kWh"]:
        if c in df.columns:
            return c
    return None

def compute_evening_metrics_from_df(
    df: pd.DataFrame,
    home_id: int,
    tariff_usd_per_kwh: float,
    grid_intensity_kg_per_kwh: float
) -> Dict[str, float]:
    if df is None or df.empty:
        return {"evening_kwh": 0.0, "evening_cost_usd": 0.0, "evening_co2_kg": 0.0}

    dfh = df
    if "Home ID" in df.columns:
        dfh = df[df["Home ID"] == home_id]
        if dfh.empty:
            return {"evening_kwh": 0.0, "evening_cost_usd": 0.0, "evening_co2_kg": 0.0}

    dt_col = _find_datetime_col(dfh)
    kwh_col = _find_kwh_col(dfh)
    if not dt_col or not kwh_col:
        return {"evening_kwh": 0.0, "evening_cost_usd": 0.0, "evening_co2_kg": 0.0}

    # Ensure datetime dtype
    if not pd.api.types.is_datetime64_any_dtype(dfh[dt_col]):
        try:
            dfh = dfh.copy()
            dfh[dt_col] = pd.to_datetime(dfh[dt_col])
        except Exception:
            return {"evening_kwh": 0.0, "evening_cost_usd": 0.0, "evening_co2_kg": 0.0}

    now = pd.Timestamp.now(tz=dfh[dt_col].dt.tz) if getattr(dfh[dt_col].dt, "tz", None) else pd.Timestamp.now()
    start = now.normalize() + pd.Timedelta(hours=17)  # 5 pm
    end = now.normalize() + pd.Timedelta(hours=22)    # 10 pm

    mask = (dfh[dt_col] >= start) & (dfh[dt_col] < end)
    evening_kwh = float(dfh.loc[mask, kwh_col].sum())

    return {
        "evening_kwh": evening_kwh,
        "evening_cost_usd": evening_kwh * float(tariff_usd_per_kwh),
        "evening_co2_kg": evening_kwh * float(grid_intensity_kg_per_kwh),
    }

# --------------------------
# Chat endpoint (used by frontend coach)
# --------------------------
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


# --------------------------
# Health + analyze + dashboard
# --------------------------
@app.get("/health")
def health():
    return {"ok": True, "csv_loaded": csv_processor.df is not None}

@app.get("/homes/{home_id}/devices")
def get_devices(home_id: int = 1):
    try:
        devices = csv_processor.get_devices(home_id)
        return {"home_id": home_id, "devices": devices}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="CSV data file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/homes/{home_id}/devices/{appliance}/stats")
def get_device_stats(home_id: int, appliance: str):
    try:
        stats = csv_processor.get_device_stats(home_id, appliance)
        return stats
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="CSV data file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= ANALYZE ENDPOINT (forecast-aware) =============
@app.post("/analyze", response_model=AnalyzeResp)
def analyze(req: AnalyzeReq):
    lat, lng = req.location["lat"], req.location["lng"]
    home_size = (req.home or {}).get("size", "medium")
    persona = (req.prefs or {}).get("comfort", "eco")

    hourly = fetch_hourly(lat, lng)

    # Try loading a ridge forecast; fall back to predict_kwh
    try:
        forecast = load_forecast()  # list of dicts with "predicted_kwh"
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
        dev = deviation(p["predicted_kwh"], p["baseline_kwh"])
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
    top_event = max(events, key=lambda e: (e["savings"]["kwh"], e["type"] != "NORMAL"))

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
        "horizonMinutes": 12 * 60,
        "series": series,
        "events": events,
        "summary": {"todayKwh": today_kwh, "potentialSavingsKwh": potential},
        "nudge": nudge
    }

# ============= CSV DASHBOARD ENDPOINTS =============
@app.get("/dashboard/metrics")
@app.get("/dashboard/metrics/{home_id}")
def get_dashboard_metrics(home_id: int = 1):
    try:
        if csv_processor.df is None:
            csv_processor.load_data()
        data = csv_processor.get_dashboard_summary(home_id)
        return data
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="CSV data file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/dashboard/current-power/{home_id}")
def get_current_power(home_id: int = 1):
    try:
        return {"current_power_kw": csv_processor.get_current_power(home_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard/today-stats/{home_id}")
def get_today_stats(home_id: int = 1):
    try:
        return {
            "usage_kwh": csv_processor.get_today_usage(home_id),
            "cost_usd": csv_processor.get_today_cost(home_id),
            "co2_kg": csv_processor.get_today_co2(home_id),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard/hourly/{home_id}")
def get_hourly_breakdown(home_id: int = 1):
    try:
        return {"data": csv_processor.get_24h_hourly_usage(home_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard/weather/{home_id}")
def get_weather_info(home_id: int = 1):
    try:
        weather = csv_processor.get_weather_data(home_id)
        if weather is None:
            raise HTTPException(status_code=404, detail="No weather data")
        return weather
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard/homes")
def get_available_homes():
    try:
        if csv_processor.df is None:
            csv_processor.load_data()

        homes = []
        home_ids = csv_processor.df['Home ID'].unique() if 'Home ID' in csv_processor.df.columns else []
        for hid in sorted(home_ids):
            home_data = csv_processor.df[csv_processor.df['Home ID'] == hid]
            location = home_data['Location City'].iloc[0] if len(home_data) > 0 and 'Location City' in home_data.columns else "Unknown"
            homes.append({
                "id": int(hid),
                "name": f"Home {hid} - {location}",
                "location": location,
                "data_points": len(home_data)
            })
        return {"homes": homes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --------------------------
# Entrypoint
# --------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
