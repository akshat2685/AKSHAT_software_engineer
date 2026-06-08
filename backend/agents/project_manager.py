from __future__ import annotations

from typing import Any, Dict

from backend.agents.base import EngineeringAgent


class ProjectManagerAgent(EngineeringAgent):
    name = "ProjectManager"
    role = "project_manager"

    def determine_next_action(self, state: Any, objective: str) -> str:
        return "Extract requirements and define execution tasks"

    def update_state(self, state: Any, objective: str, action: str, tool_result: Dict[str, Any] | None) -> str:
        task_type = getattr(state, "task_type", "general")
        state.requirements = [
            state.user_request,
            "Execute autonomously through dashboard-visible worker agents.",
            "Do not behave as a chatbot or ask conversational follow-up during execution.",
        ]
        if task_type == "research":
            state.tasks = [
                "Summarize the request",
                "Generate a readable answer artifact",
                "Review the response for clarity and accuracy",
                "Store the research outcome for reuse",
            ]
        elif task_type in {"website", "deploy"}:
            state.tasks = [
                "Read workflow state",
                "Design the browser artifact",
                "Generate or modify the website output",
                "Validate the build",
                "Publish the local deployment URL",
                "Review the deployment for readiness",
                "Store learning for replay",
            ]
        elif task_type == "bug_fix":
            state.tasks = [
                "Read workflow state",
                "Inspect failure details",
                "Generate the minimal fix",
                "Re-run validation",
                "Review the corrected output",
                "Store learning for replay",
            ]
        else:
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
