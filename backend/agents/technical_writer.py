from __future__ import annotations
from typing import Any, Dict
from backend.agents.base import EngineeringAgent

class TechnicalWriterAgent(EngineeringAgent):
    name = "TechnicalWriter"
    role = "technical_writer"

    def determine_next_action(self, state: Any, objective: str) -> str:
        return "Author documentation, READMEs, API specs, and inline code comments."

    def select_tool(self, state: Any, action: str) -> tuple[str | None, Dict[str, Any]]:
        return None, {}
