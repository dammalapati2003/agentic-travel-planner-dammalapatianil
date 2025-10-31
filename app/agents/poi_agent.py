# app/agents/poi_agent.py
import re
from typing import Optional, Tuple, Dict, Any, List

from ..llm import chat
from ..prompts import react_agent
from ..tools import poi as poi_tool


# Common regex patterns
RESTAURANT_RE = re.compile(
    r"\b(rest(?:a|e)?ur(?:a|e)?n(?:t|ts)?|resto|dining|food\s+places|best\s+rest|top\s+rest)\b",
    re.IGNORECASE,
)
FOODS_RE = re.compile(
    r"\b(foods?\s+to\s+try|local\s+dishes|must[-\s]*try\s+foods?|what\s+to\s+eat|famous\s+foods?)\b",
    re.IGNORECASE,
)
NATURE_RE = re.compile(
    r"\b(nature|park(s)?|garden(s)?|lake(s)?|waterfall(s)?|beach(es)?|viewpoint(s)?|hiking|trail(s)?|valley|forest)\b",
    re.IGNORECASE,
)
GREET_RE = re.compile(
    r"\b(hi|hello|hey|good\s+(morning|afternoon|evening|night)|how\s+are\s+you|thank(s)?|what'?s\s+up|yo|sup)\b",
    re.IGNORECASE,
)

_ALLOWED_TOPICS = {"general", "restaurants", "foods", "nature"}


def _detect_topic(text: str) -> str:
    if FOODS_RE.search(text):
        return "foods"
    if RESTAURANT_RE.search(text):
        return "restaurants"
    if NATURE_RE.search(text):
        return "nature"
    return "general"


def _header_for_topic(topic: str) -> str:
    return "Food" if topic == "foods" else "Place"


def _format_names_table(names: List[str], topic: str) -> str:
    head = _header_for_topic(topic)
    lines = [f"| {head} |", "|---|"]
    if not names:
        lines.append("| _No live results found for this scope_ |")
        return "\n".join(lines)
    for n in names:
        lines.append(f"| {n} |")
    return "\n".join(lines)


def _names_from_items(items: List[Dict[str, Any]]) -> List[str]:
    names: List[str] = []
    seen = set()
    for it in items or []:
        name = (it.get("name") or "").strip()
        if name and name.lower() not in seen:
            seen.add(name.lower())
            names.append(name)
    return names


def _is_greeting(text: str) -> bool:
    """Detect if the input is a greeting or casual message"""
    return bool(GREET_RE.search(text.strip()))


def run(
    user_query: str,
    city: str,
    limit: int = 14,
    topic: Optional[str] = None,
    **_ignored_kwargs,
) -> Tuple[str, Dict[str, Any]]:
    """
    Live-first POI agent with greetings + fallback handling
    """
    #   Handle casual chat
    if _is_greeting(user_query):
        return (
            " Hey there! I can help you plan trips, find restaurants, or explore tourist spots. "
            "Try asking something like:\n"
            "- *best restaurants in Delhi*\n"
            "- *plan a 3-day trip to Kashmir*\n"
            "- *nature spots near Ooty*\n",
            {},
        )

    topic = (topic or "").lower().strip() if topic else None
    if topic not in _ALLOWED_TOPICS:
        topic = _detect_topic(user_query)

    # LLM + ReAct wrapper 
    system = {"role": "system", "content": react_agent.REACT_PROMPT}
    user = {
        "role": "user",
        "content": (
            "You will receive an observation with live POIs.\n"
            "Return ONLY a Markdown table of names (no descriptions)."
        ),
    }
    _ = chat([system, user], temperature=0.2)

    #  Live data
    try:
        if topic == "foods":
            obs = poi_tool.list_foods(city, limit=max(12, limit))
        else:
            obs = poi_tool.list_pois(city, limit=max(14, limit), topic=topic)
    except Exception as e:
        obs = {"city": city, "error": f"poi fetch failed: {e}", "items": []}

    items = obs.get("items", []) or []
    names = _names_from_items(items)

    #  Fallback via LLM
    if not names:
        prompt_topic_text = (
            "foods to try" if topic == "foods"
            else ("restaurants" if topic == "restaurants" else ("nature places" if topic == "nature" else "tourist attractions"))
        )
        proposal = chat(
            [
                {
                    "role": "system",
                    "content": "List strictly names only (no descriptions, no numbering). Output as Markdown table.",
                },
                {
                    "role": "user",
                    "content": f"Give top {prompt_topic_text} in {city}. Names only.",
                },
            ],
            temperature=0.2,
        )
        extracted = re.findall(r"\|\s*([^\|\n]+?)\s*\|", proposal)
        for n in extracted:
            n2 = n.strip()
            low = n2.lower()
            if n2 and low not in {"place", "food", "---"} and n2 not in names:
                names.append(n2)

    return _format_names_table(names, topic), obs
