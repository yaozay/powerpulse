from datetime import datetime

def is_peak(ts: datetime, start=15, end=19) -> bool:
    return start <= ts.hour <= end

def tariff_cents(peak: bool, peak_cents=26, off_cents=12) -> float:
    return float(peak_cents if peak else off_cents)
