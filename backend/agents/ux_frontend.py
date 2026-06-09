from __future__ import annotations
from typing import Any, Dict
from backend.agents.base import EngineeringAgent

class UXFrontendAgent(EngineeringAgent):
    name = "UXFrontend"
    role = "ux_frontend"

    def determine_next_action(self, state: Any, objective: str) -> str:
        return "Design interface layouts, component hierarchy, accessibility checklists, and design tokens."

    def select_tool(self, state: Any, action: str) -> tuple[str | None, Dict[str, Any]]:
        return None, {}
