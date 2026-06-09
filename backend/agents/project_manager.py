from __future__ import annotations

from typing import Any, Dict

from backend.agents.base import EngineeringAgent


class ProjectManagerAgent(EngineeringAgent):
    name = "ProjectManager"
    role = "project_manager"

    def prompt_for_model(self, state: Any, objective: str, action: str, tool_result: Dict[str, Any] | None) -> str:
        mem_ctx = getattr(state, "agent_context", {}).get(self.name, {}).get("memory_engine_context", "")
        return (
            f"You are the Project Manager.\n"
            f"Analyze this user request deeply: {state.user_request}\n"
            f"{mem_ctx}\n"
            f"Return ONLY a JSON object with two lists of strings: 'requirements' and 'tasks'.\n"
            f"Example format:\n"
            f'{{"requirements": ["Must be a responsive portfolio", "Needs drag and drop functionality"], "tasks": ["Setup layout", "Implement drag and drop", "Style components"]}}'
        )

    def update_state(self, state: Any, objective: str, action: str, tool_result: Dict[str, Any] | None) -> str:
        from backend.services.ollama_service import generate_response
        import json
        import re

        prompt = self.prompt_for_model(state, objective, action, tool_result)
        response = generate_response(self.role, prompt)

        # Set fallbacks in case parsing fails
        state.requirements = [state.user_request, "Autonomously execute tasks."]
        state.tasks = ["Plan", "Design", "Implement", "Review"]

        try:
            # Look for JSON block
            match = re.search(r'\{.*\}', response.replace('\n', ' '), re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                if isinstance(data.get("requirements"), list) and data["requirements"]:
                    state.requirements = data["requirements"]
                if isinstance(data.get("tasks"), list) and data["tasks"]:
                    state.tasks = data["tasks"]
        except Exception:
            pass

        return "Requirements captured for autonomous execution:\n" + "\n".join(f"- {t}" for t in state.tasks)
