from __future__ import annotations

from typing import Any, Callable, Dict


ToolRunner = Callable[[str, Dict[str, Any]], Dict[str, Any]]


def run_validation(tool_runner: ToolRunner, agent_name: str) -> Dict[str, Any]:
    return tool_runner(
        "run_tests",
        {
            "agent_name": agent_name,
            "reason": "Validate autonomous engineering workflow before review",
        },
    )
