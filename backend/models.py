from pydantic import BaseModel
from typing import List, Literal

class AnalyzeReq(BaseModel):
    indoor: dict | None = None   # {"tempC": 26, "rh": 60}
    home: dict | None = None     # {"size":"medium","acKw":2.5}
    prefs: dict | None = None    # {"comfort":"eco","maxTempC":25}
    location: dict               # {"lat": 29.76, "lng": -95.37}

class SeriesPoint(BaseModel):
    ts: str
    predicted_kwh: float
    baseline_kwh: float

class Savings(BaseModel):
    kwh: float
    co2_g: int
    cost_usd: float

class Event(BaseModel):
    type: Literal["SPIKE","PEAK","NORMAL"]
    at: str
    suggestion: Literal["RAISE_THERM","PRECOOL","SHIFT_APPLIANCE","NONE"]
    savings: Savings
    reason: str

class AnalyzeResp(BaseModel):
    horizonMinutes: int
    series: List[SeriesPoint]
    events: List[Event]
    summary: dict
    nudge: str
