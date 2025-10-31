import argparse
import re
from rich.console import Console

from .config import settings
from .agents.router import route
from .agents.weather_agent import run as weather_run
from .agents.poi_agent import run as poi_run
from .agents.planner_agent import run as planner_run
from .io.input_handler import interactive_loop

console = Console()

#  Minimal helper & detection 

_HELP_TEXT = (
    "👋 Hey there! I can help you plan trips, find restaurants, or explore tourist spots.\n"
    "Try asking something like:\n\n"
    "best restaurants in Delhi\n\n"
    "plan a 3-day trip to Kashmir\n\n"
    "nature spots near Ooty\n"
)

_GREET_WORDS = ("hi", "hello", "hey", "yo", "sup", "thanks", "thank you", "ok", "okay")
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
    # greetings
    if any(w in _GREET_WORDS for w in words):
        # but allow travel queries even if they start with hello
        if any(h in t for h in _TRAVEL_HINTS):
            return False
        return True
    # very short messages 
    if len(words) <= 3 and not any(h in t for h in _TRAVEL_HINTS):
        return True
    return False


def main():
    parser = argparse.ArgumentParser(description="Multi-Agent Travel Planner")
    parser.add_argument("query", nargs="?", help="Natural language prompt (omit to enter interactive mode)")
    parser.add_argument(
        "--agent",
        choices=["auto", "weather", "poi", "plan"],
        default="auto",
        help="Force a specific agent"
    )
    parser.add_argument("--debug", action="store_true", help="Show internal JSON (observations/context)")
    parser.add_argument("--no-route-banner", action="store_true", help="Hide the 'Routed to: ...' banner")
    args = parser.parse_args()

    if not args.query:
        def _noop(*_a, **_kw):
            return None

        print_json = None
        if args.debug:
            import json
            def print_json(title, data):
                console.rule(title)
                console.print_json(json.dumps(data, ensure_ascii=False))

        interactive_loop(
            default_agent=args.agent,
            print_json=print_json if args.debug else _noop,
            show_route=not args.no_route_banner,
        )
        return

    user_input = args.query
    timezone = settings.app_tz

    def maybe_print_route(intent, city, start_date, end_date):
        if not args.no_route_banner:
            console.print(f"[bold]Routed to:[/bold] {intent} • city={city} • dates={start_date}→{end_date}")

    if args.agent == "auto":
        # short-circuit greetings
        if _is_chitchat(user_input):
            console.print(_HELP_TEXT)
            return

        r = route(user_input, timezone)

        # Fallback 
        if not r.get("intent") or r.get("intent") not in ["weather", "poi", "plan"]:
            console.print(_HELP_TEXT)
            return

        intent = r["intent"]
        city = r["city"] or "Delhi"
        maybe_print_route(intent, city, r["start_date"], r["end_date"])

        if intent == "weather":
            final, obs = weather_run(user_input, city, r["start_date"], r["end_date"])
            console.print(final)
            if args.debug:
                import json
                console.rule("Weather JSON")
                console.print_json(json.dumps(obs, ensure_ascii=False))

        elif intent == "poi":
            final, obs = poi_run(user_input, city, topic=r.get("poi_topic"))
            console.print(final)
            if args.debug:
                import json
                console.rule("POIs JSON")
                console.print_json(json.dumps(obs, ensure_ascii=False))

        else:  # plan
            final, ctx = planner_run(
                user_input,
                city,
                r["start_date"],
                r["end_date"],
                r["days"],
                budget_amount=r.get("budget_amount"),
                budget_currency=r.get("budget_currency"),
                budget_mode=r.get("budget_mode", False),
                poi_topic=r.get("poi_topic"),
            )
            console.print(final)
            if args.debug:
                import json
                console.rule("Planner Context JSON")
                console.print_json(json.dumps(ctx, ensure_ascii=False))

    elif args.agent == "weather":
        r = route(user_input, timezone)
        city = r["city"] or "Delhi"
        maybe_print_route("weather", city, r["start_date"], r["end_date"])
        final, obs = weather_run(user_input, city, r["start_date"], r["end_date"])
        console.print(final)
        if args.debug:
            import json
            console.rule("Weather JSON")
            console.print_json(json.dumps(obs, ensure_ascii=False))

    elif args.agent == "poi":
        r = route(user_input, timezone)
        city = r["city"] or "Delhi"
        maybe_print_route("poi", city, r["start_date"], r["end_date"])
        final, obs = poi_run(user_input, city, topic=r.get("poi_topic"))
        console.print(final)
        if args.debug:
            import json
            console.rule("POIs JSON")
            console.print_json(json.dumps(obs, ensure_ascii=False))

    else:  # plan
        r = route(user_input, timezone)
        city = r["city"] or "Delhi"
        maybe_print_route("plan", city, r["start_date"], r["end_date"])
        final, ctx = planner_run(
            user_input,
            city,
            r["start_date"],
            r["end_date"],
            r["days"],
            budget_amount=r.get("budget_amount"),
            budget_currency=r.get("budget_currency"),
            budget_mode=r.get("budget_mode", False),
            poi_topic=r.get("poi_topic"),
        )
        console.print(final)
        if args.debug:
            import json
            console.rule("Planner Context JSON")
            console.print_json(json.dumps(ctx, ensure_ascii=False))


if __name__ == "__main__":
    main()
