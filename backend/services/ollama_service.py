from typing import Any, Optional, Callable
from backend.services.llm_service import LLMService, generate_response

class OllamaService(LLMService):
    def __init__(self, logger: Optional[Callable[..., Any]] = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if logger:
            self.logger = logger
            # Bind the logger to LLMService's loggers if needed
