from __future__ import annotations

from typing import Any, Dict

from backend.agents.base import EngineeringAgent


class ArchitectAgent(EngineeringAgent):
    name = "Architect"
    role = "architect"

    def determine_next_action(self, state: Any, objective: str) -> str:
        task_type = getattr(state, "task_type", "general")
        if task_type in {"website", "deploy"}:
            return "Design the artifact, deployment route, and review surfaces"
        if task_type == "research":
            return "Design the report structure and evidence trail"
        if task_type == "bug_fix":
            return "Design the minimal fix and validation loop"
        return "Design backend, database, agent graph, services, tools, and dashboard surfaces"

    def update_state(self, state: Any, objective: str, action: str, tool_result: Dict[str, Any] | None) -> str:
        task_type = getattr(state, "task_type", "general")
        if task_type in {"website", "deploy"}:
            state.architecture = [
                "Developer creates the browser artifact inside src/assets.",
                "Tester validates the build before publishing.",
                "Deploy publishes the artifact to a stable /deploy/<name> URL.",
                "Reviewer confirms the live preview and source remain aligned.",
            ]
        elif task_type == "research":
            state.architecture = [
                "Developer produces a readable review page with the answer and evidence.",
                "Reviewer checks clarity, safety, and answer quality.",
                "Memory stores the prompt-to-artifact history for reuse.",
            ]
        else:
            state.architecture = [
                "Backend agents are workers managed by a prompt-routed workflow.",
                "Tester branches to Reviewer on pass and Improver on fail.",
                "Ollama access is centralized through services/ollama_service.py.",
                "Database models track requirements, architecture, agent runs, tests, and replay events.",
                "Dashboard remains the primary project-owner interface.",
            ]
        return "\n".join(state.architecture)
