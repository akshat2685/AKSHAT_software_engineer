from __future__ import annotations

from dataclasses import dataclass


POSTGRESQL_TABLES = {
    "projects": "id, name, status, created_at",
    "requirements": "id, project_id, content",
    "architectures": "id, project_id, content",
    "agent_runs": "id, project_id, agent_name, action, result, timestamp",
    "test_results": "id, project_id, passed, failed, coverage",
    "memory_entries": "id, problem, solution, outcome, embedding",
    "replay_events": "id, project_id, event_type, payload, timestamp",
}


@dataclass(frozen=True)
class ProjectRecord:
    id: str
    name: str
    status: str
    created_at: str
