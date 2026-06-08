from __future__ import annotations

import json
import queue
import sqlite3
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def stamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


def slug(text: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in text).strip("-")


def json_preview(raw: str, limit: int = 2000) -> Dict[str, Any]:
    if len(raw) <= limit:
        try:
            value = json.loads(raw)
            return value if isinstance(value, dict) else {"value": value}
        except Exception:
            return {"preview": raw, "truncated": False}
    return {"preview": raw[:limit], "size": len(raw), "truncated": True}


@dataclass
class Event:
    ts: str
    kind: str
    message: str
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskState:
    task_id: str = "idle"
    prompt: str = ""
    status: str = "idle"
    avatar_state: str = "Idle"
    current_action: str = "Waiting for task"
    task_type: str = "general"
    prompt_analysis: Dict[str, Any] = field(default_factory=dict)
    selected_agents: List[str] = field(default_factory=list)
    execution_order: List[str] = field(default_factory=list)
    plan: List[str] = field(default_factory=list)
    todo_list: List[str] = field(default_factory=list)
    steps_done: List[str] = field(default_factory=list)
    workflow: Dict[str, Any] = field(default_factory=dict)
    current_agent: str = "Idle"
    quality_score: int = 0
    security_score: int = 0
    iteration_count: int = 0
    build_results: Dict[str, Any] = field(default_factory=dict)
    artifact_url: str = ""
    artifact_output_url: str = ""
    artifact_path: str = ""
    artifact_name: str = ""
    artifact_version: str = ""
    project_path: str = ""
    entry_file: str = ""
    entry_url: str = ""
    created_files: List[str] = field(default_factory=list)
    deployment_url: str = ""
    deployment_status: str = "pending"
    artifact_history: List[Dict[str, Any]] = field(default_factory=list)
    final_deliverable: str = ""
    final_result: str = ""
    structured_result: Dict[str, Any] = field(default_factory=dict)
    execution_trace: List[Dict[str, Any]] = field(default_factory=list)
    chat: List[Dict[str, str]] = field(default_factory=list)
    tests: Dict[str, Any] = field(default_factory=lambda: {"passed": 0, "failed": 0, "summary": "Not run"})
    browser: Dict[str, Any] = field(default_factory=lambda: {"url": "", "screenshot": "", "notes": ""})
    repo: Dict[str, Any] = field(default_factory=dict)
    git: Dict[str, Any] = field(default_factory=dict)
    agent_context: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    memory_hits: List[str] = field(default_factory=list)
    habits: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)


class EventBus:
    def __init__(self) -> None:
        self.clients: List[queue.Queue[str]] = []
        self.lock = threading.Lock()

    def subscribe(self) -> queue.Queue[str]:
        client: queue.Queue[str] = queue.Queue()
        with self.lock:
            self.clients.append(client)
        return client

    def unsubscribe(self, client: queue.Queue[str]) -> None:
        with self.lock:
            if client in self.clients:
                self.clients.remove(client)

    def publish(self, event: Event) -> None:
        payload = json.dumps(asdict(event), ensure_ascii=False)
        with self.lock:
            clients = list(self.clients)
        for client in clients:
            client.put(payload)


class MemoryStore:
    def __init__(self, path: Path):
        from backend.database.connection import init_db, SessionLocal
        init_db()
        self.SessionLocal = SessionLocal

    def add(self, kind: str, prompt: str, summary: str, payload: Dict[str, Any]) -> None:
        from backend.database.models import Memory
        db = self.SessionLocal()
        try:
            outcome = payload.get("outcome", "")
            if not outcome and isinstance(payload, dict):
                outcome = json.dumps(payload)
            entry = Memory(problem=prompt, solution=summary, outcome=outcome, tags=kind)
            db.add(entry)
            db.commit()
        finally:
            db.close()

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        from backend.database.models import Memory
        db = self.SessionLocal()
        try:
            q = f"%{query.lower()}%"
            rows = db.query(Memory).filter(
                (Memory.problem.ilike(q)) | (Memory.solution.ilike(q)) | (Memory.outcome.ilike(q))
            ).order_by(Memory.id.desc()).limit(limit).all()
            return [
                {
                    "created_at": row.created_at.isoformat(),
                    "kind": row.tags,
                    "prompt": row.problem,
                    "summary": row.solution,
                    "payload": {"outcome": row.outcome},
                }
                for row in rows
            ]
        finally:
            db.close()

    def recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        from backend.database.models import Memory
        db = self.SessionLocal()
        try:
            rows = db.query(Memory).order_by(Memory.id.desc()).limit(limit).all()
            return [
                {
                    "created_at": row.created_at.isoformat(),
                    "kind": row.tags,
                    "prompt": row.problem,
                    "summary": row.solution,
                    "payload": {"outcome": row.outcome},
                }
                for row in rows
            ]
        finally:
            db.close()

    def add_habit(self, kind: str, pattern: str, confidence: float, evidence: Dict[str, Any]) -> None:
        # Habits are mapped to Memory with tags="habit"
        self.add("habit", pattern, f"Confidence: {confidence}", {"kind": kind, "evidence": evidence})

    def recent_habits(self, limit: int = 20) -> List[Dict[str, Any]]:
        from backend.database.models import Memory
        db = self.SessionLocal()
        try:
            rows = db.query(Memory).filter(Memory.tags == "habit").order_by(Memory.id.desc()).limit(limit).all()
            return [
                {
                    "created_at": row.created_at.isoformat(),
                    "kind": "habit",
                    "pattern": row.problem,
                    "confidence": 0.9, # fallback
                    "evidence": {"outcome": row.outcome},
                }
                for row in rows
            ]
        finally:
            db.close()

    def add_tool_log(self, agent_name: str, tool_name: str, reason: str, parameters: Dict[str, Any], result: Dict[str, Any]) -> None:
        from backend.database.models import AgentRun
        db = self.SessionLocal()
        try:
            # Look up or mock active project ID
            project_id = parameters.get("project_id", "idle")
            run = AgentRun(
                project_id=project_id,
                agent=agent_name,
                action=f"{tool_name}: {reason}",
                result=json.dumps(result)
            )
            run.set_payload(parameters)
            db.add(run)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

    def recent_tool_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        from backend.database.models import AgentRun
        db = self.SessionLocal()
        try:
            rows = db.query(AgentRun).order_by(AgentRun.id.desc()).limit(limit).all()
            return [
                {
                    "created_at": row.created_at.isoformat(),
                    "agent_name": row.agent,
                    "tool_name": row.action.split(":")[0] if ":" in row.action else row.action,
                    "reason": row.action.split(":", 1)[1].strip() if ":" in row.action else "",
                    "parameters": json_preview(row.payload, 2000),
                    "result": json_preview(row.result, 1000),
                }
                for row in rows
            ]
        finally:
            db.close()
