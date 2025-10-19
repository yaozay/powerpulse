from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

# ---------- Requests ----------
class AnalyzeReq(BaseModel):
    location: Optional[Dict[str, float]] = None  
    home: Optional[Dict[str, Any]] = None        
    prefs: Optional[Dict[str, Any]] = None       

class InferenceRow(BaseModel):
    timestamp: datetime
    kwh: float
    temp_out_c: float
    humidity: float
    hour: int
    dayofweek: int
    is_peak: int
    baseline_kwh_per_hour: float
    tariff_usd_per_kwh: float
    home_size_sqft: float
    occupants: int
    ma3: float
    ma12: float
    lag1: float
    lag2: float
    season: Optional[str] = None
    hvac_type: Optional[str] = None
    comfort_level: Optional[str] = None

class PredictRequest(BaseModel):
    rows: List[InferenceRow]

# ---------- Responses ----------
class SeriesItem(BaseModel):
    ts: datetime
    predicted_kwh: float
    baseline_kwh: float

class Savings(BaseModel):
    kwh: float
    co2_g: int
    cost_usd: float

class Event(BaseModel):
    type: str                    # "SPIKE" | "PEAK" | "NORMAL"
    at: datetime
    suggestion: str              # "RAISE_THERM" | "SHIFT_APPLIANCE" | "NONE"
    savings: Savings
    reason: str

class AnalyzeSummary(BaseModel):
    today_kwh: float = Field(alias="todayKwh")
    potential_savings_kwh: float = Field(alias="potentialSavingsKwh")
    class Config:
        populate_by_name = True

class AnalyzeResp(BaseModel):
    horizon_minutes: int = Field(alias="horizonMinutes")
    series: List[SeriesItem]
    events: List[Event]
    summary: AnalyzeSummary
    nudge: str
    class Config:
        populate_by_name = True

class PredictResponse(BaseModel):
    predictions_kwh_next: List[float]
