from __future__ import annotations

from typing import Any, Dict

from backend.agents.base import EngineeringAgent


class DeveloperAgent(EngineeringAgent):
    name = "Developer"
    role = "developer"

    def determine_next_action(self, state: Any, objective: str) -> str:
        if getattr(state, "task_type", "") in {"website", "deploy"}:
            return "Build and stage a browser-viewable website artifact"
        if getattr(state, "task_type", "") == "research":
            return "Build a readable review artifact that captures the analysis"
        return "Build browser-viewable output artifact in the running application"

    def select_tool(self, state: Any, action: str) -> tuple[str | None, Dict[str, Any]]:
        context = getattr(state, "agent_context", {}).get("Developer", {})
        return "build_artifact", {
            "prompt": state.user_request,
            "artifact_name": context.get("artifact_name", getattr(state, "artifact_name", "")),
            "artifact_version": context.get("artifact_version", getattr(state, "artifact_version", "")),
            "task_type": context.get("task_type", getattr(state, "task_type", "")),
            "requirements": getattr(state, "requirements", []),
            "architecture": getattr(state, "architecture", []),
            "reason": "Every user prompt must produce a reviewable browser artifact.",
        }

    def update_state(self, state: Any, objective: str, action: str, tool_result: Dict[str, Any] | None) -> str:
        if tool_result and tool_result.get("success") and tool_result.get("url"):
            artifact = {
                "name": tool_result.get("name", getattr(state, "artifact_name", "")),
                "version": tool_result.get("version", getattr(state, "artifact_version", "")),
                "path": tool_result.get("path", ""),
                "review_url": tool_result.get("url", ""),
                "output_url": tool_result.get("output_url", ""),
                "deploy_url": tool_result.get("deploy_url", ""),
                "project_path": tool_result.get("project_path", ""),
                "entry_file": tool_result.get("entry_file", ""),
                "entry_url": tool_result.get("entry_url", ""),
                "created_files": list(tool_result.get("created_files", [])),
            }
            state.artifact_history.append(artifact)
            state.artifact_url = str(tool_result.get("url", ""))
            state.artifact_output_url = str(tool_result.get("output_url", ""))
            state.artifact_path = str(tool_result.get("path", ""))
            state.artifact_name = str(tool_result.get("name", getattr(state, "artifact_name", "")))
            state.artifact_version = str(tool_result.get("version", getattr(state, "artifact_version", "")))
            state.project_path = str(tool_result.get("project_path", ""))
            state.entry_file = str(tool_result.get("entry_file", ""))
            state.entry_url = str(tool_result.get("entry_url", ""))
            state.created_files = list(tool_result.get("created_files", []))
            created = "\n".join(f"- {path}" for path in state.created_files) or f"- {tool_result.get('path')}"
            deliverable = (
                f"Built browser artifact for: {state.user_request}\n"
                f"Path: {tool_result.get('path')}\n"
                f"URL: {tool_result.get('deploy_url') or tool_result.get('url')}\n"
                f"Files created:\n{created}"
            )
            state.generated_code = deliverable
            state.final_deliverable = deliverable
            state.final_result = deliverable
            return deliverable
        deliverable = (
            f"AKSHAT is executing: {state.user_request}\n\n"
            "Implementation plan:\n"
            + "\n".join(f"- {task}" for task in state.tasks)
            + "\n\nArchitecture:\n"
            + "\n".join(f"- {item}" for item in state.architecture)
        )
        state.generated_code = deliverable
        state.final_deliverable = deliverable
        return deliverable
