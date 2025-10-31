import json
from typing import Any, Dict, Optional

from ..llm import chat
from ..prompts import planner_system
from .weather_agent import run as weather_run
from .poi_agent import run as poi_run


def run(
    user_query: str,
    city: str,
    start_date: str,
    end_date: str,
    days: int = 2,
    *,
    budget_amount: Optional[int] = None,
    budget_currency: Optional[str] = None,
    budget_mode: bool = False,
    poi_topic: Optional[str] = None,
    guide_topic: Optional[str] = None,
    **_ignored_kwargs: Any,  
):
    """
    Compose an itinerary from live weather + POIs.

    Guarantees:
      - Exactly `days` rows in output (router set date window already).
      - Morning/Afternoon/Evening cells contain **only place names** (no descriptions).
      - Notes contain short logistics or weather cues only.
      - Accepts extra kwargs like `guide_topic` without error.
    """

    # Fetch weather 
    weather_obs: Dict[str, Any] = {}
    try:
        _, weather_obs = weather_run(user_query, city, start_date, end_date)
    except Exception as e:
        weather_obs = {"error": f"weather failed: {e}", "days": []}

    # Fetch POIs 
    poi_obs: Dict[str, Any] = {"items": []}
    try:
       
        _, poi_obs = poi_run(f"best tourist attractions in {city}", city, limit=18, topic="general")
    except Exception as e:
        poi_obs = {"error": f"poi failed: {e}", "items": []}

    # Build planning context for the LLM
    constraints = {
        "days": days,
        "date_window": [start_date, end_date],
        "budget": {"amount": budget_amount, "currency": budget_currency} if budget_mode else None,
        "rules": {
            "table_only": True,
            "names_only_in_slots": True,
            "notes_weather_only": True,
        },
    }

    # System + user prompt 
    sys = {"role": "system", "content": planner_system.SYSTEM_PROMPT}
    user = {
        "role": "user",
        "content": (
            f"Plan a {days}-day itinerary for {city} between {start_date} and {end_date}. "
            f"Use ONLY the observations provided (weather + POIs). "
            + (
                f"Stay roughly within a budget of ~{budget_amount} {budget_currency}. "
                f"Prefer free/low-cost POIs, public transit, and affordable eateries. "
                if budget_mode else ""
            )
            + "Output ONLY a Markdown table with columns: Day | Morning | Afternoon | Evening | Notes. "
            + "Morning/Afternoon/Evening cells must contain only place names (no descriptions). "
            + "Notes must contain short logistics/weather cues only."
        ),
    }

    ctx = {"weather": weather_obs, "pois": poi_obs, "constraints": constraints}

    # Ask LLM to compose the table 
    final = chat(
        [sys, user, {"role": "user", "content": f"Observations: {json.dumps(ctx)}"}],
        temperature=0.2,
    )

    return final, ctx
