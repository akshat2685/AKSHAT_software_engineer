"""
Custom exceptions for the application.
Provides structured error handling across agents and API.
"""

class AkshatException(Exception):
    """Base exception for all AKSHAT exceptions."""
    
    def __init__(self, message: str, code: str = None, details: dict = None):
        self.message = message
        self.code = code or "INTERNAL_ERROR"
        self.details = details or {}
        super().__init__(self.message)

class AgentException(AkshatException):
    """Raised when an agent fails to execute."""
    pass

class AgentTimeoutException(AgentException):
    """Raised when an agent execution times out."""
    code = "AGENT_TIMEOUT"

class LLMException(AkshatException):
    """Raised when LLM API call fails."""
    pass

class LLMProviderException(LLMException):
    """Raised when LLM provider is unavailable."""
    code = "LLM_PROVIDER_UNAVAILABLE"

class ValidationException(AkshatException):
    """Raised when input validation fails."""
    code = "VALIDATION_ERROR"

class WorkflowException(AkshatException):
    """Raised when workflow execution fails."""
    pass

class DatabaseException(AkshatException):
    """Raised when database operation fails."""
    pass

class AuthenticationException(AkshatException):
    """Raised when authentication fails."""
    code = "AUTHENTICATION_FAILED"

class AuthorizationException(AkshatException):
    """Raised when user doesn't have permission."""
    code = "UNAUTHORIZED"
