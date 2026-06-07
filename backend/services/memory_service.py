from __future__ import annotations

from typing import Any, Dict, List, Protocol


class MemoryBackend(Protocol):
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        ...

    def add(self, kind: str, prompt: str, summary: str, payload: Dict[str, Any]) -> None:
        ...


class MemoryService:
    def __init__(self, backend: MemoryBackend):
        self.backend = backend

    def retrieve(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        return self.backend.search(query, limit)

    def store_entry(self, problem: str, solution: str, outcome: str, payload: Dict[str, Any]) -> None:
        self.backend.add(
            "memory_entry",
            problem,
            solution,
            {"outcome": outcome, "embedding": payload.get("embedding", []), **payload},
        )
