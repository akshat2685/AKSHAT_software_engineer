import time
from typing import Dict, Any, List

class ObservabilityEngine:
    def __init__(self):
        self.metrics: List[Dict[str, Any]] = []

    def record_agent_execution(self, agent_name: str, duration_ms: float, tokens_used: int, success: bool):
        self.metrics.append({
            "timestamp": time.time(),
            "event": "agent_execution",
            "agent": agent_name,
            "duration_ms": duration_ms,
            "tokens_used": tokens_used,
            "success": success
        })

    def get_metrics(self) -> List[Dict[str, Any]]:
        return self.metrics

observability_engine = ObservabilityEngine()
