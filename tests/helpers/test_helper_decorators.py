# tests/helpers/test_decorators.py
from unittest.mock import patch

import pytest
from apiflask import APIFlask
from flask import jsonify

from flask_devkit.helpers.decorators import log_activity, setup_rate_limiting


@pytest.fixture
def app():
    app = APIFlask(__name__)
    app.config["TESTING"] = True
    # For Flask-Limiter
    app.config["RATELIMIT_STORAGE_URI"] = "memory://"

    @app.route("/logged")
    @log_activity
    def logged_route():
        return jsonify(message="logged"), 200

    return app


@pytest.fixture
def client(app):
    return app.test_client()


def test_log_activity_decorator(app, client):
    with app.app_context():
        with patch("flask_devkit.helpers.decorators.current_app.logger") as mock_logger:
            client.get("/logged")
            assert mock_logger.info.call_count >= 2


def test_setup_rate_limiting(app):
    limiter = setup_rate_limiting(app, default_rate="1/minute")
    assert limiter is not None
    # Check if the extension is registered with the app
    assert "limiter" in app.extensions
