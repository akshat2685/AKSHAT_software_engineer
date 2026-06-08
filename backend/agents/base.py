from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List

from backend.services.ollama_service import generate_response


Emit = Callable[[str, str, Dict[str, Any]], None]
ToolRunner = Callable[[str, Dict[str, Any]], Dict[str, Any]]
ROOT = Path(__file__).resolve().parents[2]


@dataclass
class AgentResult:
    action: str
    result: str
    tool_result: Dict[str, Any] | None = None


class EngineeringAgent:
    name = "Agent"
    role = "agent"

    def __init__(self, tool_runner: ToolRunner):
        self.tool_runner = tool_runner

    def run(self, state: Any, emit: Emit) -> AgentResult:
        command = self.private_command()
        if command and hasattr(state, "agent_commands"):
            state.agent_commands[self.name] = command
        memory = self.retrieve_memory(state)
        objective = self.determine_objective(state, memory)
        action = self.determine_next_action(state, objective)
        tool_name, tool_args = self.select_tool(state, action)
        tool_result = self.execute_tool(tool_name, tool_args) if tool_name else None
        result = self.update_state(state, objective, action, tool_result)
        self.log_action(state, action, result, tool_result)
        emit(self.role, f"{self.name}: {action}", {"agent": self.name, "result": result, "tool_result": tool_result or {}})
        return AgentResult(action=action, result=result, tool_result=tool_result)

    def retrieve_memory(self, state: Any) -> List[str]:
        return list(getattr(state, "memory_context", []) or [])

    def determine_objective(self, state: Any, memory: List[str]) -> str:
        return f"Complete project task: {state.user_request}"

    def determine_next_action(self, state: Any, objective: str) -> str:
        return objective

    def select_tool(self, state: Any, action: str) -> tuple[str | None, Dict[str, Any]]:
        return None, {}

    def execute_tool(self, tool_name: str | None, tool_args: Dict[str, Any]) -> Dict[str, Any] | None:
        if not tool_name:
            return None
        payload = {"agent_name": self.name, "reason": tool_args.pop("reason", f"{self.name} selected {tool_name}"), **tool_args}
        return self.tool_runner(tool_name, payload)

    def update_state(self, state: Any, objective: str, action: str, tool_result: Dict[str, Any] | None) -> str:
        response = generate_response(self.role, self.prompt_for_model(state, objective, action, tool_result))
        return response or action

    def prompt_for_model(self, state: Any, objective: str, action: str, tool_result: Dict[str, Any] | None) -> str:
        command = self.private_command()
        command_block = f"\nPrivate command file:\n{command}\n" if command else ""
        context = getattr(state, "agent_context", {}).get(self.name, {})
        context_block = f"\nContext:\n{context}\n" if context else ""
        return (
            f"Role: {self.name}\n"
            f"Project: {state.project_id}\n"
            f"Task: {state.user_request}\n"
            f"Task type: {getattr(state, 'task_type', 'general')}\n"
            f"Objective: {objective}\n"
            f"Action: {action}\n"
            f"{command_block}"
            f"{context_block}"
            "Return concise worker output for the dashboard. Do not chat with the user."
        )

    def log_action(self, state: Any, action: str, result: str, tool_result: Dict[str, Any] | None) -> None:
        state.record(self.name, action, result, {"tool_result": tool_result or {}})

    def private_command(self) -> str:
        path = ROOT / "config" / "agents" / f"{self.role}.prompt"
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8").strip()
