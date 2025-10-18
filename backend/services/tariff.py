import os
from datetime import datetime
from zoneinfo import ZoneInfo

PEAK_START = 15  # 3pm local
PEAK_END   = 19  # 7pm local

def is_peak(ts_iso: str, tz_str: str = "America/Chicago") -> bool:
    from datetime import datetime
    from zoneinfo import ZoneInfo
    dt = datetime.fromisoformat(ts_iso.replace("Z","+00:00")).astimezone(ZoneInfo(tz_str))
    return 15 <= dt.hour < 19


def tariff_cents(peak: bool) -> float:
    if peak:
        return float(os.getenv("TARIFF_CENTS_PER_KWH_PEAK", "32"))
    return float(os.getenv("TARIFF_CENTS_PER_KWH_OFFPEAK", "12"))
