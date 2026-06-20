import os
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

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


class BaseOpenAICompatibleProvider(LLMServiceProvider):
    """Base class for OpenAI-compatible APIs (OpenAI, OpenRouter, Ollama Cloud, NVIDIA NIM, Groq, etc.)"""
    
    def __init__(self, name: str, url: str, model: str, api_key: str) -> None:
        self.name = name
        self.url = url.strip() if url else ""
        self.model = model.strip() if model else ""
        self.api_key = api_key.strip() if api_key else ""
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
        
        import json
        import urllib.request
        import urllib.error
        
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
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode())
                
                choices = result.get("choices", [])
                if choices:
                    first = choices[0] or {}
                    msg = first.get("message") or {}
                    if isinstance(msg, dict) and msg.get("content"):
                        return msg["content"].strip()
                return ""
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            raise RuntimeError(f"{self.name} HTTP error {e.code}: {error_body}")
        except Exception as exc:
            raise RuntimeError(f"{self.name} call failed: {exc}") from exc

    def get_status(self) -> Dict[str, Any]:
        msg = f"{self.name} ready"
        if not self.api_key:
            msg = f"{self.name} disabled - API key missing"
        elif not self.url or not self.model:
            msg = f"{self.name} disabled - URL/model missing"
        
        return {
            "provider": self.name,
            "url": self.url,
            "configured_model": self.model,
            "configured": bool(self.api_key),
            "ready": self.ready,
            "api_key_present": bool(self.api_key),
            "message": msg
        }


class OllamaProvider(LLMServiceProvider):
    """Local Ollama provider"""
    
    def __init__(self, url: str, model: str, timeout: float) -> None:
        self.url = url.strip() if url else "http://localhost:11434/api/generate"
        self.model = model.strip() if model else "free01/gemma4:e4b"
        self.timeout = timeout
        self._resolved_model = None

    def is_ready(self) -> bool:
        try:
            import urllib.request
            req = urllib.request.Request(f"{self.url.replace('/api/generate', '')}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except Exception:
            return False

    def resolve_model(self) -> Optional[str]:
        if self._resolved_model:
            return self._resolved_model
        try:
            import urllib.request
            import json
            req = urllib.request.Request(f"{self.url.replace('/api/generate', '')}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                models = [m.get("name", "") for m in data.get("models", [])]
                # Try exact match, then prefix match
                for m in models:
                    if m == self.model:
                        self._resolved_model = m
                        return m
                for m in models:
                    if m.startswith(self.model.split(":")[0]):
                        self._resolved_model = m
                        return m
                if models:
                    self._resolved_model = models[0]
                    return models[0]
        except Exception:
            pass
        return None

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: Optional[int] = None
    ) -> str:
        import json
        import urllib.request
        
        model = self.resolve_model() or self.model
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        payload = {
            "model": model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        try:
            req = urllib.request.Request(
                self.url,
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                result = json.loads(response.read().decode())
                return result.get("response", "").strip()
        except Exception as e:
            LOGGER.warning("Ollama generation failed: %s", e)
            raise

    def get_status(self) -> Dict[str, Any]:
        connected = self.is_ready()
        model = self.resolve_model()
        return {
            "provider": "Ollama",
            "url": self.url,
            "configured_model": self.model,
            "resolved_model": model or "",
            "connected": connected,
            "installed": connected,
            "available_models": [model] if model else [],
            "ready": connected,
            "message": "Ollama connected" if connected else "Ollama not running"
        }


class GeminiProvider(LLMServiceProvider):
    """Google Gemini native provider"""
    
    def __init__(self, api_key: str, model: str) -> None:
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
        max_tokens: Optional[int] = None
    ) -> str:
        if not self.ready:
            return ""
        
        try:
            import google.generativeai as genai
        except ImportError:
            LOGGER.warning("google-generativeai not installed")
            return ""
        
        try:
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model)
            
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens or 8192,
            )
            
            response = model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            if response.text:
                return response.text.strip()
            return ""
        except Exception as e:
            LOGGER.warning("Gemini generation failed: %s", e)
            raise

    def get_status(self) -> Dict[str, Any]:
        return {
            "provider": "Gemini",
            "configured_model": self.model,
            "ready": self.ready,
            "api_key_present": bool(self.api_key),
            "message": f"Gemini active ({self.model})" if self.ready else "Gemini disabled - GEMINI_API_KEY missing"
        }


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
        
        # Local Ollama
        self.ollama_url = url or os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
        self.ollama_model = model or os.environ.get("OLLAMA_MODEL", "free01/gemma4:e4b").strip()
        timeout_env = os.environ.get("OLLAMA_TIMEOUT_SECONDS", "120")
        self.ollama_timeout = timeout if timeout is not None else float(timeout_env)
        
        # NVIDIA NIM Cloud (existing)
        self.cloud_key = cloud_api_key if cloud_api_key is not None else os.environ.get("CLOUD_API_KEY", "").strip()
        self.cloud_url = cloud_api_url if cloud_api_url is not None else (
            os.environ.get("CLOUD_API_URL", "").strip() or 
            os.environ.get("CLOUD_API_BASE_URL", "").strip()
        )
        if not self.cloud_url and self.cloud_key.startswith("nvapi-"):
            self.cloud_url = "https://integrate.api.nvidia.com/v1/chat/completions"
        self.cloud_model = cloud_api_model if cloud_api_model is not None else os.environ.get("CLOUD_API_MODEL", "").strip()
        if not self.cloud_model and self.cloud_key.startswith("nvapi-"):
            self.cloud_model = "nvidia/llama-3.1-nemotron-70b-instruct"
        
        # OpenAI
        self.openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
        self.openai_model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip()
        self.openai_url = "https://api.openai.com/v1/chat/completions"
        
        # OpenRouter
        self.openrouter_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        self.openrouter_model = os.environ.get("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet").strip()
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Ollama Cloud
        self.ollama_cloud_key = os.environ.get("OLLAMA_CLOUD_API_KEY", "").strip()
        self.ollama_cloud_model = os.environ.get("OLLAMA_CLOUD_MODEL", "llama3.1:8b").strip()
        self.ollama_cloud_url = "https://ollama.com/api/chat/completions"
        
        # Gemini
        self.gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
        self.gemini_model = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash").strip()
        
        # Fallback settings
        if cloud_fallback_enabled is not None:
            self.cloud_fallback_enabled = cloud_fallback_enabled
        else:
            fallback_val = os.environ.get("CLOUD_FALLBACK_ENABLED") or os.environ.get("AKSHAT_CLOUD_FALLBACK", "true")
            self.cloud_fallback_enabled = fallback_val.strip().lower() in {"1", "true", "yes", "y", "on", "enabled"}
        
        # DB Overrides
        self._load_db_settings()
        
        # Initialize Providers
        self.ollama_provider = OllamaProvider(self.ollama_url, self.ollama_model, self.ollama_timeout)
        
        # NVIDIA NIM Cloud
        self.cloud_provider = BaseOpenAICompatibleProvider(
            "NVIDIA NIM", self.cloud_url, self.cloud_model, self.cloud_key
        )
        
        # OpenAI
        self.openai_provider = BaseOpenAICompatibleProvider(
            "OpenAI", self.openai_url, self.openai_model, self.openai_key
        )
        
        # OpenRouter
        self.openrouter_provider = BaseOpenAICompatibleProvider(
            "OpenRouter", self.openrouter_url, self.openrouter_model, self.openrouter_key
        )
        
        # Ollama Cloud
        self.ollama_cloud_provider = BaseOpenAICompatibleProvider(
            "Ollama Cloud", self.ollama_cloud_url, self.ollama_cloud_model, self.ollama_cloud_key
        )
        
        # Gemini
        self.gemini_provider = GeminiProvider(self.gemini_key, self.gemini_model)
        
        # Default cloud provider (NVIDIA NIM) for backward compatibility
        self.cloud = self.cloud_provider
        
        # Ollama timeout
        self.ollama_timeout = self.ollama_timeout

    def _load_db_settings(self):
        try:
            from backend.database.connection import SessionLocal
            from backend.database.models import SystemSettings
            db = SessionLocal()
            try:
                for key in ["cloud_url", "cloud_key", "cloud_model", "openai_key", "openrouter_key", "gemini_key"]:
                    db_val = db.query(SystemSettings).filter(SystemSettings.setting_key == key).first()
                    if db_val and db_val.setting_value:
                        setattr(self, key, db_val.setting_value)
            finally:
                db.close()
        except Exception as e:
            LOGGER.error("Failed to load DB settings: %s", e)

    def update_config(self, **kwargs):
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
            
            for key, val in kwargs.items():
                if val:
                    _upsert(key, val)
            
            db.commit()
            self._load_db_settings()
            # Reinitialize providers with new values
            self._reinit_providers()
        finally:
            db.close()

    def _reinit_providers(self):
        self.cloud_provider = BaseOpenAICompatibleProvider(
            "NVIDIA NIM", self.cloud_url, self.cloud_model, self.cloud_key
        )
        self.openai_provider = BaseOpenAICompatibleProvider(
            "OpenAI", self.openai_url, self.openai_model, self.openai_key
        )
        self.openrouter_provider = BaseOpenAICompatibleProvider(
            "OpenRouter", self.openrouter_url, self.openrouter_model, self.openrouter_key
        )
        self.ollama_cloud_provider = BaseOpenAICompatibleProvider(
            "Ollama Cloud", self.ollama_cloud_url, self.ollama_cloud_model, self.ollama_cloud_key
        )
        self.gemini_provider = GeminiProvider(self.gemini_key, self.gemini_model)

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: Optional[int] = None
    ) -> str:
        # Priority order: Local Ollama → OpenAI → OpenRouter → Ollama Cloud → NVIDIA NIM → Gemini
        
        # 1. Try local Ollama
        if self.ollama_provider.is_ready():
            try:
                LOGGER.info("Generating response using local Ollama (%s)...", self.ollama_model)
                res = self.ollama_provider.generate(prompt, system_prompt, temperature, max_tokens)
                if res:
                    return res
            except Exception as e:
                LOGGER.warning("Ollama generation failed: %s. Falling back...", e)

        # 2. Try OpenAI
        if self.openai_provider.is_ready():
            try:
                LOGGER.info("Using OpenAI (%s)...", self.openai_model)
                return self.openai_provider.generate(prompt, system_prompt, temperature, max_tokens)
            except Exception as e:
                LOGGER.warning("OpenAI generation failed: %s. Falling back...", e)

        # 3. Try OpenRouter
        if self.openrouter_provider.is_ready():
            try:
                LOGGER.info("Using OpenRouter (%s)...", self.openrouter_model)
                return self.openrouter_provider.generate(prompt, system_prompt, temperature, max_tokens)
            except Exception as e:
                LOGGER.warning("OpenRouter generation failed: %s. Falling back...", e)

        # 4. Try Ollama Cloud
        if self.ollama_cloud_provider.is_ready():
            try:
                LOGGER.info("Using Ollama Cloud (%s)...", self.ollama_cloud_model)
                return self.ollama_cloud_provider.generate(prompt, system_prompt, temperature, max_tokens)
            except Exception as e:
                LOGGER.warning("Ollama Cloud generation failed: %s. Falling back...", e)

        # 5. Try NVIDIA NIM Cloud
        if self.cloud_fallback_enabled and self.cloud_provider.is_ready():
            try:
                LOGGER.info("Using NVIDIA NIM (%s)...", self.cloud_model)
                return self.cloud_provider.generate(prompt, system_prompt, temperature, max_tokens)
            except Exception as e:
                LOGGER.error("NVIDIA NIM generation failed: %s", e)

        # 6. Try Gemini
        if self.gemini_provider.is_ready():
            try:
                LOGGER.info("Using Gemini (%s)...", self.gemini_model)
                return self.gemini_provider.generate(prompt, system_prompt, temperature, max_tokens)
            except Exception as e:
                LOGGER.error("Gemini generation fallback also failed: %s", e)

        return ""

    def status(self) -> Dict[str, Any]:
        providers_status = {
            "ollama": self.ollama_provider.get_status(),
            "openai": self.openai_provider.get_status(),
            "openrouter": self.openrouter_provider.get_status(),
            "ollama_cloud": self.ollama_cloud_provider.get_status(),
            "nvidia_nim": self.cloud_provider.get_status(),
            "gemini": self.gemini_provider.get_status(),
        }
        
        ready = any(p.get("ready", False) for p in providers_status.values())
        
        # Determine active provider
        if providers_status["ollama"].get("ready"):
            msg = "Ollama connected (local)"
        elif providers_status["openai"].get("ready"):
            msg = f"OpenAI active ({self.openai_model})"
        elif providers_status["openrouter"].get("ready"):
            msg = f"OpenRouter active ({self.openrouter_model})"
        elif providers_status["ollama_cloud"].get("ready"):
            msg = f"Ollama Cloud active ({self.ollama_cloud_model})"
        elif providers_status["nvidia_nim"].get("ready"):
            msg = f"NVIDIA NIM active ({self.cloud_model})"
        elif providers_status["gemini"].get("ready"):
            msg = f"Gemini active ({self.gemini_model})"
        else:
            msg = "No LLM provider available"
        
        return {
            "provider": "Multi-provider LLM Service",
            "providers": providers_status,
            "ready": ready,
            "message": msg
        }

    def _get_system_prompt(self, role: str) -> str:
        from pathlib import Path
        root_dir = Path(__file__).resolve().parents[2]
        master_prompt_path = root_dir / "config" / "master_system.prompt"
        master_prompt = ""
        if master_prompt_path.exists():
            master_prompt = master_prompt_path.read_text(encoding="utf-8").strip()
        return f"{master_prompt}\n\nYou are AKSHAT's {role} agent." if master_prompt else f"You are AKSHAT's {role} agent."

    def generate_response(self, role: str, prompt: str) -> str:
        system_prompt = self._get_system_prompt(role)
        return self.generate(prompt, system_prompt)


# Singleton service instance
_default_service = LLMService()

def generate_response(role: str, prompt: str) -> str:
    return _default_service.generate_response(role, prompt)