from __future__ import annotations

from typing import Any, Dict

from backend.agents.base import EngineeringAgent


class MemoryAgent(EngineeringAgent):
    name = "Memory"
    role = "memory"

    def determine_next_action(self, state: Any, objective: str) -> str:
        return "Store replay-ready project learning"

    def update_state(self, state: Any, objective: str, action: str, tool_result: Dict[str, Any] | None) -> str:
        outcome = "passed" if getattr(state, "tests_passed", False) else "failed"
        result = f"Stored replay event for project {state.project_id} with outcome {outcome}."
        state.replay_events.append({"event_type": "workflow_complete", "payload": {"outcome": outcome}})
        state.final_result = state.final_deliverable
        return result
