"""
Tests for the application logging functionality.
"""
import pytest
from flask_devkit.database import db
from flask_devkit.users.models import User


def test_login_logging(caplog, db_session, user_service):
    from flask_devkit.core.exceptions import AuthenticationError
    with db_session.begin_nested():
        user = user_service.create({"username": "login_log_user", "password": "password123"})

    # Test a failed login attempt
    with caplog.at_level("WARNING"):
        with pytest.raises(AuthenticationError):
            user_service.login_user(username="login_log_user", password="wrongpassword")
        assert "Failed login attempt for username: login_log_user" in caplog.text

    caplog.clear()

    # Test a successful login
    with caplog.at_level("INFO"):
        user_service.login_user(username="login_log_user", password="password123")
        assert "User login_log_user logged in successfully" in caplog.text


def test_error_logging(client, caplog, admin_auth_headers):
    """Test that application and unhandled exceptions are logged."""
    # Test a 404 Not Found, which we log at INFO level
    with caplog.at_level("INFO"):
        response = client.get(
            "/api/v1/users/non_existent_uuid", headers=admin_auth_headers
        )
        assert response.status_code == 404
        assert "Resource not found" in caplog.text

    caplog.clear()

    # Test a 401 Unauthorized, which we log at WARNING
    with caplog.at_level("WARNING"):
        # Make a request with no auth headers
        response = client.get("/api/v1/users/")
        assert response.status_code == 401
        assert "Authorization missing for a request" in caplog.text


def test_init_app_handles_mkdir_race_condition(app, caplog):
    """Test that a FileExistsError race condition is handled gracefully."""
    import os
    from unittest.mock import patch
    from flask_devkit import logging

    app.debug = False
    app.testing = False

    # Simulate race condition: exists is false, but mkdir fails because another process created it
    with patch("os.path.exists", return_value=False):
        # os.makedirs will be called, which should handle the existing directory
        with caplog.at_level("ERROR"):
            logging.init_app(app)
            # No error should be logged because exist_ok=True handles this
            assert not caplog.text

