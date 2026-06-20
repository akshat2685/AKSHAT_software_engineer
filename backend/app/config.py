"""
Application configuration management.
Supports environment-based configuration with validation.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
import os
from typing import Optional, List

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Core
    DEBUG: bool = Field(default=False)
    ENV: str = Field(default="development")  # development, staging, production
    
    # Server
    HOST: str = Field(default="127.0.0.1")
    PORT: int = Field(default=3000)
    
    # Database
    DATABASE_URL: str = Field(...)
    DATABASE_ECHO: bool = Field(default=False)
    
    # JWT/Security
    JWT_SECRET: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRATION_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRATION_DAYS: int = Field(default=7)
    
    # LLM Configuration
    LLM_PROVIDER: str = Field(default="ollama")  # ollama, groq, openai
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434")
    OLLAMA_MODEL: str = Field(default="free01/gemma4:e4b")
    OLLAMA_TIMEOUT: int = Field(default=120)  # seconds
    
    GROQ_API_KEY: Optional[str] = Field(default=None)
    GROQ_MODEL: str = Field(default="mixtral-8x7b-32768")
    
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    OPENAI_MODEL: str = Field(default="gpt-4")
    
    # Cache
    REDIS_URL: Optional[str] = Field(default=None)
    CACHE_ENABLED: bool = Field(default=True)
    CACHE_TTL_SECONDS: int = Field(default=3600)
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"]
    )
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True)
    RATE_LIMIT_REQUESTS: int = Field(default=100)
    RATE_LIMIT_PERIOD: int = Field(default=60)  # seconds

    # Workflow Safeguards — hard limits to prevent infinite loops & runaway cost
    WORKFLOW_MAX_ITERATIONS: int = Field(default=50)
    WORKFLOW_TIMEOUT_SECONDS: int = Field(default=300)
    WORKFLOW_RATE_LIMIT: int = Field(default=50)        # workflows per window
    WORKFLOW_RATE_WINDOW: int = Field(default=3600)     # window in seconds

    # Sandbox (Issue 4)
    SANDBOX_ENABLED: bool = Field(default=True)
    SANDBOX_IMAGE: str = Field(default="python:3.12-slim")
    SANDBOX_MEMORY: str = Field(default="512m")
    SANDBOX_CPUS: str = Field(default="1.0")
    SANDBOX_TIMEOUT_SECONDS: int = Field(default=30)
    SANDBOX_PIDS_LIMIT: int = Field(default=100)

    # Observability (Issue 5)
    LANGSMITH_ENABLED: bool = Field(default=False)
    LANGSMITH_API_KEY: Optional[str] = Field(default=None)
    LANGSMITH_PROJECT: str = Field(default="akshat")

    # Prompt security (Issue 6)
    PROMPT_INJECTION_BLOCK_THRESHOLD: float = Field(default=0.8)
    PROMPT_INJECTION_FLAG_THRESHOLD: float = Field(default=0.5)
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(default="json")  # json or standard
    
    # Project settings
    MAX_PROJECT_NAME_LENGTH: int = 100
    MAX_REQUIREMENTS_PER_PROJECT: int = 50
    MAX_FILE_SIZE_MB: int = 100
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    @field_validator("JWT_SECRET")
    @classmethod
    def validate_jwt_secret(cls, v):
        """Ensure JWT secret is sufficiently long."""
        if len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters")
        return v
    
    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v):
        """Validate database URL format."""
        if not v.startswith(("postgresql://", "sqlite://", "mysql://")):
            raise ValueError("Invalid database URL format")
        return v
    
    @field_validator("LLM_PROVIDER")
    @classmethod
    def validate_llm_provider(cls, v):
        """Ensure valid LLM provider is selected."""
        if v not in ["ollama", "groq", "openai"]:
            raise ValueError("LLM_PROVIDER must be one of: ollama, groq, openai")
        return v
    
    def model_post_init(self, __context) -> None:
        # Validate that required API keys are present for selected provider
        if self.LLM_PROVIDER == "groq" and not self.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY required when LLM_PROVIDER=groq")
        if self.LLM_PROVIDER == "openai" and not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY required when LLM_PROVIDER=openai")

# Global settings instance
settings = Settings()
