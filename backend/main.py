import os
from pathlib import Path
from datetime import datetime
from typing import List, Literal, Dict, Any, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel

from models import AnalyzeReq, AnalyzeResp
from services.weather import fetch_hourly
from services.tariff import is_peak, tariff_cents
from services.analytics import (
    baseline_by_size, predict_kwh, deviation,
    savings_raise_thermostat, savings_shift_appliance,
    co2_g, cost_usd
)
from services.llm import build_nudge, chat_with_energy_data
from services.csv_processor import EnergyDataProcessor

load_dotenv()

app = FastAPI(title="PowerPulse Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", "http://127.0.0.1:3000",
        "http://localhost:5173", "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------
# Models
# --------------------------
class ChatMsg(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ChatReq(BaseModel):
    message: str
    home_id: Optional[int] = 1
    history: List[Dict[str, Any]] = []

# --------------------------
# CSV init
# --------------------------
csv_path = os.getenv("CSV_DATA_PATH")
if csv_path is None:
    base_dir = Path(__file__).parent
    csv_path = base_dir / "data" / "powerpulse-datas.csv"
    print(f"📁 Using default CSV path: {csv_path}")
else:
    csv_path = Path(csv_path)
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
    """Try common datetime column names."""
    for c in ["DateTime", "Datetime", "Timestamp", "Time", "Date"]:
        if c in df.columns:
            return c
    return None

def _find_kwh_col(df: pd.DataFrame) -> Optional[str]:
    """Try common energy column names."""
    for c in ["Energy Consumption (kWh)", "kWh", "Usage (kWh)", "Energy_kWh"]:
        if c in df.columns:
            return c
    return None

def compute_evening_metrics_from_df(df: pd.DataFrame, home_id: int,
                                    tariff_usd_per_kwh: float,
                                    grid_intensity_kg_per_kwh: float) -> Dict[str, float]:
    """
    Compute total energy, cost, and CO₂ for the evening (5–10 pm) window for a given home_id.
    Falls back to zeros if data/columns are missing.
    """
    if df is None or df.empty:
        return {"evening_kwh": 0.0, "evening_cost_usd": 0.0, "evening_co2_kg": 0.0}

    # Filter by home
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

    # Define today's 5pm–10pm in the dataframe's (naive) local timeframe
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
# Chat endpoint
# --------------------------
@app.post("/chat/energy-coach")
def energy_coach(req: ChatReq):
    try:
        # 0) normalize message
        msg_raw = (req.message or "").strip()
        msg_lower = msg_raw.lower()

        # --- guards & quick replies (no LLM) ---
        SMALL_TALK = {
            "how are you", "what's up", "whats up", "how’s it going", "hows it going",
            "hello", "hi", "hey", "sup", "yo", "good morning", "good evening", "good night"
        }
        THANKS = {"thanks", "thank you", "ty", "thx", "appreciate it", "appreciate it!"}

        if any(phrase in msg_lower for phrase in SMALL_TALK):
            return {"reply": "Hey! I’m your energy coach. Ask me about cutting evening usage, shifting laundry, thermostat tips, or saving on your bill."}
        if any(phrase in msg_lower for phrase in THANKS):
            return {"reply": "Anytime! Want tips for tonight’s 5–10 pm window or for lowering your monthly bill?"}

        alnum_count = sum(ch.isalnum() for ch in msg_raw)
        if alnum_count < 2:
            return {"reply": "Try a question like: “How can I cut my evening usage?” or “What thermostat setting saves the most?”"}

        # --- classify intent ---
        QUESTION_WORDS = ["how", "what", "why", "when", "which", "where", "should", "could", "tips", "recommend", "ideas"]
        ENERGY_KEYWORDS = [
            "energy","usage","kwh","bill","cost","evening","peak","off-peak","off peak",
            "thermostat","ac","a/c","heater","laundry","dishwasher","oven","air fryer",
            "lighting","lights","phantom","vampire","standby","reduce","save","savings"
        ]
        is_question = any(w in msg_lower for w in QUESTION_WORDS) or msg_lower.endswith("?")
        is_energy = any(k in msg_lower for k in ENERGY_KEYWORDS)
        wants_nudge = any(p in msg_lower for p in ["nudge", "one tip", "one quick tip", "short tip"])

        if not is_energy:
            return {"reply": "I can help with energy: ask about evening usage, thermostat, laundry timing, cooking methods, or lighting."}

        # --- inputs for context ---
        tariff = float(os.getenv("TARIFF_USD_PER_KWH", "0.15"))
        grid_intensity = float(os.getenv("GRID_INTENSITY_KG_PER_KWH", "0.40"))

        # compute evening metrics from CSV
        try:
            if csv_processor.df is None:
                csv_processor.load_data()
            metrics = compute_evening_metrics_from_df(
                csv_processor.df, req.home_id or 1, tariff, grid_intensity
            )
        except Exception:
            metrics = {"evening_kwh": 0.0, "evening_cost_usd": 0.0, "evening_co2_kg": 0.0}

        # You can also grab dashboard aggregates to enrich chat responses
        # (these are optional; chat_with_energy_data will ignore missing fields)
        try:
            dash = csv_processor.get_dashboard_summary(req.home_id or 1)
        except Exception:
            dash = {}

        context = {
            "home_id": req.home_id or 1,
            "user_message": msg_raw,
            "conversation_history": [m.get("content", "") for m in (req.history or [])][-10:],
            "tariff_usd_per_kwh": tariff,
            "grid_intensity_kg_per_kwh": grid_intensity,
            **metrics,
            # Optional broader stats for better answers
            "current_power_kw": dash.get("current_power_kw"),
            "today_usage_kwh": dash.get("today_usage_kwh"),
            "today_cost_usd": dash.get("today_cost_usd"),
            "today_co2_kg": dash.get("today_co2_kg"),
            "weather": dash.get("weather"),
            "potentials": [
                {"name": "Dishwasher", "shift_kwh": 0.9, "note": "Run after 10 pm or use eco cycle"},
                {"name": "Washer/Dryer", "shift_kwh": 2.0, "note": "Delay to off-peak; use low-heat dryer"},
                {"name": "Oven → Air Fryer", "save_kwh": 0.6, "note": "Use air fryer/microwave for small meals"},
                {"name": "Lighting", "save_kwh": 0.2, "note": "Use task lighting; turn off empty rooms"},
                {"name": "Phantom Loads", "save_kwh": 0.15, "note": "Power strip for TV/console/chargers"},
            ],
        }

        # --- route by intent ---
        if wants_nudge:
            # explicit “one tip” -> short nudge
            reply = build_nudge(persona="friendly", context=context)
        elif is_question:
            # natural questions -> fuller chat answer that uses the actual message + history
            reply = chat_with_energy_data(context)
        else:
            # energy-related but not an explicit question -> give a concise nudge by default
            reply = build_nudge(persona="friendly", context=context)

        return {"reply": reply}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --------------------------
# Health + analyze + dashboard
# --------------------------
@app.get("/health")
def health():
    return {"ok": True, "csv_loaded": csv_processor.df is not None}

# ============= ORIGINAL ANALYZE ENDPOINT =============
@app.post("/analyze", response_model=AnalyzeResp)
def analyze(req: AnalyzeReq):
    lat, lng = req.location["lat"], req.location["lng"]
    home_size = (req.home or {}).get("size", "medium")
    persona = (req.prefs or {}).get("comfort", "eco")

    hourly = fetch_hourly(lat, lng)
    base = baseline_by_size(home_size)
    series = []
    for h in hourly:
        pred = predict_kwh(base, h["tempC"])
        series.append({
            "ts": h["ts"],
            "predicted_kwh": pred,
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

    nudge = build_nudge(persona, context)

    return {
        "horizonMinutes": 12 * 60,
        "series": series,
        "events": events,
        "summary": {"todayKwh": today_kwh, "potentialSavingsKwh": potential},
        "nudge": nudge
    }

# ============= NEW CSV DASHBOARD ENDPOINTS =============
@app.get("/dashboard/metrics")
@app.get("/dashboard/metrics/{home_id}")
def get_dashboard_metrics(home_id: int = 1):
    """
    Get all dashboard metrics from CSV data
    """
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
    """Get current power reading in kW"""
    try:
        return {"current_power_kw": csv_processor.get_current_power(home_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard/today-stats/{home_id}")
def get_today_stats(home_id: int = 1):
    """Get today's usage, cost, and CO2 in one call"""
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
    """Get 24-hour hourly usage for chart"""
    try:
        return {"data": csv_processor.get_24h_hourly_usage(home_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard/weather/{home_id}")
def get_weather_info(home_id: int = 1):
    """Get current weather data from CSV"""
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
    """Get list of available home IDs in the CSV"""
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
