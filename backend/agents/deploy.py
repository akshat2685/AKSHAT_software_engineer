from __future__ import annotations

from typing import Any, Dict

from backend.agents.base import EngineeringAgent


class DeployAgent(EngineeringAgent):
    name = "Deploy"
    role = "deploy"

    def determine_next_action(self, state: Any, objective: str) -> str:
        return "Publish the validated artifact to a stable local deployment URL"

    def select_tool(self, state: Any, action: str) -> tuple[str | None, Dict[str, Any]]:
        context = getattr(state, "agent_context", {}).get("Deploy", {})
        return "deploy_artifact", {
            "artifact_name": context.get("artifact_name", getattr(state, "artifact_name", "")),
            "artifact_version": context.get("artifact_version", getattr(state, "artifact_version", "")),
            "artifact_path": getattr(state, "artifact_path", ""),
            "review_url": context.get("review_url", getattr(state, "artifact_url", "")),
            "deploy_url": context.get("deploy_url", getattr(state, "deployment_url", "")),
            "output_url": context.get("output_url", getattr(state, "artifact_output_url", "")),
            "reason": "Website and deploy prompts must return a stable, reviewable live URL.",
        }

    def update_state(self, state: Any, objective: str, action: str, tool_result: Dict[str, Any] | None) -> str:
        result = tool_result or {"success": False, "message": "Deployment failed"}
        if result.get("success"):
            state.deployment_status = "published"
            state.deployment_url = str(result.get("deploy_url") or result.get("url") or "")
            state.artifact_url = str(result.get("review_url") or state.artifact_url)
            state.artifact_output_url = str(result.get("output_url") or state.artifact_output_url)
            state.artifact_version = str(result.get("version", state.artifact_version))
            if state.artifact_history:
                state.artifact_history[-1]["deployment_url"] = state.deployment_url
                state.artifact_history[-1]["deploy_url"] = state.deployment_url
                state.artifact_history[-1]["output_url"] = state.artifact_output_url
            state.final_deliverable = (
                f"Deployed artifact: {state.artifact_name}\n"
                f"Deploy URL: {state.deployment_url}\n"
                f"Review URL: {state.artifact_url}"
            )
            return f"Deployment published at {state.deployment_url}"

        state.deployment_status = "failed"
        state.final_deliverable = f"Deployment failed for {state.artifact_name or state.user_request}"
        return state.final_deliverable
