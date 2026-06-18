from typing import Any, Dict
from backend.services.memory_engine import memory_engine

class ReflectionEngine:
    def trigger_reflection(self, task: str, result_state: Dict[str, Any]):
        print(f"[ReflectionEngine] Analyzing task: {task}")
        # Call LLM to analyze what worked, what failed, how to improve
        analysis = {
            "what_worked": "Correctly utilized the provided API.",
            "what_failed": "Missed some edge cases in validation.",
            "how_to_improve": "Add strict type checking for inputs."
        }
        
        # Ingest into memory
        memory_engine.ingest({
            "content": str(analysis),
            "type": "EPISODIC",
            "source_agent": "ReflectionSystem",
            "project_id": result_state.get("project_id", "default"),
            "outcome": "reflection"
        })
        return analysis

reflection_engine = ReflectionEngine()
