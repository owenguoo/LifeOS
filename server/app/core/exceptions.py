from fastapi import HTTPException
from typing import Optional, Dict, Any


class LifeOSException(Exception):
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(LifeOSException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_ERROR")


class AuthorizationError(LifeOSException):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, "AUTHORIZATION_ERROR")


class VideoProcessingError(LifeOSException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VIDEO_PROCESSING_ERROR", details)


class VectorStoreError(LifeOSException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VECTOR_STORE_ERROR", details)


class ExternalServiceError(LifeOSException):
    def __init__(self, service: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(f"{service} service error: {message}", f"{service.upper()}_ERROR", details)


def create_http_exception(
    status_code: int,
    message: str,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={
            "message": message,
            "error_code": error_code,
            "details": details or {}
        }
    )