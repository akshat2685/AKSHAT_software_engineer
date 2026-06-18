from __future__ import annotations
from typing import Any, Dict
from backend.agents.base import EngineeringAgent

class DebugAgent(EngineeringAgent):
    name = "Debug"
    role = "debug"

    def determine_next_action(self, state: Any, objective: str) -> str:
        return "Analyze failed builds, logs, and stack traces. Determine root causes. Generate minimal fixes. Retry until success or escalation."

    def select_tool(self, state: Any, action: str) -> tuple[str | None, Dict[str, Any]]:
        return None, {}
