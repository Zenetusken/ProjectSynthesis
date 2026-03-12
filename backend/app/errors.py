"""Standardized HTTP error response factories.

All error responses follow the format: {"code": "ERROR_CODE", "message": "..."}
Optional extra fields can be included for context.

Usage:
    from app.errors import bad_request, not_found
    raise bad_request("Invalid input")
    raise not_found("Optimization not found")
"""

from fastapi import HTTPException


def bad_request(message: str, code: str = "BAD_REQUEST", **extra) -> HTTPException:
    """400 Bad Request."""
    return HTTPException(status_code=400, detail={"code": code, "message": message, **extra})


def unauthorized(message: str, code: str = "UNAUTHORIZED", **extra) -> HTTPException:
    """401 Unauthorized."""
    return HTTPException(status_code=401, detail={"code": code, "message": message, **extra})


def forbidden(message: str, code: str = "FORBIDDEN", **extra) -> HTTPException:
    """403 Forbidden."""
    return HTTPException(status_code=403, detail={"code": code, "message": message, **extra})


def not_found(message: str, code: str = "NOT_FOUND", **extra) -> HTTPException:
    """404 Not Found."""
    return HTTPException(status_code=404, detail={"code": code, "message": message, **extra})


def conflict(message: str, code: str = "CONFLICT", **extra) -> HTTPException:
    """409 Conflict."""
    return HTTPException(status_code=409, detail={"code": code, "message": message, **extra})


def rate_limited(message: str, code: str = "RATE_LIMIT_EXCEEDED", **extra) -> HTTPException:
    """429 Too Many Requests."""
    return HTTPException(status_code=429, detail={"code": code, "message": message, **extra})


def internal_server_error(message: str, code: str = "INTERNAL_SERVER_ERROR", **extra) -> HTTPException:
    """500 Internal Server Error."""
    return HTTPException(status_code=500, detail={"code": code, "message": message, **extra})


def bad_gateway(message: str, code: str = "BAD_GATEWAY", **extra) -> HTTPException:
    """502 Bad Gateway."""
    return HTTPException(status_code=502, detail={"code": code, "message": message, **extra})


def service_unavailable(message: str, code: str = "SERVICE_UNAVAILABLE", **extra) -> HTTPException:
    """503 Service Unavailable."""
    return HTTPException(status_code=503, detail={"code": code, "message": message, **extra})
