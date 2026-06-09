from __future__ import annotations
from typing import Any, Dict
from backend.agents.base import EngineeringAgent

class PerformanceAgent(EngineeringAgent):
    name = "Performance"
    role = "performance"

    def determine_next_action(self, state: Any, objective: str) -> str:
        return "Profile application code, load test bottlenecks, and recommend optimizations."

    def select_tool(self, state: Any, action: str) -> tuple[str | None, Dict[str, Any]]:
        return None, {}
