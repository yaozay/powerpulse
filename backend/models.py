from pydantic import BaseModel
from typing import List, Literal

class AnalyzeReq(BaseModel):
    indoor: dict | None = None 
    home: dict | None = None   
    prefs: dict | None = None  
    location: dict             

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


class CoachChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class CoachChatReq(BaseModel):
    messages: List[CoachChatMessage]
    persona: Literal["eco", "budget", "comfort"] | None = None
    context: dict | None = None


class CoachChatResp(BaseModel):
    message: str
