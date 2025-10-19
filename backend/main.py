import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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
from services.csv_processor import EnergyDataProcessor

load_dotenv()
app = FastAPI(title="PowerPulse Backend")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize CSV processor with proper path handling
csv_path = os.getenv("CSV_DATA_PATH")
if csv_path is None:
    # Auto-detect path relative to main.py
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

@app.get("/health")
def health(): 
    return {"ok": True, "csv_loaded": csv_processor.df is not None}

# ============= ORIGINAL ANALYZE ENDPOINT =============
@app.post("/analyze", response_model=AnalyzeResp)
def analyze(req: AnalyzeReq):
    lat, lng = req.location["lat"], req.location["lng"]
    home_size = (req.home or {}).get("size", "medium")
    persona = (req.prefs or {}).get("comfort", "eco")

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
    
    Returns:
    - current_power_kw: Current power draw
    - today_usage_kwh: Total energy usage today
    - today_cost_usd: Total cost today
    - today_co2_kg: Total CO2 emissions today
    - hourly_usage_24h: 24-hour hourly breakdown
    - weather: Current weather conditions
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)