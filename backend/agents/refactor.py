from __future__ import annotations
from typing import Any, Dict
from backend.agents.base import EngineeringAgent

class RefactorAgent(EngineeringAgent):
    name = "Refactor"
    role = "refactor"

    def determine_next_action(self, state: Any, objective: str) -> str:
        return "Improve readability, modularity, and performance. Reduce complexity and duplication. Preserve behavior."

    def select_tool(self, state: Any, action: str) -> tuple[str | None, Dict[str, Any]]:
        return None, {}
