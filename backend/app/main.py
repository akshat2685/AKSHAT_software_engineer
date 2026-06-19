"""
FastAPI application factory and configuration.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.utils.logger import setup_logging
from app.middleware import RequestIDMiddleware, LoggingMiddleware, ErrorHandlingMiddleware
from app.exceptions import AkshatException
from app.api.v2 import auth

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_client import Counter, Histogram
import time

# Setup logging
setup_logging()

def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="AKSHAT API",
        description="Autonomous Software Engineering Platform",
        version="2.0.0",
        debug=settings.DEBUG,
        docs_url="/api/docs",
        redoc_url="/api/redoc"
    )
    
    # Rate Limiting
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests"}
        )

    # Add middleware
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Exception handlers
    @app.exception_handler(AkshatException)
    async def akshat_exception_handler(request: Request, exc: AkshatException):
        return JSONResponse(
            status_code=400,
            content={
                "detail": exc.message,
                "code": exc.code,
                "details": exc.details,
                "request_id": getattr(request.state, 'request_id', None)
            }
        )
    
    # Health check
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "environment": settings.ENV}
    
    # Include routers
    app.include_router(auth.router, prefix="/api/v2/auth", tags=["auth"])
    
    return app

app = create_app()
