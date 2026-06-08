from __future__ import annotations

from typing import Any, Dict

from backend.agents.base import EngineeringAgent


class MemoryAgent(EngineeringAgent):
    name = "Memory"
    role = "memory"

    def determine_next_action(self, state: Any, objective: str) -> str:
        return "Store replay-ready project learning and structured completion data"

    def update_state(self, state: Any, objective: str, action: str, tool_result: Dict[str, Any] | None) -> str:
        outcome = "passed" if getattr(state, "tests_passed", False) else "failed"
        result = f"Stored replay event for project {state.project_id} with outcome {outcome}."
        state.replay_events.append(
            {
                "event_type": "workflow_complete",
                "timestamp": state.agent_runs[-1]["timestamp"] if state.agent_runs else "",
                "payload": {
                    "outcome": outcome,
                    "task_type": getattr(state, "task_type", "general"),
                    "artifact_name": getattr(state, "artifact_name", ""),
                    "deployment_url": getattr(state, "deployment_url", ""),
                },
            }
        )
        state.final_result = state.final_deliverable
        return result
