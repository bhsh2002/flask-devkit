# tests/users/test_permissions.py
import pytest
from apiflask import APIFlask
from flask_jwt_extended import create_access_token

from flask_devkit import DevKit
from flask_devkit.database import db
from flask_devkit.users.models import Base, Role, User


@pytest.fixture
def app():
    app = APIFlask(__name__)
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["JWT_SECRET_KEY"] = "test-secret"
    DevKit(app)
    with app.app_context():
        Base.metadata.create_all(db.engine)
        yield app
        Base.metadata.drop_all(db.engine)


@pytest.fixture
def client(app):
    return app.test_client()


def auth_header(app, identity: str, perms: list[str] | None = None):
    with app.app_context():
        token = create_access_token(
            identity=identity, additional_claims={"permissions": perms or []}
        )
    return {"Authorization": f"Bearer {token}"}


def test_assign_role_forbidden_without_permission(app, client):
    with client.application.app_context():
        user = User(username="nope")
        user.set_password("a_good_password123")
        role = Role(name="viewer", display_name="Viewer")
        db.session.add_all([user, role])
        db.session.commit()
        user_uuid, role_id = str(user.uuid), role.id

    headers = auth_header(
        app, identity=user_uuid, perms=["read:user"]
    )  # missing assign_role:user
    resp = client.post(
        f"/roles/users/{user_uuid}", json={"role_id": role_id}, headers=headers
    )
    assert resp.status_code == 403
