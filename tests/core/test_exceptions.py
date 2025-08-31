# tests/core/test_exceptions.py
import pytest

from flask_devkit.core.exceptions import (
    AppBaseException,
    NotFoundError,
    PermissionDeniedError,
)


def test_not_found_error_properties():
    """Tests that NotFoundError sets its properties correctly."""
    error = NotFoundError(entity_name="User", entity_id=123)
    assert error.status_code == 404
    assert error.error_code == "NOT_FOUND"
    assert "User with ID/identifier '123' not found" in error.message
    assert error.payload["entity"] == "User"
    assert error.payload["id"] == "123"


def test_to_dict_method():
    """Tests the to_dict method for proper serialization."""
    error = AppBaseException(
        message="A custom error",
        status_code=418,
        error_code="IM_A_TEAPOT",
        payload={"extra": "info"},
    )
    error_dict = error.to_dict()
    expected_dict = {
        "message": "A custom error",
        "error_code": "IM_A_TEAPOT",
        "details": {"extra": "info"},
    }
    assert error_dict == expected_dict


def test_raise_permission_denied():
    """Tests that a function correctly raises PermissionDeniedError."""

    def protected_function():
        raise PermissionDeniedError()

    with pytest.raises(PermissionDeniedError) as excinfo:
        protected_function()

    assert excinfo.value.status_code == 403
    assert "You do not have permission" in excinfo.value.message
