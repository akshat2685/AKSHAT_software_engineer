from __future__ import annotations
from typing import Any, Dict
from backend.agents.base import EngineeringAgent

class DataEngineerAgent(EngineeringAgent):
    name = "DataEngineer"
    role = "data_engineer"

    def determine_next_action(self, state: Any, objective: str) -> str:
        return "Design database schemas, migration scripts, and data pipelines."

    def select_tool(self, state: Any, action: str) -> tuple[str | None, Dict[str, Any]]:
        return None, {}
