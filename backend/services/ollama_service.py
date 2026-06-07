from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, Optional


OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "free01/gemma4:e4b").strip()


class OllamaService:
    def __init__(
        self,
        url: str = OLLAMA_URL,
        model: str = OLLAMA_MODEL,
        logger: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        self.url = url
        self.configured_model = model
        self.logger = logger

    def resolve_model(self) -> str:
        if self.configured_model:
            return self.configured_model
        try:
            completed = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=15, shell=False)
        except Exception:
            return ""
        if completed.returncode != 0:
            return ""
        lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
        if len(lines) < 2:
            return ""
        return lines[1].split()[0]

    def _tags_url(self) -> str:
        parsed = urllib.parse.urlparse(self.url)
        return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, "/api/tags", "", "", ""))

    def connection_status(self) -> Dict[str, Any]:
        try:
            with urllib.request.urlopen(self._tags_url(), timeout=3) as response:
                payload = json.loads(response.read().decode())
        except urllib.error.URLError as exc:
            return {"connected": False, "models": [], "error": str(exc.reason)}
        except Exception as exc:
            return {"connected": False, "models": [], "error": str(exc)}
        models = [item.get("name", "") for item in payload.get("models", []) if item.get("name")]
        return {"connected": True, "models": models, "error": ""}

    def status(self) -> Dict[str, Any]:
        model = self.resolve_model()
        connection = self.connection_status()
        installed = model in connection["models"]
        ready = bool(model and connection["connected"] and installed)
        return {
            "provider": "Local inference engine",
            "url": self.url,
            "configured_model": self.configured_model,
            "resolved_model": model,
            "connected": connection["connected"],
            "installed": installed,
            "available_models": connection["models"],
            "ready": ready,
            "message": self._status_message(model, connection, installed),
        }

    def generate_response(self, role: str, prompt: str) -> str:
        started = time.time()
        model = self.resolve_model()
        if not model:
            self._log(role, prompt, "", 0, "model_unavailable")
            return ""
        payload = {"model": model, "prompt": prompt, "stream": False}
        request = urllib.request.Request(
            self.url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                text = json.loads(response.read().decode()).get("response", "").strip()
            self._log(role, prompt, text, int((time.time() - started) * 1000), "ok")
            return text
        except Exception as exc:
            self._log(role, prompt, "", int((time.time() - started) * 1000), str(exc))
            return ""

    def _status_message(self, model: str, connection: Dict[str, Any], installed: bool) -> str:
        if not model:
            return "No local model configured"
        if not connection["connected"]:
            return "Inference engine offline"
        if not installed:
            return "Configured model not found locally"
        return "Inference engine connected"

    def _log(self, role: str, prompt: str, response: str, duration_ms: int, status: str) -> None:
        if self.logger:
            self.logger(
                {
                    "role": role,
                    "prompt_chars": len(prompt),
                    "response_chars": len(response),
                    "duration_ms": duration_ms,
                    "status": status,
                }
            )


_default_service = OllamaService()


def generate_response(role: str, prompt: str) -> str:
    return _default_service.generate_response(role, prompt)
