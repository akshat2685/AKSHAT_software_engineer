from __future__ import annotations

from typing import Any, Dict

from backend.agents.base import EngineeringAgent


class DevOpsAgent(EngineeringAgent):
    name = "DevOps"
    role = "devops"

    def determine_next_action(self, state: Any, objective: str) -> str:
        return "Generate CI/CD pipelines, Infrastructure-as-Code, and publish artifact."

    def select_tool(self, state: Any, action: str) -> tuple[str | None, Dict[str, Any]]:
        context = getattr(state, "agent_context", {}).get("DevOps", {})
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
        llm_response = super().update_state(state, objective, action, tool_result)
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
            state.final_deliverable = f"{llm_response}\n\nDeployed artifact: {state.artifact_name}\nDeploy URL: {state.deployment_url}\nReview URL: {state.artifact_url}"
            return state.final_deliverable

        state.deployment_status = "failed"
        state.final_deliverable = f"{llm_response}\n\nDeployment failed for {state.artifact_name or state.user_request}"
        return state.final_deliverable
