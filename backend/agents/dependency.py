from __future__ import annotations
from typing import Any, Dict
from backend.agents.base import EngineeringAgent

class DependencyAgent(EngineeringAgent):
    name = "Dependency"
    role = "dependency"

    def determine_next_action(self, state: Any, objective: str) -> str:
        return "Manage package versions. Resolve dependency conflicts. Upgrade vulnerable libraries."

    def select_tool(self, state: Any, action: str) -> tuple[str | None, Dict[str, Any]]:
        return None, {}
