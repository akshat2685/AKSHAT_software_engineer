from __future__ import annotations

from typing import Any, Dict

from backend.agents.base import EngineeringAgent


class DeveloperAgent(EngineeringAgent):
    name = "Developer"
    role = "developer"

    def determine_next_action(self, state: Any, objective: str) -> str:
        return "Prepare implementation deliverable for the requested software task"

    def update_state(self, state: Any, objective: str, action: str, tool_result: Dict[str, Any] | None) -> str:
        deliverable = (
            f"AKSHAT is executing: {state.user_request}\n\n"
            "Implementation plan:\n"
            + "\n".join(f"- {task}" for task in state.tasks)
            + "\n\nArchitecture:\n"
            + "\n".join(f"- {item}" for item in state.architecture)
        )
        state.generated_code = deliverable
        state.final_deliverable = deliverable
        return deliverable
