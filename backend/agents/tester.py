from __future__ import annotations

from typing import Any, Dict

from backend.agents.base import EngineeringAgent


class TesterAgent(EngineeringAgent):
    name = "Tester"
    role = "tester"

    def determine_next_action(self, state: Any, objective: str) -> str:
        if getattr(state, "task_type", "") in {"website", "deploy"}:
            return "Run build validation for the staged website artifact"
        return "Run validation and report pass or fail"

    def select_tool(self, state: Any, action: str) -> tuple[str | None, Dict[str, Any]]:
        if getattr(state, "task_type", "") in {"website", "deploy"}:
            return "validate_artifact", {
                "artifact_path": getattr(state, "artifact_path", ""),
                "created_files": list(getattr(state, "created_files", []) or []),
                "reason": "Website and deploy prompts need generated file validation before publish",
            }
        return "run_tests", {"reason": "Tests gate Reviewer or Improver branch"}

    def update_state(self, state: Any, objective: str, action: str, tool_result: Dict[str, Any] | None) -> str:
        result = tool_result or {"success": False, "returncode": 1, "stderr": "No validation result"}
        state.test_results = result
        if getattr(state, "task_type", "") in {"website", "deploy"}:
            state.build_results = result
        state.iteration_count += 1
        passed = bool(result.get("success")) or result.get("returncode") == 0
        state.tests_passed = passed
        return "Tests passed." if passed else f"Tests failed: {result.get('stderr') or result.get('summary') or 'unknown failure'}"
