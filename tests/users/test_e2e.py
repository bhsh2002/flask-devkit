# tests/users/test_e2e.py
import pytest
from apiflask import APIBlueprint, APIFlask
from flask_jwt_extended import create_access_token

from flask_devkit import DevKit
from flask_devkit.database import db
from flask_devkit.users.models import Base, Permission, Role, User


@pytest.fixture
def app():
    app = APIFlask(__name__, spec_path="/openapi.json")
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["JWT_SECRET_KEY"] = "test-secret"
    app.config["SERVER_NAME"] = "localhost"

    bp = APIBlueprint("api_v1", __name__, url_prefix="/api/v1")
    DevKit(app, bp)


    with app.app_context():
        Base.metadata.create_all(db.engine)
        yield app
        Base.metadata.drop_all(db.engine)


@pytest.fixture
def client(app):
    return app.test_client()


def test_login_flow(client):
    with client.application.app_context():
        user = User(username="alice")
        user.set_password("a_good_password123")
        db.session.add(user)
        db.session.commit()

    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "alice", "password": "a_good_password123"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert "access_token" in data
    assert data["user"]["username"] == "alice"


def test_change_password_and_relogin(client):
    with client.application.app_context():
        u = User(username="dave")
        u.set_password("old_password123")
        db.session.add(u)
        db.session.commit()

    login_resp = client.post(
        "/api/v1/auth/login", json={"username": "dave", "password": "old_password123"}
    )
    token = login_resp.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    change_resp = client.post(
        "/api/v1/users/change-password",
        json={"current_password": "old_password123", "new_password": "new_password456"},
        headers=headers,
    )
    assert change_resp.status_code == 200

    relogin_resp = client.post(
        "/api/v1/auth/login", json={"username": "dave", "password": "new_password456"}
    )
    assert relogin_resp.status_code == 200


def test_full_rbac_flow(client):
    with client.application.app_context():
        user = User(username="eve")
        user.set_password("a_good_password123")
        role = Role(name="manager", display_name="Manager")
        perm = Permission(name="create:thing")
        db.session.add_all([user, role, perm])
        db.session.commit()
        user_uuid, role_id, perm_id = str(user.uuid), role.id, perm.id

        # Token must be created within app context
        token = create_access_token(
            identity=user_uuid,
            additional_claims={
                "is_super_admin": True,
                # Elevate permissions for testing RBAC assignments
            },
        )

    headers = {"Authorization": f"Bearer {token}"}

    # Assign role to user
    ar = client.post(
        f"/api/v1/roles/users/{user_uuid}", json={"role_id": role_id}, headers=headers
    )
    assert ar.status_code == 200

    # Assign permission to role
    pr = client.post(
        f"/api/v1/roles/{role_id}/permissions",
        json={"permission_id": perm_id},
        headers=headers,
    )
    assert pr.status_code == 200

    # List role permissions
    lp = client.get(f"/api/v1/roles/{role_id}/permissions", headers=headers)
    assert lp.status_code == 200
    assert any(p.get("name") == "create:thing" for p in lp.get_json())


def test_revoke_permissions_and_roles(client):
    with client.application.app_context():
        user = User(username="frank")
        user.set_password("a_good_password123")
        role = Role(name="temp_worker", display_name="Temp")
        perm = Permission(name="temp:access")
        db.session.add_all([user, role, perm])
        db.session.commit()
        user_uuid, role_id, perm_id = str(user.uuid), role.id, perm.id

        role.permissions.append(perm)
        user.roles.append(role)
        db.session.commit()

        token = create_access_token(
            identity=user_uuid, additional_claims={"is_super_admin": True}
        )

    headers = {"Authorization": f"Bearer {token}"}

    # Revoke permission from role
    revoke_perm_resp = client.delete(
        f"/api/v1/roles/{role_id}/permissions",
        json={"permission_id": perm_id},
        headers=headers,
    )
    assert revoke_perm_resp.status_code == 200

    # Verify permission is gone
    permissions_resp = client.get(
        f"/api/v1/roles/{role_id}/permissions", headers=headers
    )
    assert len(permissions_resp.get_json()) == 0

    # Revoke role from user
    revoke_role_resp = client.delete(
        f"/api/v1/roles/users/{user_uuid}", json={"role_id": role_id}, headers=headers
    )
    assert revoke_role_resp.status_code == 200

    # Verify role is gone
    roles_resp = client.get(f"/api/v1/roles/users/{user_uuid}", headers=headers)
    assert len(roles_resp.get_json()) == 0


def test_system_role_protection(client):
    with client.application.app_context():
        sys_role = Role(name="system_role", display_name="System", is_system_role=True)
        db.session.add(sys_role)
        db.session.commit()
        role_id = sys_role.id

        token = create_access_token(
            identity="admin", additional_claims={"is_super_admin": True}
        )

    headers = {"Authorization": f"Bearer {token}"}

    # Attempt to delete the system role
    delete_resp = client.delete(f"/api/v1/roles/{role_id}", headers=headers)
    assert delete_resp.status_code == 400  # BusinessLogicError
    assert delete_resp.get_json()["error_code"] == "BUSINESS_LOGIC_ERROR"

    # Attempt to rename the system role
    patch_resp = client.patch(
        f"/api/v1/roles/{role_id}",
        json={"name": "new_name", "display_name": "New Name"},
        headers=headers,
    )
    assert patch_resp.status_code == 400  # BusinessLogicError
    assert patch_resp.get_json()["error_code"] == "BUSINESS_LOGIC_ERROR"
