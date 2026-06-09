from __future__ import annotations
from typing import Any, Dict
from backend.agents.base import EngineeringAgent

class SecurityAgent(EngineeringAgent):
    name = "Security"
    role = "security"

    def determine_next_action(self, state: Any, objective: str) -> str:
        return "Perform SAST, DAST, SCA, and secrets scanning on all code artifacts."

    def select_tool(self, state: Any, action: str) -> tuple[str | None, Dict[str, Any]]:
        return None, {}
