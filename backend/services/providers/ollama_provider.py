import json
import urllib.request
import urllib.parse
import urllib.error
import subprocess
import time
from typing import Dict, Any, Optional, List
from backend.services.llm_service import LLMServiceProvider

class OllamaProvider(LLMServiceProvider):
    def __init__(self, url: str, model: str, timeout: float = 15.0) -> None:
        self.url = url
        self.configured_model = model
        self.timeout = timeout
        self.last_failed_time = 0.0

    def resolve_model(self) -> str:
        if self.configured_model:
            return self.configured_model
        try:
            completed = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5, shell=False)
            if completed.returncode == 0:
                lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
                if len(lines) > 1:
                    return lines[1].split()[0]
        except Exception:
            pass
        return ""

    def _tags_url(self) -> str:
        parsed = urllib.parse.urlparse(self.url)
        return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, "/api/tags", "", "", ""))

    def connection_status(self) -> Dict[str, Any]:
        if time.time() - self.last_failed_time < 30.0:
            return {"connected": False, "models": [], "error": "Ollama connection in cooldown"}
        try:
            with urllib.request.urlopen(self._tags_url(), timeout=3) as response:
                payload = json.loads(response.read().decode())
            models = [item.get("name", "") for item in payload.get("models", []) if item.get("name")]
            return {"connected": True, "models": models, "error": ""}
        except Exception as exc:
            self.last_failed_time = time.time()
            return {"connected": False, "models": [], "error": str(exc)}

    def is_ready(self) -> bool:
        if time.time() - self.last_failed_time < 30.0:
            return False
        model = self.resolve_model()
        conn = self.connection_status()
        installed = model in conn["models"]
        return bool(model and conn["connected"] and installed)

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: Optional[int] = None
    ) -> str:
        model = self.resolve_model()
        if not model:
            return ""

        # Construct raw prompt with system instruction context if present
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\nUser: {prompt}"

        payload = {
            "model": model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        req = urllib.request.Request(
            self.url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                result = json.loads(response.read().decode())
                return result.get("response", "").strip()
        except Exception as exc:
            self.last_failed_time = time.time()
            raise RuntimeError(f"Ollama call failed: {exc}") from exc

    def get_status(self) -> Dict[str, Any]:
        model = self.resolve_model()
        conn = self.connection_status()
        installed = model in conn["models"]
        ready = bool(model and conn["connected"] and installed)
        return {
            "ready": ready,
            "connected": conn["connected"],
            "installed": installed,
            "resolved_model": model,
            "available_models": conn["models"]
        }
