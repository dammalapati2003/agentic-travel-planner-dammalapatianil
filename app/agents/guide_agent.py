from typing import Tuple, Dict, List
from ..tools import guide as guide_tool

def _names_table(names: List[str]) -> str:
    if not names:
        return "| Item |\n|---|\n| _No live results found_ |"
    lines = ["| Item |", "|---|"] + [f"| {n} |" for n in names]
    return "\n".join(lines)

def _tips_list(tips: List[str]) -> str:
    if not tips:
        return "- _No live results found_"
    tips = [f"- {t}" for t in tips[:12]]
    return "\n".join(tips)

def run_foods(city: str) -> Tuple[str, Dict]:
    obs = guide_tool.foods_to_try(city)
    names = [it["name"] for it in obs.get("items", []) if it.get("name")]
    return _names_table(names), obs

def run_budget(city: str) -> Tuple[str, Dict]:
    obs = guide_tool.budget_tips(city)
    tips = obs.get("items", [])
    return _tips_list(tips), obs
