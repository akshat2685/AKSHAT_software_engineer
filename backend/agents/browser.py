from __future__ import annotations
from typing import Any, Dict
from backend.agents.base import EngineeringAgent

class BrowserAgent(EngineeringAgent):
    name = "Browser Operator"
    role = "browser"

    def determine_next_action(self, state: Any, objective: str) -> str:
        return "Navigate, login, click, fill forms, extract data, and validate pages using Playwright."

    def select_tool(self, state: Any, action: str) -> tuple[str | None, Dict[str, Any]]:
        return None, {}
