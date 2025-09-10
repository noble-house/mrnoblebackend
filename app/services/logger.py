import structlog
import logging
import sys
from typing import Any, Dict
from datetime import datetime

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Configure standard library logging
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=logging.INFO,
)

def get_logger(name: str = None) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)

class LoggerMixin:
    """Mixin class to add logging capabilities to any class."""
    
    @property
    def logger(self) -> structlog.BoundLogger:
        """Get logger for this class."""
        return get_logger(self.__class__.__name__)

def log_api_call(
    method: str,
    path: str,
    status_code: int,
    response_time: float,
    user_email: str = None,
    **kwargs
):
    """Log API call details."""
    logger = get_logger("api")
    logger.info(
        "API call",
        method=method,
        path=path,
        status_code=status_code,
        response_time_ms=round(response_time * 1000, 2),
        user_email=user_email,
        **kwargs
    )

def log_auth_event(
    event_type: str,
    email: str = None,
    success: bool = True,
    **kwargs
):
    """Log authentication events."""
    logger = get_logger("auth")
    logger.info(
        "Auth event",
        event_type=event_type,
        email=email,
        success=success,
        **kwargs
    )

def log_business_event(
    event_type: str,
    entity_type: str,
    entity_id: int = None,
    **kwargs
):
    """Log business logic events."""
    logger = get_logger("business")
    logger.info(
        "Business event",
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        **kwargs
    )

def log_error(
    error: Exception,
    context: Dict[str, Any] = None,
    **kwargs
):
    """Log errors with context."""
    logger = get_logger("error")
    logger.error(
        "Error occurred",
        error_type=type(error).__name__,
        error_message=str(error),
        context=context or {},
        **kwargs
    )

def log_email_event(
    event_type: str,
    to_email: str,
    subject: str = None,
    message_id: str = None,
    **kwargs
):
    """Log email-related events."""
    logger = get_logger("email")
    logger.info(
        "Email event",
        event_type=event_type,
        to_email=to_email,
        subject=subject,
        message_id=message_id,
        **kwargs
    )

def log_interview_event(
    event_type: str,
    application_id: int = None,
    token: str = None,
    **kwargs
):
    """Log interview-related events."""
    logger = get_logger("interview")
    logger.info(
        "Interview event",
        event_type=event_type,
        application_id=application_id,
        token=token,
        **kwargs
    )
