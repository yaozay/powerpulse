def build_nudge(persona: str, ctx: dict) -> str:
    # ctx: {"peak": bool, "top_event": {...}, "today_kwh": float, "pot_kwh": float}
    e = ctx.get("top_event", {})
    if persona == "budget":
        return f"Peak rates now—shift a cycle to later and save about ${e.get('savings',{}).get('cost_usd',0):.2f}."
    if persona == "comfort":
        return "It’s warming up—raise thermostat by 2°F to trim the peak without losing comfort."
    # eco default
    return f"Small changes now could avoid ~{e.get('savings',{}).get('co2_g',0)} g CO₂ today."
