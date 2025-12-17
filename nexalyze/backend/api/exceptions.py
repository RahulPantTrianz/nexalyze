"""
Custom Exceptions and Error Handlers
Production-ready error handling for the API
"""

import traceback
import logging
import uuid
from typing import Any, Dict, Optional, List
from datetime import datetime

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


# ============================================================================
# Custom Exception Classes
# ============================================================================

class NexalyzeException(Exception):
    """Base exception for all Nexalyze errors"""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        details: List[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or []
        super().__init__(self.message)


class NotFoundError(NexalyzeException):
    """Resource not found"""
    
    def __init__(self, resource: str, identifier: Any = None):
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} with id '{identifier}' not found"
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND"
        )


class ValidationError(NexalyzeException):
    """Validation error"""
    
    def __init__(self, message: str, field: str = None):
        details = []
        if field:
            details.append({"field": field, "message": message})
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details=details
        )


class DatabaseError(NexalyzeException):
    """Database connection or query error"""
    
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="DATABASE_ERROR"
        )


class ExternalServiceError(NexalyzeException):
    """External service (API) error"""
    
    def __init__(self, service: str, message: str = None):
        msg = f"External service '{service}' unavailable"
        if message:
            msg = f"{msg}: {message}"
        super().__init__(
            message=msg,
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_code="EXTERNAL_SERVICE_ERROR"
        )


class RateLimitError(NexalyzeException):
    """Rate limit exceeded"""
    
    def __init__(self, retry_after: int = 60):
        super().__init__(
            message=f"Rate limit exceeded. Please retry after {retry_after} seconds.",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            details=[{"retry_after": retry_after}]
        )


class AuthenticationError(NexalyzeException):
    """Authentication failed"""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_ERROR"
        )


class AuthorizationError(NexalyzeException):
    """Authorization failed"""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTHORIZATION_ERROR"
        )


class ConfigurationError(NexalyzeException):
    """Configuration error"""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="CONFIGURATION_ERROR"
        )


class AIServiceError(NexalyzeException):
    """AI service (AWS Bedrock) error"""
    
    def __init__(self, message: str = "AI service temporarily unavailable"):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="AI_SERVICE_ERROR"
        )


class ReportGenerationError(NexalyzeException):
    """Report generation error"""
    
    def __init__(self, message: str = "Failed to generate report"):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="REPORT_GENERATION_ERROR"
        )


# ============================================================================
# Error Response Builder
# ============================================================================

def build_error_response(
    error: str,
    message: str,
    status_code: int,
    details: List[Dict[str, Any]] = None,
    request_id: str = None
) -> Dict[str, Any]:
    """Build standardized error response"""
    return {
        "error": error,
        "message": message,
        "details": details or [],
        "status_code": status_code,
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id or str(uuid.uuid4())
    }


# ============================================================================
# Exception Handlers
# ============================================================================

async def nexalyze_exception_handler(
    request: Request,
    exc: NexalyzeException
) -> JSONResponse:
    """Handle custom Nexalyze exceptions"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    logger.error(
        f"NexalyzeException: {exc.error_code} - {exc.message}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=build_error_response(
            error=exc.error_code,
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details,
            request_id=request_id
        )
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    details = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        details.append({
            "field": field,
            "message": error["msg"],
            "code": error["type"]
        })
    
    logger.warning(
        f"Validation error: {details}",
        extra={
            "request_id": request_id,
            "path": request.url.path
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=build_error_response(
            error="VALIDATION_ERROR",
            message="Request validation failed",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
            request_id=request_id
        )
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
) -> JSONResponse:
    """Handle HTTP exceptions"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    logger.error(
        f"HTTP {exc.status_code}: {exc.detail}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=build_error_response(
            error="HTTP_ERROR",
            message=str(exc.detail),
            status_code=exc.status_code,
            request_id=request_id
        )
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """Handle unhandled exceptions"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    # Log full traceback
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {exc}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc()
        },
        exc_info=True
    )
    
    # Don't expose internal error details in production
    from config.settings import settings
    
    message = "An unexpected error occurred"
    if settings.debug:
        message = f"{type(exc).__name__}: {str(exc)}"
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=build_error_response(
            error="INTERNAL_ERROR",
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            request_id=request_id
        )
    )


# ============================================================================
# Register Exception Handlers
# ============================================================================

def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI app"""
    
    # Custom exceptions
    app.add_exception_handler(NexalyzeException, nexalyze_exception_handler)
    
    # Validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # HTTP exceptions
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    
    # Generic exceptions (catch-all)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("Exception handlers registered")

