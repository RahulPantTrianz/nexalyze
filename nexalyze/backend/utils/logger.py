"""
Production-Ready Logging Configuration
Provides structured logging with multiple handlers and formatters
"""

import logging
import sys
import json
from typing import Optional, Dict, Any
from datetime import datetime
from functools import wraps
import traceback
import asyncio
import time


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    Ideal for log aggregation systems like ELK, Datadog, etc.
    """
    
    def __init__(self, include_traceback: bool = True):
        super().__init__()
        self.include_traceback = include_traceback
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra_data') and record.extra_data:
            log_entry["extra"] = record.extra_data
        
        # Add exception info if present
        if record.exc_info and self.include_traceback:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info) if record.exc_info[0] else None
            }
        
        # Add request context if available
        for attr in ['request_id', 'user_id', 'session_id', 'correlation_id']:
            if hasattr(record, attr):
                log_entry[attr] = getattr(record, attr)
        
        return json.dumps(log_entry, default=str)


class ColoredFormatter(logging.Formatter):
    """
    Colored formatter for console output during development.
    """
    
    COLORS = {
        'DEBUG': '\033[94m',     # Blue
        'INFO': '\033[92m',      # Green
        'WARNING': '\033[93m',   # Yellow
        'ERROR': '\033[91m',     # Red
        'CRITICAL': '\033[95m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        
        # Format timestamp
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        # Build log message
        message = f"{color}[{timestamp}] {record.levelname:8}{self.RESET} | "
        message += f"{record.name:30} | {record.getMessage()}"
        
        # Add exception info if present
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"
        
        return message


class ContextLogger(logging.LoggerAdapter):
    """
    Logger adapter that adds context to log messages.
    Useful for request tracing and debugging.
    """
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        # Merge extra context
        extra = kwargs.get('extra', {})
        extra.update(self.extra)
        kwargs['extra'] = extra
        return msg, kwargs


def setup_logger(
    name: str,
    level: str = "INFO",
    log_format: str = "text",
    include_traceback: bool = True
) -> logging.Logger:
    """
    Setup a logger with appropriate handlers and formatters.
    
    Args:
        name: Logger name (usually __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Output format ('text' or 'json')
        include_traceback: Include full traceback in logs
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(getattr(logging, level.upper()))
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        
        # Choose formatter based on format type
        if log_format.lower() == 'json':
            formatter = JSONFormatter(include_traceback=include_traceback)
        else:
            formatter = ColoredFormatter()
        
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Prevent propagation to root logger
        logger.propagate = False
    
    return logger


def get_logger(name: str, context: Dict[str, Any] = None) -> logging.LoggerAdapter:
    """
    Get a logger with optional context.
    
    Args:
        name: Logger name
        context: Optional context dictionary (request_id, user_id, etc.)
    
    Returns:
        Logger adapter with context
    """
    from config.settings import settings
    
    logger = setup_logger(
        name,
        level=settings.log_level,
        log_format=settings.log_format
    )
    
    if context:
        return ContextLogger(logger, context)
    
    return logger


def log_execution_time(
    logger: logging.Logger = None,
    level: str = "INFO",
    threshold_ms: float = None
):
    """
    Decorator to log function execution time.
    
    Args:
        logger: Logger instance (creates one if not provided)
        level: Log level for timing messages
        threshold_ms: Only log if execution exceeds this threshold
    """
    def decorator(func):
        nonlocal logger
        if logger is None:
            logger = get_logger(func.__module__)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.time() - start_time) * 1000
                if threshold_ms is None or duration_ms >= threshold_ms:
                    getattr(logger, level.lower())(
                        f"{func.__name__} completed in {duration_ms:.2f}ms"
                    )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.time() - start_time) * 1000
                if threshold_ms is None or duration_ms >= threshold_ms:
                    getattr(logger, level.lower())(
                        f"{func.__name__} completed in {duration_ms:.2f}ms"
                    )
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def log_exceptions(
    logger: logging.Logger = None,
    reraise: bool = True,
    default_return: Any = None
):
    """
    Decorator to log exceptions with full context.
    
    Args:
        logger: Logger instance
        reraise: Whether to re-raise the exception
        default_return: Value to return if exception occurs and not re-raised
    """
    def decorator(func):
        nonlocal logger
        if logger is None:
            logger = get_logger(func.__module__)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.exception(
                    f"Exception in {func.__name__}: {type(e).__name__}: {str(e)}"
                )
                if reraise:
                    raise
                return default_return
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.exception(
                    f"Exception in {func.__name__}: {type(e).__name__}: {str(e)}"
                )
                if reraise:
                    raise
                return default_return
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


class LogContext:
    """
    Context manager for scoped logging with additional context.
    
    Usage:
        with LogContext(logger, {"request_id": "123", "user_id": "456"}):
            logger.info("This message includes context")
    """
    
    def __init__(self, logger: logging.Logger, context: Dict[str, Any]):
        self.logger = logger
        self.context = context
        self.original_factory = None
    
    def __enter__(self):
        self.original_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = self.original_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self.original_factory)
        return False


# ===========================================
# Pre-configured Loggers
# ===========================================

def get_api_logger() -> logging.Logger:
    """Get logger for API routes"""
    return get_logger("nexalyze.api")


def get_service_logger() -> logging.Logger:
    """Get logger for services"""
    return get_logger("nexalyze.services")


def get_db_logger() -> logging.Logger:
    """Get logger for database operations"""
    return get_logger("nexalyze.database")


def get_agent_logger() -> logging.Logger:
    """Get logger for AI agents"""
    return get_logger("nexalyze.agents")


# ===========================================
# Utility Functions
# ===========================================

def log_request(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    request_id: str = None
):
    """Log HTTP request with standard format"""
    prefix = f"[{request_id}] " if request_id else ""
    logger.info(f"{prefix}{method} {path} - {status_code} ({duration_ms:.2f}ms)")


def log_external_api_call(
    logger: logging.Logger,
    service_name: str,
    endpoint: str,
    status: str,
    duration_ms: float,
    error: str = None
):
    """Log external API call"""
    if error:
        logger.warning(
            f"External API [{service_name}] {endpoint} - {status} ({duration_ms:.2f}ms) - Error: {error}"
        )
    else:
        logger.info(
            f"External API [{service_name}] {endpoint} - {status} ({duration_ms:.2f}ms)"
        )


def log_database_operation(
    logger: logging.Logger,
    operation: str,
    table_or_collection: str,
    duration_ms: float,
    records_affected: int = None
):
    """Log database operation"""
    records_info = f" ({records_affected} records)" if records_affected is not None else ""
    logger.debug(
        f"DB [{operation}] {table_or_collection}{records_info} ({duration_ms:.2f}ms)"
    )
