# tests/auth/test_decorators.py
import pytest
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager, create_access_token

from flask_devkit.auth.decorators import permission_required
from flask_devkit.core.exceptions import PermissionDeniedError


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "secret"
    JWTManager(app)

    @app.errorhandler(PermissionDeniedError)
    def handle_permission_denied(error):
        return jsonify(error.to_dict()), error.status_code

    @app.route("/protected")
    @permission_required("read:data")
    def protected_route():
        return jsonify(message="success"), 200

    return app


@pytest.fixture
def client(app):
    return app.test_client()


def test_permission_denied_without_token(client):
    response = client.get("/protected")
    assert response.status_code == 401


def test_permission_denied_with_wrong_permission(app, client):
    with app.app_context():
        access_token = create_access_token(
            identity="testuser", additional_claims={"permissions": ["write:data"]}
        )
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/protected", headers=headers)
    assert response.status_code == 403
    assert response.json["error_code"] == "PERMISSION_DENIED"


def test_permission_granted_with_correct_permission(app, client):
    with app.app_context():
        access_token = create_access_token(
            identity="testuser", additional_claims={"permissions": ["read:data"]}
        )
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/protected", headers=headers)
    assert response.status_code == 200


def test_permission_granted_for_super_admin(app, client):
    with app.app_context():
        access_token = create_access_token(
            identity="admin", additional_claims={"is_super_admin": True}
        )
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/protected", headers=headers)
    assert response.status_code == 200
