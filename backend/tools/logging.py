from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict


def action_log(agent_name: str, action: str, result: str) -> Dict[str, Any]:
    return {
        "agent_name": agent_name,
        "action": action,
        "result": result,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
