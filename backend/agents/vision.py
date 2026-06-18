from __future__ import annotations
from typing import Any, Dict
from backend.agents.base import EngineeringAgent

class VisionAgent(EngineeringAgent):
    name = "Vision Intelligence"
    role = "vision"

    def determine_next_action(self, state: Any, objective: str) -> str:
        return "Analyze screenshots and UI layouts. Detect broken components, alignment issues, responsiveness problems, and dark mode defects."

    def select_tool(self, state: Any, action: str) -> tuple[str | None, Dict[str, Any]]:
        return None, {}
