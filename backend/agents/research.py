from __future__ import annotations
from typing import Any, Dict
from backend.agents.base import EngineeringAgent

class ResearchAgent(EngineeringAgent):
    name = "Research"
    role = "research"

    def determine_next_action(self, state: Any, objective: str) -> str:
        return "Investigate technologies, patterns, or architecture decisions and produce an RFC."

    def select_tool(self, state: Any, action: str) -> tuple[str | None, Dict[str, Any]]:
        # The Research agent might just output text analysis, no specific tool required beyond the LLM string output
        return None, {}
