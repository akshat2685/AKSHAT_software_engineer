from __future__ import annotations
from typing import Any, Dict
from backend.agents.base import EngineeringAgent

class ComplianceAgent(EngineeringAgent):
    name = "Compliance"
    role = "compliance"

    def determine_next_action(self, state: Any, objective: str) -> str:
        return "Audit dependencies, verify GDPR and data handling, and validate accessibility."

    def select_tool(self, state: Any, action: str) -> tuple[str | None, Dict[str, Any]]:
        return None, {}
