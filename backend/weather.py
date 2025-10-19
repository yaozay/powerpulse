from __future__ import annotations
from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta
import requests

def fetch_hourly(lat: float, lng: float, hours: int, tz: str) -> List[Dict[str, Any]]:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat, "longitude": lng, "timezone": tz,
        "hourly": ["temperature_2m", "relative_humidity_2m"],
        "forecast_days": 2
    }
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    j = r.json()
    times = j["hourly"]["time"]
    temps = j["hourly"]["temperature_2m"]
    rhs   = j["hourly"]["relative_humidity_2m"]

    out = []
    now = datetime.now(timezone.utc)
    for t, T, H in zip(times, temps, rhs):
        ts = datetime.fromisoformat(t.replace("Z", "+00:00"))
        if ts >= now and len(out) < hours:
            out.append({"ts": ts, "tempC": float(T), "rh": float(H)})

    if not out:
        # fallback to earliest if nowcast filter was empty
        for t, T, H in zip(times[:hours], temps[:hours], rhs[:hours]):
            ts = datetime.fromisoformat(t.replace("Z", "+00:00"))
            out.append({"ts": ts, "tempC": float(T), "rh": float(H)})
    return out
