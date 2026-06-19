"""
Custom middleware for request/response handling.
Includes logging, error handling, request ID tracking, and metrics.
"""

import time
import uuid
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID for tracking."""
    
    async def dispatch(self, request: Request, call_next):
        request.state.request_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests and responses."""
    
    async def dispatch(self, request: Request, call_next):
        # Skip logging for health checks and metrics
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)
        
        start_time = time.time()
        
        # We need a safe fallback if request_id isn't set yet
        request_id = getattr(request.state, "request_id", None)
        
        logger.info(f"Request started", extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else None,
            "event_type": "request_started"
        })
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        
        logger.info(f"Request completed", extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
            "event_type": "request_completed"
        })
        
        response.headers["X-Process-Time"] = str(duration)
        return response

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Handle and log unhandled exceptions."""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            request_id = getattr(request.state, "request_id", None)
            logger.error(f"Unhandled exception", extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "error": str(e),
                "event_type": "unhandled_exception"
            }, exc_info=True)
            
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "request_id": request_id
                }
            )
