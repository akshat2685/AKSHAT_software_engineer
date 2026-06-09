from __future__ import annotations

from typing import Any, Dict

from backend.agents.base import EngineeringAgent


class ArchitectAgent(EngineeringAgent):
    name = "Architect"
    role = "architect"

    def prompt_for_model(self, state: Any, objective: str, action: str, tool_result: Dict[str, Any] | None) -> str:
        req_str = "- " + "\n- ".join(getattr(state, "requirements", ["No specific requirements"]))
        mem_ctx = getattr(state, "agent_context", {}).get(self.name, {}).get("memory_engine_context", "")
        return (
            f"You are the Architect.\n"
            f"Task: {state.user_request}\n"
            f"Requirements:\n{req_str}\n"
            f"{mem_ctx}\n"
            f"Return ONLY a JSON object with a single list of strings named 'architecture'.\n"
            f"Example format:\n"
            f'{{"architecture": ["FastAPI backend", "React frontend", "PostgreSQL database"]}}'
        )

    def update_state(self, state: Any, objective: str, action: str, tool_result: Dict[str, Any] | None) -> str:
        from backend.services.ollama_service import generate_response
        import json
        import re

        prompt = self.prompt_for_model(state, objective, action, tool_result)
        response = generate_response(self.role, prompt)

        state.architecture = [
            "Developer creates the browser artifact inside src/assets.",
            "Tester validates the build before publishing."
        ]

        try:
            match = re.search(r'\{.*\}', response.replace('\n', ' '), re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                if isinstance(data.get("architecture"), list) and data["architecture"]:
                    state.architecture = data["architecture"]
        except Exception:
            pass

        return "\n".join(f"- {a}" for a in state.architecture)
