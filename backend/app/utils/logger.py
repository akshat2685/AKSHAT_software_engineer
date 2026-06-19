"""
Structured logging configuration.
Outputs JSON logs for easy parsing and analysis.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict
from pythonjsonlogger import jsonlogger
from app.config import settings

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""
    
    def add_fields(self, log_record: Dict[str, Any], record, message_dict):
        super().add_fields(log_record, record, message_dict)
        
        # Add custom fields
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['environment'] = settings.ENV
        log_record['service'] = 'akshat-backend'
        log_record['level'] = record.levelname
        
        # Add request ID if available (from context)
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id

def setup_logging():
    """Configure structured logging for the application."""
    
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Remove default handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    if settings.LOG_FORMAT == "json":
        formatter = CustomJsonFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if settings.ENV == "production":
        import os
        os.makedirs("logs", exist_ok=True)
        file_handler = logging.FileHandler('logs/akshat.log')
        file_handler.setLevel(logging.WARNING)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger

# Get logger instance
logger = logging.getLogger(__name__)

class LoggerMixin:
    """Mixin for classes that need logging capabilities."""
    
    @property
    def logger(self):
        return logging.getLogger(self.__class__.__name__)

class WorkflowLogger:
    """Specialized logger for workflow events."""
    
    @staticmethod
    def log_workflow_started(workflow_id: str, user_id: str, project_name: str):
        logger.info(f"Workflow started", extra={
            "workflow_id": workflow_id,
            "user_id": user_id,
            "project_name": project_name,
            "event_type": "workflow_started"
        })
    
    @staticmethod
    def log_agent_execution(workflow_id: str, agent_name: str, status: str, duration_ms: float):
        logger.info(f"Agent execution completed", extra={
            "workflow_id": workflow_id,
            "agent_name": agent_name,
            "status": status,
            "duration_ms": duration_ms,
            "event_type": "agent_execution"
        })
    
    @staticmethod
    def log_agent_error(workflow_id: str, agent_name: str, error: str, traceback: str = None):
        logger.error(f"Agent execution failed", extra={
            "workflow_id": workflow_id,
            "agent_name": agent_name,
            "error": error,
            "traceback": traceback,
            "event_type": "agent_error"
        })
    
    @staticmethod
    def log_workflow_completed(workflow_id: str, status: str, total_duration_ms: float):
        logger.info(f"Workflow completed", extra={
            "workflow_id": workflow_id,
            "status": status,
            "total_duration_ms": total_duration_ms,
            "event_type": "workflow_completed"
        })
