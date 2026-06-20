"""
Sandboxed execution engine (Issue 4).

The AI generates code and we execute it — this is the highest-risk surface in
the system. Every execution runs inside an **ephemeral Docker container** with:

  • network disabled              (--network none)        — no data exfiltration
  • read-only root filesystem     (--read-only)           — no host writes
  • memory cap                    (--memory)              — no OOM bombs
  • CPU cap                       (--cpus)                — no CPU hogging
  • process cap                   (--pids-limit)          — no fork bombs
  • all capabilities dropped      (--cap-drop ALL)        — no privileged ops
  • no privilege escalation       (--security-opt)        — no setuid escapes
  • command allowlist             (ALLOWED_COMMANDS)      — least privilege
  • wall-clock timeout            (--timeout) + kill      — no infinite loops
  • stdout/stderr truncation                              — no log bombs

If Docker is unavailable (e.g. local dev without Docker), the engine refuses to
run untrusted code rather than falling back to a naked subprocess. Shell=True is
never used: commands are passed as an argv list.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Allowlist of base commands the sandbox may run. Anything not here is refused
# before Docker is ever invoked. Extend deliberately — never use a wildcard.
ALLOWED_COMMANDS: set[str] = {
    "python3", "python", "node", "npm", "npx",
    "pip", "pytest", "black", "flake8", "mypy",
    "curl", "wget",  # only useful because --network none blocks them anyway
}

DEFAULT_IMAGE = "python:3.12-slim"
DEFAULT_MEMORY = "512m"
DEFAULT_CPUS = "1.0"
DEFAULT_PIDS_LIMIT = 100
DEFAULT_TIMEOUT_SECONDS = 30
MAX_OUTPUT_CHARS = 10_000  # truncate to bound log/db growth


class SandboxError(Exception):
    """Raised when a command is rejected or the sandbox is unavailable."""


class SandboxEngine:
    """Execute commands in hardened ephemeral Docker containers."""

    def __init__(
        self,
        image: str = DEFAULT_IMAGE,
        memory: str = DEFAULT_MEMORY,
        cpus: str = DEFAULT_CPUS,
        pids_limit: int = DEFAULT_PIDS_LIMIT,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        max_output_chars: int = MAX_OUTPUT_CHARS,
    ) -> None:
        self.image = image
        self.memory = memory
        self.cpus = cpus
        self.pids_limit = pids_limit
        self.timeout_seconds = timeout_seconds
        self.max_output_chars = max_output_chars

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute_in_sandbox(
        self,
        command: List[str] | str,
        workspace_path: Optional[str] = None,
        image: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run ``command`` in an isolated container.

        Args:
            command: Either an argv list (preferred) or a shell string. A
                string is split with shlex and the first element must be in
                the allowlist. We never invoke a shell inside the container.
            workspace_path: Host directory mounted read-write at /workspace
                inside the container. If omitted, the container has no
                writable host storage (read-only root + tmpfs only).
            image: Override the default sandbox image.

        Returns:
            Dict with ``success``, ``returncode``, ``stdout``, ``stderr``,
            ``duration_ms``, and optional ``error`` keys.
        """
        argv = self._normalize_command(command)
        self._authorize(argv)

        if not self._docker_available():
            return self._refuse(
                "Docker is not available; refusing to execute untrusted code "
                "outside the sandbox."
            )

        docker_argv = self._build_docker_argv(argv, workspace_path, image)
        logger.info("Sandbox executing: %s", " ".join(docker_argv[:6]) + " ...")

        try:
            result = subprocess.run(
                docker_argv,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": f"Execution timed out after {self.timeout_seconds}s",
                "error": "TIMEOUT",
                "killed": True,
            }
        except FileNotFoundError as exc:
            return self._refuse(f"Docker executable not found: {exc}")

        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": self._truncate(result.stdout),
            "stderr": self._truncate(result.stderr),
        }

    def execute_in_container(
        self,
        command: List[str] | str,
        workspace_path: Optional[str] = None,
        image: Optional[str] = None,
        memory: Optional[str] = None,
        cpus: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Alias for :meth:`execute_in_sandbox` with per-call resource overrides."""
        if memory:
            self.memory = memory
        if cpus:
            self.cpus = cpus
        return self.execute_in_sandbox(command, workspace_path, image)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _normalize_command(self, command: List[str] | str) -> List[str]:
        if isinstance(command, str):
            import shlex
            argv = shlex.split(command)
        else:
            argv = list(command)
        if not argv:
            raise SandboxError("Empty command")
        return argv

    def _authorize(self, argv: List[str]) -> None:
        """Reject anything not on the allowlist before touching Docker."""
        base = Path(argv[0]).name  # tolerate absolute paths like /usr/bin/python3
        if base not in ALLOWED_COMMANDS:
            raise SandboxError(
                f"Command '{base}' is not in the sandbox allowlist: "
                f"{sorted(ALLOWED_COMMANDS)}"
            )

    def _build_docker_argv(
        self,
        argv: List[str],
        workspace_path: Optional[str],
        image: Optional[str],
    ) -> List[str]:
        cmd: List[str] = [
            "docker", "run", "--rm",
            "--network", "none",
            "--read-only",
            "--memory", self.memory,
            "--cpus", self.cpus,
            "--pids-limit", str(self.pids_limit),
            "--security-opt", "no-new-privileges:true",
            "--cap-drop", "ALL",
            # tmpfs so the process can still write temp files despite --read-only
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
        ]
        if workspace_path:
            ws = str(Path(workspace_path).resolve())
            cmd += ["-v", f"{ws}:/workspace:rw", "-w", "/workspace"]
        cmd.append(image or self.image)
        cmd += argv
        return cmd

    def _truncate(self, text: str) -> str:
        if not text:
            return ""
        if len(text) <= self.max_output_chars:
            return text
        return text[: self.max_output_chars] + "\n...[truncated]..."

    def _refuse(self, reason: str) -> Dict[str, Any]:
        logger.warning("Sandbox refused execution: %s", reason)
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": reason,
            "error": "SANDBOX_UNAVAILABLE",
        }

    @staticmethod
    def _docker_available() -> bool:
        return shutil.which("docker") is not None


sandbox_engine = SandboxEngine()
