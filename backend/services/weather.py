import os, requests
from functools import lru_cache
from datetime import datetime, timedelta, timezone

BASE = os.getenv("WEATHER_API_URL", "https://api.open-meteo.com/v1/forecast")

@lru_cache(maxsize=64)
def fetch_hourly(lat: float, lng: float):
    url = f"{BASE}?latitude={lat}&longitude={lng}&hourly=temperature_2m,relative_humidity_2m&forecast_days=1"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    j = r.json()
    hours = j["hourly"]["time"]
    temps = j["hourly"]["temperature_2m"]
    rhs   = j["hourly"]["relative_humidity_2m"]

    # start from the next 3 hours to catch midday/afternoon
    nowz = datetime.now(timezone.utc)
    start_idx = next((i for i,t in enumerate(hours) if t >= nowz.isoformat(timespec='minutes').replace('+00:00','Z')), 0)
    start_idx = min(start_idx + 3, len(hours)-12)
    end_idx = start_idx + 12

    hours = hours[start_idx:end_idx]
    temps = temps[start_idx:end_idx]
    rhs   = rhs[start_idx:end_idx]
    return [{"ts": t, "tempC": float(tc), "rh": float(rh)} for t, tc, rh in zip(hours, temps, rhs)]
