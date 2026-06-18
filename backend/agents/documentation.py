from __future__ import annotations
from typing import Any, Dict
from backend.agents.base import EngineeringAgent

class DocumentationAgent(EngineeringAgent):
    name = "Documentation"
    role = "documentation"

    def determine_next_action(self, state: Any, objective: str) -> str:
        return "Generate README files, architecture diagrams, API docs, and changelogs."

    def select_tool(self, state: Any, action: str) -> tuple[str | None, Dict[str, Any]]:
        return None, {}
