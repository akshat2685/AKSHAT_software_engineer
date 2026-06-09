from __future__ import annotations
from typing import Any, Dict
from backend.agents.base import EngineeringAgent

class CostAgent(EngineeringAgent):
    name = "Cost"
    role = "cost"

    def determine_next_action(self, state: Any, objective: str) -> str:
        return "Audit LLM token usage, infrastructure costs, and propose efficiency optimizations."

    def select_tool(self, state: Any, action: str) -> tuple[str | None, Dict[str, Any]]:
        return None, {}
