"""
Exception Handlers for FastAPI
Custom handlers for validation errors and other exceptions
"""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import uuid
from services.audit_logger import store_failed_request, extract_ack_from_request


def create_validation_exception_handler(app):
    """
    Create and register the validation exception handler for banks_v2 API
    
    Args:
        app: FastAPI app instance
    """
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """
        Custom handler to return validation errors in standardized format with response codes
        Only applies to banks_v2 endpoints for consistent API responses
        Stores all failed requests for audit purposes
        """
        # Check if this is a banks_v2 endpoint
        if "/api/v2/banks/" in str(request.url):
            errors = exc.errors()
            error_details = []
            
            for error in errors:
                field = " -> ".join(str(loc) for loc in error["loc"])
                error_details.append({
                    "field": field,
                    "error": error["msg"],
                    "invalid_value": error.get("input", "")
                })
            
            # Extract acknowledgement number from request body
            body_bytes = await request.body()
            ack_no, raw_body = extract_ack_from_request(body_bytes)
            
            # Store failed request for audit
            store_failed_request(
                ack_no=ack_no,
                raw_body=raw_body,
                failure_reason="Pydantic validation failed",
                failure_type="validation_error",
                error_details={"errors": error_details}
            )
            
            return JSONResponse(
                status_code=200,  # Return 200 for consistent API behavior
                content={
                    "meta": {
                        "response_code": "01",
                        "response_message": "Validation Error"
                    },
                    "data": {
                        "acknowledgement_no": ack_no,
                        "job_id": f"BANKS-{uuid.uuid4()}",
                        "error": "Request validation failed. Please check field formats.",
                        "validation_errors": error_details
                    }
                }
            )
        else:
            # For non-banks_v2 endpoints, return default FastAPI validation error
            return JSONResponse(
                status_code=422,
                content={"detail": exc.errors()}
            )
    
    return validation_exception_handler

