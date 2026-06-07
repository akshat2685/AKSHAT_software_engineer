from __future__ import annotations

from typing import Any, Dict

from backend.agents.base import EngineeringAgent


class TesterAgent(EngineeringAgent):
    name = "Tester"
    role = "tester"

    def determine_next_action(self, state: Any, objective: str) -> str:
        return "Run validation and report pass or fail"

    def select_tool(self, state: Any, action: str) -> tuple[str | None, Dict[str, Any]]:
        return "run_tests", {"reason": "Tests gate Reviewer or Improver branch"}

    def update_state(self, state: Any, objective: str, action: str, tool_result: Dict[str, Any] | None) -> str:
        result = tool_result or {"success": False, "returncode": 1, "stderr": "No validation result"}
        state.test_results = result
        state.iteration_count += 1
        passed = bool(result.get("success")) or result.get("returncode") == 0
        state.tests_passed = passed
        return "Tests passed." if passed else f"Tests failed: {result.get('stderr') or result.get('summary') or 'unknown failure'}"
