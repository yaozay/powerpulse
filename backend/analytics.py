def baseline_by_size(size: str) -> float:
    size = (size or "medium").lower()
    return {"small": 0.6, "medium": 1.0, "large": 1.5}.get(size, 1.0)

def predict_kwh_rule(baseline_kwh: float, temp_c: float) -> float:
    bump = max(0.0, (float(temp_c) - 24.0)) * 0.07
    return max(0.0, baseline_kwh + bump)

def deviation(pred_kwh: float, base_kwh: float) -> float:
    if base_kwh <= 1e-6: return 0.0
    return (pred_kwh - base_kwh) / base_kwh

def savings_raise_thermostat(pred_kwh: float, delta_f: float = 2.0) -> float:
    # ~3.5% per °F; cap at 20%
    pct = min(0.20, 0.035 * float(delta_f))
    return max(0.0, pred_kwh * pct)

def savings_shift_appliance(kwh_to_shift: float = 1.0) -> float:
    return max(0.0, kwh_to_shift)

def co2_g(kwh: float, grid_intensity_g_per_kwh: float = 600.0) -> int:
    return int(round(max(0.0, kwh) * grid_intensity_g_per_kwh))

def cost_usd(kwh: float, cents_per_kwh: float) -> float:
    return round(max(0.0, kwh) * (float(cents_per_kwh) / 100.0), 2)
