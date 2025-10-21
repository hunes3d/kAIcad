"""Error handling middleware for Flask application.

Provides centralized error handling with:
- Friendly user-facing error messages
- Server-side logging of full stack traces
- Structured error responses with error codes
- No leakage of internal implementation details
"""

from __future__ import annotations

import logging
from typing import Dict, Tuple

from flask import Flask, jsonify

logger = logging.getLogger(__name__)


# Error code definitions
class ErrorCode:
    """Standard error codes for API responses."""

    # General errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    INVALID_REQUEST = "INVALID_REQUEST"
    NOT_FOUND = "NOT_FOUND"
    
    # Authentication/Authorization
    UNAUTHORIZED = "UNAUTHORIZED"
    API_KEY_MISSING = "API_KEY_MISSING"
    API_KEY_INVALID = "API_KEY_INVALID"
    
    # Rate limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # Resource errors
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_READ_ERROR = "FILE_READ_ERROR"
    FILE_WRITE_ERROR = "FILE_WRITE_ERROR"
    
    # Model/AI errors
    MODEL_NOT_SUPPORTED = "MODEL_NOT_SUPPORTED"
    MODEL_VALIDATION_FAILED = "MODEL_VALIDATION_FAILED"
    PLAN_GENERATION_FAILED = "PLAN_GENERATION_FAILED"
    CHAT_FAILED = "CHAT_FAILED"
    
    # KiCad errors
    KICAD_CLI_NOT_FOUND = "KICAD_CLI_NOT_FOUND"
    KICAD_COMMAND_FAILED = "KICAD_COMMAND_FAILED"
    SCHEMATIC_PARSE_ERROR = "SCHEMATIC_PARSE_ERROR"
    
    # Validation errors
    VALIDATION_FAILED = "VALIDATION_FAILED"
    INVALID_INPUT = "INVALID_INPUT"


def create_error_response(
    error_code: str,
    message: str,
    status_code: int = 400,
    details: str | None = None,
) -> Tuple[Dict, int]:
    """Create a structured error response.

    Args:
        error_code: Machine-readable error code from ErrorCode class
        message: Human-friendly error message
        status_code: HTTP status code
        details: Optional additional details (only in development mode)

    Returns:
        Tuple of (response_dict, status_code)
    """
    response = {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
        },
    }
    
    # Only include details in development mode
    import os
    if details and os.getenv("FLASK_ENV") == "development":
        response["error"]["details"] = details
    
    return response, status_code


def register_error_handlers(app: Flask) -> None:
    """Register error handlers for the Flask application.

    Args:
        app: Flask application instance
    """

    @app.errorhandler(400)
    def bad_request(e):
        """Handle 400 Bad Request errors."""
        logger.warning(f"Bad request: {e}")
        return jsonify(create_error_response(
            ErrorCode.INVALID_REQUEST,
            "Invalid request. Please check your input.",
            400
        )[0]), 400

    @app.errorhandler(404)
    def not_found(e):
        """Handle 404 Not Found errors."""
        logger.warning(f"Not found: {e}")
        return jsonify(create_error_response(
            ErrorCode.NOT_FOUND,
            "The requested resource was not found.",
            404
        )[0]), 404

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        """Handle 429 Rate Limit Exceeded errors."""
        logger.warning(f"Rate limit exceeded: {e}")
        return jsonify(create_error_response(
            ErrorCode.RATE_LIMIT_EXCEEDED,
            "Too many requests. Please wait a moment before trying again.",
            429
        )[0]), 429

    @app.errorhandler(500)
    def internal_error(e):
        """Handle 500 Internal Server Error."""
        # Log full error with stack trace server-side only
        logger.error(f"Internal server error: {e}", exc_info=True)
        
        # Return friendly message to client
        return jsonify(create_error_response(
            ErrorCode.INTERNAL_ERROR,
            "An unexpected error occurred. Please try again later.",
            500
        )[0]), 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        """Catch-all handler for unexpected exceptions."""
        # Log full error with stack trace server-side only
        logger.error(f"Unexpected error: {e}", exc_info=True)
        
        # Return friendly message to client (never expose stack trace)
        return jsonify(create_error_response(
            ErrorCode.INTERNAL_ERROR,
            "An unexpected error occurred. Please try again later.",
            500
        )[0]), 500


# Public API
__all__ = [
    "ErrorCode",
    "create_error_response",
    "register_error_handlers",
]
