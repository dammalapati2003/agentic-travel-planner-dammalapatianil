from pathlib import Path

SYSTEMS = Path(__file__).parent

class router_system:
    SYSTEM_PROMPT = (SYSTEMS / "router_system.md").read_text(encoding="utf-8")

class react_agent:
    REACT_PROMPT = (SYSTEMS / "react_agent.md").read_text(encoding="utf-8")

class planner_system:
    SYSTEM_PROMPT = (SYSTEMS / "planner_system.md").read_text(encoding="utf-8")
