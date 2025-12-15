from typing import Any, Dict, Optional
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
import logging

logger = logging.getLogger(__name__)

class BaseCustomException(Exception):
    """Base class for custom exceptions"""
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(message)

class ValidationError(BaseCustomException):
    """Raised when validation fails"""
    pass

class AuthenticationError(BaseCustomException):
    """Raised when authentication fails"""
    pass

class AuthorizationError(BaseCustomException):
    """Raised when authorization fails"""
    pass

class NotFoundError(BaseCustomException):
    """Raised when resource is not found"""
    pass

class ConflictError(BaseCustomException):
    """Raised when there's a conflict (e.g., duplicate resource)"""
    pass

class ExternalServiceError(BaseCustomException):
    """Raised when external service call fails"""
    pass

class DatabaseError(BaseCustomException):
    """Raised when database operation fails"""
    pass

class RateLimitError(BaseCustomException):
    """Raised when rate limit is exceeded"""
    pass

class WebSocketError(BaseCustomException):
    """Raised when WebSocket operation fails"""
    pass

# Exception handlers
async def custom_exception_handler(request: Request, exc: BaseCustomException):
    """Handler for custom exceptions"""
    status_code = 400
    
    # Map exception types to HTTP status codes
    if isinstance(exc, AuthenticationError):
        status_code = 401
    elif isinstance(exc, AuthorizationError):
        status_code = 403
    elif isinstance(exc, NotFoundError):
        status_code = 404
    elif isinstance(exc, ConflictError):
        status_code = 409
    elif isinstance(exc, RateLimitError):
        status_code = 429
    elif isinstance(exc, (ExternalServiceError, DatabaseError)):
        status_code = 503
    
    logger.error(f"Custom exception: {exc.error_code} - {exc.message}", extra={"details": exc.details})
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details
            },
            "path": str(request.url.path),
            "method": request.method
        }
    )

async def validation_exception_handler(request: Request, exc):
    """Handler for Pydantic validation errors"""
    logger.warning(f"Validation error: {exc}")
    
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": exc.errors() if hasattr(exc, 'errors') else str(exc)
            },
            "path": str(request.url.path),
            "method": request.method
        }
    )

async def http_exception_override_handler(request: Request, exc: HTTPException):
    """Enhanced HTTP exception handler"""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    
    # Use default handler but add more context
    response = await http_exception_handler(request, exc)
    
    # For 500 errors, provide more structured response
    if exc.status_code >= 500:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An internal server error occurred",
                    "details": {}
                },
                "path": str(request.url.path),
                "method": request.method
            }
        )
    
    return response

async def general_exception_handler(request: Request, exc: Exception):
    """Handler for unhandled exceptions"""
    logger.error(f"Unhandled exception: {type(exc).__name__} - {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "UNEXPECTED_ERROR",
                "message": "An unexpected error occurred",
                "details": {}
            },
            "path": str(request.url.path),
            "method": request.method
        }
    ) 