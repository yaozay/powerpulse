import os

BASELINES = {"small": 0.7, "medium": 1.2, "large": 1.8}  # kWh/h
TEMP_REF = 22.0     # was 24.0 → more heat effect
ALPHA    = 1.0      # was 0.5 → higher temp sensitivity
HVAC_SHARE = 0.7       # portion of load that's HVAC during hot hours
GRID_EF = float(os.getenv("GRID_EMISSIONS_KG_PER_KWH","0.45"))  # kg/kWh

def baseline_by_size(size: str | None) -> float:
    return BASELINES.get((size or "medium"), 1.2)

def predict_kwh(baseline: float, tempC: float) -> float:
    pred = baseline + ALPHA * ((tempC - TEMP_REF) / 10.0)
    return max(0.1, round(pred, 3))

def deviation(pred: float, base: float) -> float:
    return (pred - base) / max(0.1, base)

def savings_raise_thermostat(pred_kwh: float, delta_F: float = 2.0) -> float:
    # ~3% per °F on HVAC portion
    return round(pred_kwh * HVAC_SHARE * 0.03 * delta_F, 3)

def savings_shift_appliance(kwh_cycle: float = 1.0) -> float:
    # energy “saved” is in $ (moving out of peak); for simplicity keep kWh = 1.0 as avoided peak use
    return float(kwh_cycle)

def co2_g(kwh: float) -> int:
    return int(round(kwh * GRID_EF * 1000))

def cost_usd(kwh: float, cents_per_kwh: float) -> float:
    return round(kwh * (cents_per_kwh / 100.0), 2)
