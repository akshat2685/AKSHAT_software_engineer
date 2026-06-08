from __future__ import annotations

from typing import Any, Dict

from backend.agents.base import EngineeringAgent


class ImproverAgent(EngineeringAgent):
    name = "Improver"
    role = "improver"

    def determine_next_action(self, state: Any, objective: str) -> str:
        return "Analyze failed validation output and prepare the smallest corrective retry"

    def update_state(self, state: Any, objective: str, action: str, tool_result: Dict[str, Any] | None) -> str:
        failure = state.test_results.get("stderr") or state.test_results.get("summary") or "Validation failed"
        fix = f"Failure analyzed and queued for retry: {failure[:300]}"
        state.fix_history.append(fix)
        return fix
