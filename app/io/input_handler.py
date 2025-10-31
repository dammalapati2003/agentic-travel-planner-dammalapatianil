# app/io/input_handler.py
import re
from rich.console import Console
from ..agents.router import route
from ..agents.weather_agent import run as weather_run
from ..agents.poi_agent import run as poi_run
from ..agents.planner_agent import run as planner_run

console = Console()

_HELP_TEXT = (
    " Hey there! I can help you plan trips, find restaurants, or explore tourist spots.\n"
    "Try asking something like:\n\n"
    "best restaurants in Delhi\n\n"
    "plan a 3-day trip to Kashmir\n\n"
    "nature spots near Ooty\n"
)

_GREET_WORDS = {"hi", "hello", "hey", "yo", "sup", "thanks", "thank", "thank you", "ok", "okay"}
_TRAVEL_HINTS = (
    "plan", "trip", "itinerary", "travel", "tour", "stay", "hotel", "flight", "train", "bus",
    "weather", "rain", "temperature", "attraction", "attractions", "restaurant", "food",
    "nature", "places", "place", "poi"
)

def _is_chitchat(text: str) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return True
    words = re.findall(r"[a-zA-Z]+", t)
    if any(w in _GREET_WORDS for w in words):
        # allow genuine travel queries that happen to include a greeting
        if any(h in t for h in _TRAVEL_HINTS):
            return False
        return True
    if len(words) <= 3 and not any(h in t for h in _TRAVEL_HINTS):
        return True
    return False


def interactive_loop(default_agent: str, print_json, show_route: bool):
    """
    Simple REPL for interactive usage. Minimal chitchat handling:
    - If user input is greeting/random, print helper and continue.
    - If router returns no/invalid intent, print helper and continue.
    """
    while True:
        try:
            user_input = console.input("[bold] You:[/bold] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n Bye!")
            return

        if not user_input:
            continue

        # 🔹 Short-circuit greetings 
        if _is_chitchat(user_input):
            console.print(_HELP_TEXT)
            continue

        # Route the request
        from ..config import settings
        r = route(user_input, settings.app_tz)

        # 🔹 If router couldn't confidently pick an agent, show helper
        if not r.get("intent") or r.get("intent") not in ["weather", "poi", "plan"]:
            console.print(_HELP_TEXT)
            continue

        intent = r["intent"]
        city = r.get("city") or "Delhi"
        start_date = r.get("start_date")
        end_date = r.get("end_date")

        # Only show the banner if dates are resolved and user wants it
        if show_route:
            console.print(
                f"[dim]Routed to: {intent} • city={city} • dates={start_date}→{end_date}[/dim]"
            )

        # Execute agent
        if intent == "weather":
            final, obs = weather_run(user_input, city, start_date, end_date)
            console.print(final)
            print_json and print_json("Weather JSON", obs or {})

        elif intent == "poi":
            final, obs = poi_run(user_input, city, topic=r.get("poi_topic"))
            console.print(final)
            print_json and print_json("POIs JSON", obs or {})

        else:  
            final, ctx = planner_run(
                user_input,
                city,
                start_date,
                end_date,
                r.get("days", 2),
                budget_amount=r.get("budget_amount"),
                budget_currency=r.get("budget_currency"),
                budget_mode=r.get("budget_mode", False),
                poi_topic=r.get("poi_topic"),
            )
            console.print(final)
            print_json and print_json("Planner Context JSON", ctx or {})
