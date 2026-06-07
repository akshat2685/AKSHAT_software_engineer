from __future__ import annotations

from typing import Any, Dict

from backend.agents.base import EngineeringAgent


class ProjectManagerAgent(EngineeringAgent):
    name = "ProjectManager"
    role = "project_manager"

    def determine_next_action(self, state: Any, objective: str) -> str:
        return "Extract requirements and define execution tasks"

    def update_state(self, state: Any, objective: str, action: str, tool_result: Dict[str, Any] | None) -> str:
        state.requirements = [
            state.user_request,
            "Execute autonomously through dashboard-visible worker agents.",
            "Do not behave as a chatbot or ask conversational follow-up during execution.",
        ]
        state.tasks = [
            "Read workflow state",
            "Read available memory",
            "Design implementation",
            "Generate or modify code",
            "Run validation",
            "Review quality and risks",
            "Store learning for replay",
        ]
        return "Requirements captured for autonomous execution.\n" + "\n".join(state.tasks)
