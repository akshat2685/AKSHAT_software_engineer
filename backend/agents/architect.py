from __future__ import annotations

from typing import Any, Dict

from backend.agents.base import EngineeringAgent


class ArchitectAgent(EngineeringAgent):
    name = "Architect"
    role = "architect"

    def determine_next_action(self, state: Any, objective: str) -> str:
        return "Design backend, database, agent graph, services, tools, and dashboard surfaces"

    def update_state(self, state: Any, objective: str, action: str, tool_result: Dict[str, Any] | None) -> str:
        state.architecture = [
            "Backend agents are workers managed by a workflow graph.",
            "Tester branches to Reviewer on pass and Improver on fail.",
            "Ollama access is centralized through services/ollama_service.py.",
            "Database models include projects, requirements, architectures, agent_runs, test_results, memory_entries, and replay_events.",
            "Dashboard remains the primary project-owner interface.",
        ]
        return "\n".join(state.architecture)
