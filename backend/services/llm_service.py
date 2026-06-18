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
        from backend.services.providers.gemini_provider import GeminiProvider

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

        # Gemini provider (native Google Generative AI)
        self.gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
        self.gemini_model = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash").strip()

        # DB Overrides
        self._load_db_settings()

        # Providers
        self.ollama_provider = OllamaProvider(self.ollama_url, self.ollama_model, self.ollama_timeout)
        self.cloud_provider = CloudProvider(self.cloud_url, self.cloud_model, self.cloud_key)
        self.gemini_provider = GeminiProvider(self.gemini_key, self.gemini_model)
        self.cloud = self.cloud_provider

    def _load_db_settings(self):
        try:
            from backend.database.connection import SessionLocal
            from backend.database.models import SystemSettings
            db = SessionLocal()
            try:
                db_url = db.query(SystemSettings).filter(SystemSettings.setting_key == "cloud_url").first()
                db_key = db.query(SystemSettings).filter(SystemSettings.setting_key == "cloud_key").first()
                db_model = db.query(SystemSettings).filter(SystemSettings.setting_key == "cloud_model").first()
                
                if db_url and db_url.setting_value:
                    self.cloud_url = db_url.setting_value
                if db_key and db_key.setting_value:
                    self.cloud_key = db_key.setting_value
                if db_model and db_model.setting_value:
                    self.cloud_model = db_model.setting_value
            finally:
                db.close()
        except Exception as e:
            LOGGER.error("Failed to load DB settings: %s", e)

    def update_config(self, cloud_url: str, cloud_key: str, cloud_model: str):
        from backend.database.connection import SessionLocal
        from backend.database.models import SystemSettings
        db = SessionLocal()
        try:
            def _upsert(key, val):
                s = db.query(SystemSettings).filter(SystemSettings.setting_key == key).first()
                if not s:
                    s = SystemSettings(setting_key=key)
                    db.add(s)
                s.setting_value = val

            if cloud_url: _upsert("cloud_url", cloud_url)
            if cloud_key: _upsert("cloud_key", cloud_key)
            if cloud_model: _upsert("cloud_model", cloud_model)
            
            db.commit()

            # Apply to current instance
            self._load_db_settings()
            from backend.services.providers.cloud_provider import CloudProvider
            self.cloud_provider = CloudProvider(self.cloud_url, self.cloud_model, self.cloud_key)
            self.cloud = self.cloud_provider
            self.cloud_fallback_enabled = True # Always enable fallback if user sets custom keys
        finally:
            db.close()

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
                LOGGER.warning("Ollama generation failed: %s. Falling back...", e)

        # 2. Try Gemini (native Google AI)
        if self.gemini_provider.is_ready():
            try:
                LOGGER.info("Using Gemini provider (%s)...", self.gemini_model)
                return self.gemini_provider.generate(prompt, system_prompt, temperature, max_tokens)
            except Exception as e:
                LOGGER.warning("Gemini generation failed: %s. Trying cloud fallback...", e)

        # 3. Try generic Cloud Fallback (OpenAI-compatible)
        if self.cloud_fallback_enabled and self.cloud_provider.is_ready():
            try:
                LOGGER.info("Using Cloud Provider (%s)...", self.cloud_model)
                return self.cloud_provider.generate(prompt, system_prompt, temperature, max_tokens)
            except Exception as e:
                LOGGER.error("Cloud generation fallback also failed: %s", e)

        return ""

    def status(self) -> Dict[str, Any]:
        ollama_status = self.ollama_provider.get_status()
        cloud_status = self.cloud_provider.get_status()
        gemini_status = self.gemini_provider.get_status()
        
        ready = (
            ollama_status.get("ready", False) or
            gemini_status.get("ready", False) or
            (self.cloud_fallback_enabled and cloud_status.get("ready", False))
        )
        
        if ollama_status.get("ready"):
            msg = "Ollama connected"
        elif gemini_status.get("ready"):
            msg = f"Gemini active ({self.gemini_model})"
        elif self.cloud_fallback_enabled and cloud_status.get("ready"):
            msg = "Cloud fallback active"
        else:
            msg = "No LLM provider available — set GEMINI_API_KEY in .env"

        return {
            "provider": "Local inference engine",
            "url": self.ollama_url,
            "configured_model": self.ollama_model,
            "cloud_configured_model": self.cloud_model,
            "cloud_configured_url": self.cloud_url,
            "gemini_model": self.gemini_model,
            "gemini_ready": gemini_status.get("ready", False),
            "resolved_model": ollama_status.get("resolved_model", ""),
            "connected": ollama_status.get("connected", False),
            "installed": ollama_status.get("installed", False),
            "available_models": ollama_status.get("available_models", []),
            "ready": ready,
            "message": msg,
            "cloud": cloud_status,
            "gemini": gemini_status,
        }

    def _get_system_prompt(self, role: str) -> str:
        from pathlib import Path
        root_dir = Path(__file__).resolve().parents[2]
        master_prompt_path = root_dir / "config" / "master_system.prompt"
        master_prompt = ""
        if master_prompt_path.exists():
            master_prompt = master_prompt_path.read_text(encoding="utf-8").strip()
        return f"{master_prompt}\n\nYou are AKSHAT's {role} agent." if master_prompt else f"You are AKSHAT's {role} agent."

    def _generate_with_ollama(self, role: str, prompt: str, model: str, started: float) -> tuple[str, str]:
        try:
            sys_prompt = self._get_system_prompt(role)
            res = self.ollama_provider.generate(prompt=prompt, system_prompt=sys_prompt)
            return res, "ok"
        except Exception as e:
            return "", str(e)

    # Backward compatibility wrapper
    def generate_response(self, role: str, prompt: str) -> str:
        model = self.ollama_provider.resolve_model()
        ollama_text = ""
        if model:
            ollama_text, ollama_status = self._generate_with_ollama(role, prompt, model, time.time())
            if ollama_text:
                return ollama_text
        
        # Try Gemini next
        if self.gemini_provider.is_ready():
            try:
                sys_prompt = self._get_system_prompt(role)
                return self.gemini_provider.generate(prompt=prompt, system_prompt=sys_prompt)
            except Exception as e:
                LOGGER.warning("Gemini generate_response failed: %s", e)

        # Fallback to cloud
        if self.cloud_fallback_enabled and self.cloud_provider.is_ready():
            sys_prompt = self._get_system_prompt(role)
            return self.cloud_provider.generate(prompt=prompt, system_prompt=sys_prompt)
        return ""

# Singleton service instance
_default_service = LLMService()

def generate_response(role: str, prompt: str) -> str:
    return _default_service.generate_response(role, prompt)
