# flask_devkit/core/exceptions.py
from typing import Any


class AppBaseException(Exception):
    """The base exception class for all custom exceptions in the application.

    This class provides a consistent structure for handling errors, including
    an HTTP status code, a message, a unique error code, and an optional
    payload for extra details.
    """

    status_code: int = 500
    message: str = "An unexpected error occurred."
    error_code: str = "UNEXPECTED_ERROR"

    def __init__(
        self,
        message: str | None = None,
        status_code: int | None = None,
        error_code: str | None = None,
        payload: Any = None,
    ):
        """Initializes the base exception.

        Args:
            message (str, optional): The error message. Defaults to the class default.
            status_code (int, optional): The HTTP status code.
              Defaults to the class default.
            error_code (str, optional): A unique string identifying the error type.
            payload (Any, optional): Any extra data to attach to the error response.
        """
        super().__init__(message or self.message)
        if message is not None:
            self.message = message
        if status_code is not None:
            self.status_code = status_code
        if error_code is not None:
            self.error_code = error_code
        self.payload = payload

    def to_dict(self) -> dict:
        """Converts the exception into a serializable dictionary."""
        rv = {"message": self.message, "error_code": self.error_code}
        if self.payload:
            rv["details"] = self.payload
        return rv


class NotFoundError(AppBaseException):
    """Raised when a requested resource could not be found."""

    status_code = 404
    error_code = "NOT_FOUND"

    def __init__(self, entity_name: str, entity_id: Any, message: str | None = None):
        super().__init__(
            message or f"{entity_name} with ID/identifier '{entity_id}' not found.",
            status_code=404,
            error_code=self.error_code,
            payload={"entity": entity_name, "id": str(entity_id)},
        )


class DuplicateEntryError(AppBaseException):
    """Raised when an attempt to create a resource violates a uniqueness constraint."""

    status_code = 409  # Conflict
    error_code = "DUPLICATE_ENTRY"

    def __init__(self, message: str = "A database entry with the given value already exists.", original_exception: Exception | None = None):
        super().__init__(message, status_code=409, error_code=self.error_code)
        self.original_exception = original_exception


class BusinessLogicError(AppBaseException):
    """Raised for general business logic violations that
    are not covered by other exceptions."""

    status_code = 400
    error_code = "BUSINESS_LOGIC_ERROR"

    def __init__(
        self, message: str, status_code: int = 400, error_code: str | None = None
    ):
        super().__init__(
            message, status_code=status_code, error_code=error_code or self.error_code
        )


class AuthenticationError(AppBaseException):
    """Raised when authentication credentials are not provided or are invalid."""

    status_code = 401
    error_code = "AUTHENTICATION_FAILED"

    def __init__(self, message: str = "Authentication failed."):
        super().__init__(message, status_code=401, error_code=self.error_code)


class InvalidTokenError(AuthenticationError):
    """Raised when a provided token is invalid, malformed, or expired."""

    error_code = "INVALID_TOKEN"

    def __init__(self, message: str = "Invalid or expired token."):
        # Note: Inherits status_code=401 from AuthenticationError
        super().__init__(message=message)


class PermissionDeniedError(AppBaseException):
    """Raised when an authenticated user tries
    to access a resource without permission."""

    status_code = 403
    error_code = "PERMISSION_DENIED"

    def __init__(
        self, message: str = "You do not have permission to perform this action."
    ):
        super().__init__(message, status_code=403, error_code=self.error_code)


class DatabaseError(AppBaseException):
    """Raised for database-related errors, wrapping the original exception."""

    status_code = 500
    error_code = "DATABASE_ERROR"

    def __init__(
        self,
        message: str = "A database error occurred.",
        original_exception: Exception | None = None,
    ):
        super().__init__(message, status_code=500, error_code=self.error_code)
        self.original_exception = original_exception
