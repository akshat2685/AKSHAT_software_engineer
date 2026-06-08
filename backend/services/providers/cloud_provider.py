import json
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, Any, Optional
from backend.services.llm_service import LLMServiceProvider

class CloudProvider(LLMServiceProvider):
    def __init__(self, url: str, model: str, api_key: str) -> None:
        self.url = url.strip()
        self.model = model.strip()
        self.api_key = api_key.strip()
        self.ready = bool(self.api_key and self.url and self.model)

    def is_ready(self) -> bool:
        return self.ready

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: Optional[int] = None
    ) -> str:
        if not self.ready:
            return ""

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "temperature": temperature
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        req = urllib.request.Request(
            self.url,
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            },
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode())
                
                # Try to extract content
                choices = result.get("choices", [])
                if choices:
                    first = choices[0] or {}
                    msg = first.get("message") or {}
                    if isinstance(msg, dict) and msg.get("content"):
                        return msg["content"].strip()
                return ""
        except Exception as exc:
            raise RuntimeError(f"Cloud provider call failed: {exc}") from exc

    def generate_response(self, role: str, prompt: str, logger: Optional[Any] = None) -> str:
        return self.generate(prompt, system_prompt=f"You are AKSHAT's {role} agent.")

    def get_status(self) -> Dict[str, Any]:
        msg = "Cloud provider ready"
        if not self.api_key:
            msg = "Cloud provider disabled until CLOUD_API_KEY is set"
        elif not self.url or not self.model:
            msg = "Cloud provider disabled until URL and model are configured"

        return {
            "provider": "Cloud API",
            "url": self.url,
            "configured_model": self.model,
            "configured": bool(self.api_key),
            "ready": self.ready,
            "fallback_enabled": self.ready, # or fallback configured
            "api_key_present": bool(self.api_key),
            "disabled_reason": self._disabled_reason() if not self.ready else "",
            "message": msg
        }

    def _disabled_reason(self) -> str:
        if not self.api_key:
            return "CLOUD_API_KEY is missing"
        if not self.url:
            return "CLOUD_API_URL is missing"
        if not self.model:
            return "CLOUD_API_MODEL is missing"
        return ""
