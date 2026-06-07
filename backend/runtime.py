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
    plan: List[str] = field(default_factory=list)
    todo_list: List[str] = field(default_factory=list)
    steps_done: List[str] = field(default_factory=list)
    workflow: Dict[str, Any] = field(default_factory=dict)
    current_agent: str = "Idle"
    quality_score: int = 0
    security_score: int = 0
    iteration_count: int = 0
    final_deliverable: str = ""
    chat: List[Dict[str, str]] = field(default_factory=list)
    tests: Dict[str, Any] = field(default_factory=lambda: {"passed": 0, "failed": 0, "summary": "Not run"})
    browser: Dict[str, Any] = field(default_factory=lambda: {"url": "", "screenshot": "", "notes": ""})
    repo: Dict[str, Any] = field(default_factory=dict)
    git: Dict[str, Any] = field(default_factory=dict)
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
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.lock = threading.Lock()
        self._init_schema()

    def _init_schema(self) -> None:
        with self.lock:
            self.conn.execute(
                "CREATE TABLE IF NOT EXISTS memories(id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, kind TEXT NOT NULL, prompt TEXT NOT NULL, summary TEXT NOT NULL, payload TEXT NOT NULL)"
            )
            self.conn.execute(
                "CREATE TABLE IF NOT EXISTS habits(id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, kind TEXT NOT NULL, pattern TEXT NOT NULL, confidence REAL NOT NULL, evidence TEXT NOT NULL)"
            )
            self.conn.execute(
                "CREATE TABLE IF NOT EXISTS tool_logs(id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, agent_name TEXT NOT NULL, tool_name TEXT NOT NULL, reason TEXT NOT NULL, parameters TEXT NOT NULL, result TEXT NOT NULL)"
            )
            self.conn.commit()

    def add(self, kind: str, prompt: str, summary: str, payload: Dict[str, Any]) -> None:
        with self.lock:
            self.conn.execute(
                "INSERT INTO memories(created_at, kind, prompt, summary, payload) VALUES (?,?,?,?,?)",
                (now_iso(), kind, prompt, summary, json.dumps(payload)),
            )
            self.conn.commit()

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        return self._memory_rows(
            "WHERE lower(prompt) LIKE ? OR lower(summary) LIKE ?",
            (f"%{query.lower()}%", f"%{query.lower()}%", limit),
            limit,
        )

    def recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        return self._memory_rows("", (limit,), limit)

    def _memory_rows(self, where: str, params: tuple[Any, ...], limit: int) -> List[Dict[str, Any]]:
        sql = (
            "SELECT created_at, kind, prompt, summary, length(payload) AS payload_size, "
            f"substr(payload, 1, 300) AS payload_preview FROM memories {where} ORDER BY id DESC LIMIT ?"
        )
        with self.lock:
            rows = self.conn.execute(sql, params).fetchall()
        return [
            {
                "created_at": row["created_at"],
                "kind": row["kind"],
                "prompt": row["prompt"],
                "summary": row["summary"],
                "payload": {"preview": row["payload_preview"], "size": row["payload_size"], "truncated": True},
            }
            for row in rows
        ]

    def add_habit(self, kind: str, pattern: str, confidence: float, evidence: Dict[str, Any]) -> None:
        with self.lock:
            self.conn.execute(
                "INSERT INTO habits(created_at, kind, pattern, confidence, evidence) VALUES (?,?,?,?,?)",
                (now_iso(), kind, pattern, confidence, json.dumps(evidence)),
            )
            self.conn.commit()

    def recent_habits(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self.lock:
            rows = self.conn.execute(
                "SELECT created_at, kind, pattern, confidence, length(evidence) AS evidence_size, substr(evidence, 1, 300) AS evidence_preview FROM habits ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            {
                "created_at": row["created_at"],
                "kind": row["kind"],
                "pattern": row["pattern"],
                "confidence": row["confidence"],
                "evidence": {"preview": row["evidence_preview"], "size": row["evidence_size"], "truncated": True},
            }
            for row in rows
        ]

    def add_tool_log(self, agent_name: str, tool_name: str, reason: str, parameters: Dict[str, Any], result: Dict[str, Any]) -> None:
        with self.lock:
            self.conn.execute(
                "INSERT INTO tool_logs(created_at, agent_name, tool_name, reason, parameters, result) VALUES (?,?,?,?,?,?)",
                (now_iso(), agent_name, tool_name, reason, json.dumps(parameters), json.dumps(result)),
            )
            self.conn.commit()

    def recent_tool_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self.lock:
            rows = self.conn.execute(
                "SELECT created_at, agent_name, tool_name, reason, parameters, result FROM tool_logs ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            {
                "created_at": row["created_at"],
                "agent_name": row["agent_name"],
                "tool_name": row["tool_name"],
                "reason": row["reason"],
                "parameters": json_preview(row["parameters"], 2000),
                "result": json_preview(row["result"], 1000),
            }
            for row in rows
        ]
