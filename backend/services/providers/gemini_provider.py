"""
Gemini Cloud Provider
Supports Google Gemini API (gemini-1.5-flash, gemini-2.0-flash, etc.)
Falls back to OpenAI-compatible format if URL is custom.
"""
import json
import urllib.request
import urllib.error
import os
from typing import Dict, Any, Optional
from backend.services.llm_service import LLMServiceProvider

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiProvider(LLMServiceProvider):
    """Native Google Gemini API provider."""

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash") -> None:
        self.api_key = api_key.strip() if api_key else ""
        self.model = model.strip() if model else "gemini-1.5-flash"
        self.ready = bool(self.api_key)

    def is_ready(self) -> bool:
        return self.ready

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
    ) -> str:
        if not self.ready:
            return ""

        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"[System instruction]: {system_prompt}"}]})
            contents.append({"role": "model", "parts": [{"text": "Understood. I will follow those instructions."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "candidateCount": 1,
            }
        }
        if max_tokens:
            payload["generationConfig"]["maxOutputTokens"] = max_tokens

        url = f"{GEMINI_BASE}/{self.model}:generateContent?key={self.api_key}"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))
                candidates = result.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
            return ""
        except Exception as exc:
            raise RuntimeError(f"Gemini API call failed: {exc}") from exc

    def get_status(self) -> Dict[str, Any]:
        if not self.api_key:
            return {
                "provider": "Gemini",
                "ready": False,
                "configured": False,
                "message": "GEMINI_API_KEY not set",
            }
        return {
            "provider": "Gemini",
            "ready": True,
            "configured": True,
            "model": self.model,
            "message": f"Gemini provider ready ({self.model})",
        }
