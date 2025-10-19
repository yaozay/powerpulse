"""
Add this to your main.py or create as a separate router file
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from services.csv_processor import EnergyDataProcessor

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Initialize processor
csv_path = "backend/data/powerpulse-datas.csv"  # Adjust path as needed
processor = EnergyDataProcessor(csv_path)

class HourlyUsage(BaseModel):
    time: str
    hour: int
    kwh: float

class Weather(BaseModel):
    temperature_f: int
    temperature_c: float
    indoor_temperature_c: float
    humidity: Optional[int] = None
    wind_speed: Optional[int] = None

class DashboardResponse(BaseModel):
    current_power_kw: float
    today_usage_kwh: float
    today_cost_usd: float
    today_co2_kg: float
    hourly_usage_24h: List[HourlyUsage]
    weather: Optional[Weather]

@router.get("/metrics/{home_id}", response_model=DashboardResponse)
def get_dashboard_metrics(home_id: int = 1):
    """
    Get all dashboard metrics for a specific home
    
    Returns:
    - current_power_kw: Current power draw in kilowatts
    - today_usage_kwh: Total energy usage today in kWh
    - today_cost_usd: Total cost today in USD
    - today_co2_kg: Total CO2 emissions today in kg
    - hourly_usage_24h: Hourly breakdown for last 24 hours
    - weather: Current weather conditions
    """
    try:
        data = processor.get_dashboard_summary(home_id)
        return data
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="CSV data file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing data: {str(e)}")

@router.get("/current-power/{home_id}")
def get_current_power(home_id: int = 1):
    """Get just the current power reading"""
    try:
        return {"current_power_kw": processor.get_current_power(home_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/today-usage/{home_id}")
def get_today_usage(home_id: int = 1):
    """Get today's total energy usage"""
    try:
        return {"today_usage_kwh": processor.get_today_usage(home_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/today-cost/{home_id}")
def get_today_cost(home_id: int = 1):
    """Get today's total cost"""
    try:
        return {"today_cost_usd": processor.get_today_cost(home_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/today-co2/{home_id}")
def get_today_co2(home_id: int = 1):
    """Get today's CO2 emissions"""
    try:
        return {"today_co2_kg": processor.get_today_co2(home_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/hourly-usage/{home_id}")
def get_hourly_usage(home_id: int = 1):
    """Get 24-hour hourly usage breakdown"""
    try:
        return {"hourly_usage": processor.get_24h_hourly_usage(home_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/weather/{home_id}")
def get_weather(home_id: int = 1):
    """Get current weather data"""
    try:
        weather = processor.get_weather_data(home_id)
        if weather is None:
            raise HTTPException(status_code=404, detail="No weather data available")
        return weather
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

