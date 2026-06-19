"""
Retry utilities with exponential backoff.
Used for LLM calls, database operations, and external API calls.
"""

import asyncio
import logging
import functools
from typing import Callable, Type, Tuple, Any
from app.exceptions import AgentException

logger = logging.getLogger(__name__)

class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retriable_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retriable_exceptions = retriable_exceptions

async def retry_async(
    func: Callable,
    config: RetryConfig = None,
    *args,
    **kwargs
) -> Any:
    """
    Execute async function with retry logic.
    
    Args:
        func: Async function to execute
        config: RetryConfig instance
        *args, **kwargs: Arguments for function
    
    Returns:
        Function result
    
    Raises:
        AgentException: If all retries fail
    """
    if config is None:
        config = RetryConfig()
    
    last_exception = None
    delay = config.initial_delay
    
    for attempt in range(config.max_attempts):
        try:
            return await func(*args, **kwargs)
        except config.retriable_exceptions as e:
            last_exception = e
            
            if attempt < config.max_attempts - 1:
                # Calculate delay with exponential backoff
                next_delay = min(
                    delay * config.exponential_base,
                    config.max_delay
                )
                
                # Add jitter to prevent thundering herd
                if config.jitter:
                    import random
                    next_delay = next_delay * (0.5 + random.random())
                
                logger.warning(
                    f"Attempt {attempt + 1} failed, retrying in {next_delay:.1f}s",
                    extra={
                        "attempt": attempt + 1,
                        "max_attempts": config.max_attempts,
                        "error": str(e),
                        "delay": next_delay
                    }
                )
                
                await asyncio.sleep(next_delay)
                delay = next_delay
            else:
                logger.error(
                    f"All {config.max_attempts} attempts failed",
                    extra={
                        "error": str(e),
                        "function": func.__name__
                    }
                )
    
    raise AgentException(
        message=f"Failed after {config.max_attempts} retries: {last_exception}",
        code="MAX_RETRIES_EXCEEDED",
        details={"original_error": str(last_exception)}
    )

def async_retry(config: RetryConfig = None):
    """Decorator for async functions with retry logic."""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_async(func, config or RetryConfig(), *args, **kwargs)
        return wrapper
    
    return decorator

# Example usage
llm_retry_config = RetryConfig(
    max_attempts=3,
    initial_delay=1.0,
    max_delay=30.0,
    retriable_exceptions=(TimeoutError, ConnectionError, Exception)
)
