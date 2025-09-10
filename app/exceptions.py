from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from app.services.logger import log_error
from app.schemas import ErrorResponse
from datetime import datetime

class MrNobleException(Exception):
    """Base exception for MrNoble application."""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class BusinessLogicError(MrNobleException):
    """Exception for business logic violations."""
    pass

class DataIntegrityError(MrNobleException):
    """Exception for data integrity violations."""
    pass

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        errors.append(f"{field}: {error['msg']}")
    
    error_message = "Validation error: " + "; ".join(errors)
    
    log_error(exc, context={
        "operation": "validation_error",
        "path": str(request.url.path),
        "method": request.method,
        "errors": errors
    })
    
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            detail=error_message,
            error_code="VALIDATION_ERROR"
        ).dict()
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    log_error(exc, context={
        "operation": "http_error",
        "path": str(request.url.path),
        "method": request.method,
        "status_code": exc.status_code
    })
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            detail=exc.detail,
            error_code=f"HTTP_{exc.status_code}"
        ).dict()
    )

async def mrnoble_exception_handler(request: Request, exc: MrNobleException):
    """Handle custom MrNoble exceptions."""
    log_error(exc, context={
        "operation": "business_error",
        "path": str(request.url.path),
        "method": request.method,
        "error_code": exc.error_code
    })
    
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            detail=exc.message,
            error_code=exc.error_code or "BUSINESS_ERROR"
        ).dict()
    )

async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    log_error(exc, context={
        "operation": "unhandled_error",
        "path": str(request.url.path),
        "method": request.method
    })
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            detail="An internal server error occurred",
            error_code="INTERNAL_ERROR"
        ).dict()
    )
