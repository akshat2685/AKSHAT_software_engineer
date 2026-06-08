import os
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

LOGGER = logging.getLogger(__name__)

class LLMServiceProvider(ABC):
    @abstractmethod
    def is_ready(self) -> bool:
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: Optional[int] = None
    ) -> str:
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        pass

class LLMService:
    def __init__(
        self,
        url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
        cloud_api_key: Optional[str] = None,
        cloud_api_url: Optional[str] = None,
        cloud_api_model: Optional[str] = None,
        cloud_fallback_enabled: Optional[bool] = None,
    ) -> None:
        from backend.services.providers.ollama_provider import OllamaProvider
        from backend.services.providers.cloud_provider import CloudProvider

        # Load environment values or constructor args
        self.ollama_url = url or os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
        self.ollama_model = model or os.environ.get("OLLAMA_MODEL", "free01/gemma4:e4b").strip()
        
        timeout_env = os.environ.get("OLLAMA_TIMEOUT_SECONDS", "5")
        self.ollama_timeout = timeout if timeout is not None else float(timeout_env)

        self.cloud_key = cloud_api_key if cloud_api_key is not None else os.environ.get("CLOUD_API_KEY", "").strip()
        self.cloud_url = cloud_api_url if cloud_api_url is not None else (
            os.environ.get("CLOUD_API_URL", "").strip() or 
            os.environ.get("CLOUD_API_BASE_URL", "").strip()
        )
        if not self.cloud_url and self.cloud_key.startswith("gsk_"):
            self.cloud_url = "https://api.groq.com/openai/v1/chat/completions"
            
        self.cloud_model = cloud_api_model if cloud_api_model is not None else os.environ.get("CLOUD_API_MODEL", "").strip()
        if not self.cloud_model and self.cloud_key.startswith("gsk_"):
            self.cloud_model = "llama-3.3-70b-versatile"

        if cloud_fallback_enabled is not None:
            self.cloud_fallback_enabled = cloud_fallback_enabled
        else:
            fallback_val = os.environ.get("CLOUD_FALLBACK_ENABLED") or os.environ.get("AKSHAT_CLOUD_FALLBACK", "true")
            self.cloud_fallback_enabled = fallback_val.strip().lower() in {"1", "true", "yes", "y", "on", "enabled"}

        # Providers
        self.ollama_provider = OllamaProvider(self.ollama_url, self.ollama_model, self.ollama_timeout)
        self.cloud_provider = CloudProvider(self.cloud_url, self.cloud_model, self.cloud_key)
        self.cloud = self.cloud_provider

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: Optional[int] = None
    ) -> str:
        # 1. Try local Ollama
        if self.ollama_provider.is_ready():
            try:
                LOGGER.info("Generating response using local Ollama (%s)...", self.ollama_model)
                res = self.ollama_provider.generate(prompt, system_prompt, temperature, max_tokens)
                if res:
                    return res
            except Exception as e:
                LOGGER.warning("Ollama generation failed: %s. Falling back to cloud...", e)

        # 2. Try Cloud Fallback
        if self.cloud_fallback_enabled and self.cloud_provider.is_ready():
            try:
                LOGGER.info("Local Ollama unavailable or failed. Using Cloud Provider (%s)...", self.cloud_model)
                return self.cloud_provider.generate(prompt, system_prompt, temperature, max_tokens)
            except Exception as e:
                LOGGER.error("Cloud generation fallback also failed: %s", e)

        return ""

    def status(self) -> Dict[str, Any]:
        ollama_status = self.ollama_provider.get_status()
        cloud_status = self.cloud_provider.get_status()
        
        ready = ollama_status.get("ready", False) or (self.cloud_fallback_enabled and cloud_status.get("ready", False))
        
        # Build status message
        if ollama_status.get("ready"):
            msg = "Ollama connected; cloud fallback available" if cloud_status.get("ready") else "Inference engine connected"
        elif self.cloud_fallback_enabled and cloud_status.get("ready"):
            msg = "Local Ollama offline; cloud fallback active"
        else:
            msg = "No LLM provider available"

        return {
            "provider": "Local inference engine",
            "url": self.ollama_url,
            "configured_model": self.ollama_model,
            "resolved_model": ollama_status.get("resolved_model", ""),
            "connected": ollama_status.get("connected", False),
            "installed": ollama_status.get("installed", False),
            "available_models": ollama_status.get("available_models", []),
            "ready": ready,
            "message": msg,
            "cloud": cloud_status,
        }

    def _generate_with_ollama(self, role: str, prompt: str, model: str, started: float) -> tuple[str, str]:
        try:
            res = self.ollama_provider.generate(prompt=prompt, system_prompt=f"You are AKSHAT's {role} agent.")
            return res, "ok"
        except Exception as e:
            return "", str(e)

    # Backward compatibility wrapper
    def generate_response(self, role: str, prompt: str) -> str:
        model = self.ollama_provider.resolve_model()
        ollama_text = ""
        ollama_status = "model_unavailable"
        if model:
            # Call the helper so it can be patched in tests
            ollama_text, ollama_status = self._generate_with_ollama(role, prompt, model, time.time())
            if ollama_text:
                return ollama_text
        
        # Fallback to cloud
        if self.cloud_fallback_enabled and self.cloud_provider.is_ready():
            return self.cloud.generate_response(role, prompt)
        return ""

# Singleton service instance
_default_service = LLMService()

def generate_response(role: str, prompt: str) -> str:
    return _default_service.generate_response(role, prompt)
