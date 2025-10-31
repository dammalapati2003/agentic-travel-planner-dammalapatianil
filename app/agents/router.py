import json
from ..llm import chat
from ..prompts import router_system
from ..utils import date_utils
from ..tools import weather as weather_tool  

def route(query: str, tz: str):
    system = {"role": "system", "content": router_system.SYSTEM_PROMPT}
    user = {"role": "user", "content": query}

    out = chat([system, user], temperature=0.0)

    # Expect pure JSON from the LLM 
    try:
        data = json.loads(out.strip())
    except Exception:
        # Minimal safe fallback 
        data = {
            "intent": "poi",
            "city": "",
            "days": 2,
            "relative_date_phrase": query,
            "poi_topic": "general",
            "guide_topic": "none",
        }

    # City: if empty, try live geocode 
    city = (data.get("city") or "").strip()
    if not city:
        try:
            g = weather_tool.geocode_city(query)
            city = g.get("name") or ""
        except Exception:
            city = ""

    # Days 
    try:
        days = int(data.get("days") or 2)
    except Exception:
        days = 2
    if days < 1:
        days = 1

    # Dates from relative phrase 
    rel = data.get("relative_date_phrase") or query
    start, end = date_utils.resolve_dates(rel, tz_name=tz, default_days=days)

    return {
        "intent": data.get("intent", "poi"),
        "city": city,
        "start_date": start,
        "end_date": end,
        "days": days,
        "poi_topic": data.get("poi_topic", "general"),
        "guide_topic": data.get("guide_topic", "none"),
    }
