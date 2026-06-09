from __future__ import annotations

from typing import Any, Dict

from backend.agents.base import EngineeringAgent


class ToolsIntegrationAgent(EngineeringAgent):
    name = "ToolsEngine"
    role = "tools_integration"

    def determine_next_action(self, state: Any, objective: str) -> str:
        return "Validate and execute requested tool safely"

    def update_state(self, state: Any, objective: str, action: str, tool_result: Dict[str, Any] | None) -> str:
        report = "Tool execution completed."
        if tool_result:
            if not tool_result.get("success", True):
                report = f"Tool execution failed: {tool_result.get('error', 'unknown')}"
            else:
                report = f"Tool executed successfully. Output summary: {tool_result.get('output_summary', 'None')}"
        return report
