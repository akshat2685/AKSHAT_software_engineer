from __future__ import annotations

from typing import Any, Dict

from backend.agents.base import EngineeringAgent


class ReviewerAgent(EngineeringAgent):
    name = "Reviewer"
    role = "reviewer"

    def determine_next_action(self, state: Any, objective: str) -> str:
        if getattr(state, "deployment_url", ""):
            return "Review the deployed website and confirm readiness"
        return "Review implementation quality, security, and readiness"

    def update_state(self, state: Any, objective: str, action: str, tool_result: Dict[str, Any] | None) -> str:
        issues = []
        if tool_result:
            issues = [item for item in tool_result.get("issues", []) if item]
        if issues:
            report = "Review found issues: " + "; ".join(issues[:4])
        elif state.tests_passed or state.task_type == "research":
            report = "Implementation is ready for memory retention and project-owner dashboard reporting."
        else:
            report = "Review completed with validation concerns still open."
        state.review_reports.append(report)
        state.quality_score = 92 if state.tests_passed or state.task_type == "research" else 68
        state.security_score = 89 if state.tests_passed or state.task_type == "research" else 62
        return report
