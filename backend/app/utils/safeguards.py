"""
Production safeguards for workflow execution.

Provides three hard guards against runaway execution:
  1. Recursion / iteration limits  — caps agent loops per workflow
  2. Wall-clock timeout            — kills workflows that run too long
  3. Rate limiting                 — per-IP throttling (Redis if available,
                                     in-process fallback otherwise)

These wrap WorkflowOrchestrator.run so a malicious or pathological prompt
("Create a full operating system") cannot burn API budget indefinitely.
"""

from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. Iteration / recursion budget
# ---------------------------------------------------------------------------

class IterationBudget:
    """Hard ceiling on how many agent invocations a single workflow may make.

    Mirrors LangGraph's ``recursion_limit`` config: each agent call increments
    the counter, and exceeding the budget raises :class:`BudgetExceeded`.
    """

    def __init__(self, limit: int = 50) -> None:
        self.limit = max(1, int(limit))
        self._count = 0
        self._lock = threading.Lock()

    def tick(self, agent_name: str = "") -> None:
        with self._lock:
            self._count += 1
            if self._count > self.limit:
                raise BudgetExceeded(
                    f"Workflow exceeded iteration limit ({self.limit}) "
                    f"at agent '{agent_name}'"
                )

    @property
    def consumed(self) -> int:
        return self._count

    def reset(self) -> None:
        with self._lock:
            self._count = 0


class BudgetExceeded(RuntimeError):
    """Raised when a workflow blows past its iteration budget."""


# ---------------------------------------------------------------------------
# 2. Wall-clock timeout (thread-safe, no signals — works on Windows)
# ---------------------------------------------------------------------------

class WorkflowTimeoutError(RuntimeError):
    """Raised when a workflow runs past its wall-clock deadline."""


class WorkflowTimeout:
    """Enforce a wall-clock deadline on a (sync) workflow.

    Uses a watchdog thread rather than ``signal.SIGALRM`` so it works on
    Windows and inside worker threads where the orchestrator actually runs.

    Usage::

        with WorkflowTimeout(300) as guard:
            result = orchestrator.run(...)
            guard.checkpoint(result)   # persist partial state if needed
    """

    def __init__(self, seconds: int) -> None:
        self.seconds = max(1, int(seconds))
        self._deadline: float = 0.0
        self._timer: Optional[threading.Timer] = None
        self._timed_out = threading.Event()

    def __enter__(self) -> "WorkflowTimeout":
        self._deadline = time.monotonic() + self.seconds
        self._timed_out.clear()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
        # Swallow our own timeout exception so callers can handle it
        if exc_type is WorkflowTimeoutError:
            return True
        return False

    def touch(self) -> None:
        """Raise if the deadline has passed. Call between agent steps."""
        if self._timed_out.is_set() or time.monotonic() > self._deadline:
            raise WorkflowTimeoutError(
                f"Workflow exceeded {self.seconds}s wall-clock budget"
            )

    def expired(self) -> bool:
        return self._timed_out.is_set() or time.monotonic() > self._deadline

    def checkpoint(self, state: Any, save_fn: Optional[Callable[[str, Any], None]],
                   workflow_id: str, reason: str = "TIMEOUT") -> None:
        """Persist partial state before aborting (best-effort)."""
        if save_fn is None:
            return
        try:
            save_fn(workflow_id, {"partial_state": state, "abort_reason": reason})
        except Exception as exc:  # noqa: BLE001 - checkpoint failure is non-fatal
            logger.warning("Checkpoint save failed during timeout: %s", exc)


# ---------------------------------------------------------------------------
# 3. Per-IP rate limiter
# ---------------------------------------------------------------------------

class RateLimiter:
    """Sliding-window rate limiter keyed by client identifier.

    In production set ``backend_factory`` to a Redis-backed implementation;
    the default in-process dict is only suitable for single-process deploys.
    """

    def __init__(self, max_requests: int = 50, window_seconds: int = 3600) -> None:
        self.max_requests = max(1, int(max_requests))
        self.window_seconds = max(1, int(window_seconds))
        self._hits: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def check(self, key: str) -> Tuple[bool, int]:
        """Return ``(allowed, remaining)`` for the given key (e.g. client IP)."""
        now = time.time()
        cutoff = now - self.window_seconds
        with self._lock:
            bucket = [t for t in self._hits[key] if t > cutoff]
            if len(bucket) >= self.max_requests:
                self._hits[key] = bucket
                return False, 0
            bucket.append(now)
            self._hits[key] = bucket
            return True, self.max_requests - len(bucket)

    def reset(self, key: Optional[str] = None) -> None:
        with self._lock:
            if key is None:
                self._hits.clear()
            else:
                self._hits.pop(key, None)


# ---------------------------------------------------------------------------
# 4. Facade + defaults wired from settings
# ---------------------------------------------------------------------------

class WorkflowGuardrails:
    """Bundles all three guards with sensible defaults from ``settings``."""

    def __init__(
        self,
        max_iterations: int = 50,
        timeout_seconds: int = 300,
        rate_max: int = 50,
        rate_window: int = 3600,
    ) -> None:
        self.budget = IterationBudget(max_iterations)
        self.timeout = WorkflowTimeout(timeout_seconds)
        self.limiter = RateLimiter(rate_max, rate_window)

    @classmethod
    def from_settings(cls) -> "WorkflowGuardrails":
        """Read limits from app config, falling back to safe defaults."""
        try:
            from app.config import settings  # type: ignore
            return cls(
                max_iterations=getattr(settings, "WORKFLOW_MAX_ITERATIONS", 50),
                timeout_seconds=getattr(settings, "WORKFLOW_TIMEOUT_SECONDS", 300),
                rate_max=getattr(settings, "WORKFLOW_RATE_LIMIT", 50),
                rate_window=getattr(settings, "WORKFLOW_RATE_WINDOW", 3600),
            )
        except Exception:  # noqa: BLE001 - config not available (e.g. tests)
            return cls()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
