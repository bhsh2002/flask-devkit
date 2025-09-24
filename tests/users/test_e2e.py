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

    # Enable the 'list_deleted' route for the user entity for testing purposes
    custom_config = {"list_deleted": {"enabled": True, "permission": "is_super_admin"}}

    bp = APIBlueprint("api_v1", __name__, url_prefix="/api/v1")
    devkit = DevKit()
    devkit.register_routes_config("user", custom_config)
    devkit.init_app(app, bp)

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db_session(app):
    """
    Provides a transactional database session for each test.                                                        │
    Rolls back transactions automatically after each test.
    """
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()
        session = db.Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def user_service(db_session):
    """
    Fixture to create a UserService instance for each test.
    """
    from flask_devkit.users.services import UserService

    return UserService(model=User, db_session=db_session)


@pytest.fixture
def role_service(db_session):
    """
    Fixture to create a RoleService instance for each test.
    """
    from flask_devkit.users.services import RoleService

    return RoleService(model=Role, db_session=db_session)


def test_login_flow(client, db_session):
    with client.application.app_context():
        user = User(username="alice")
        user.set_password("a_good_password123")
        db_session.add(user)
        db_session.flush()

    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "alice", "password": "a_good_password123"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert "access_token" in data
    assert data["user"]["username"] == "alice"


def test_change_password_and_relogin(client, db_session):
    with client.application.app_context():
        u = User(username="dave")
        u.set_password("old_password123")
        db_session.add(u)
        db_session.flush()

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


def test_full_rbac_flow(client, db_session):
    with client.application.app_context():
        user = User(username="eve")
        user.set_password("a_good_password123")
        role = Role(name="manager", display_name="Manager")
        perm = Permission(name="create:thing")
        db_session.add_all([user, role, perm])
        db_session.flush()
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


def test_revoke_permissions_and_roles(client, db_session):
    with client.application.app_context():
        user = User(username="frank")
        user.set_password("a_good_password123")
        role = Role(name="temp_worker", display_name="Temp")
        perm = Permission(name="temp:access")
        db_session.add_all([user, role, perm])
        db_session.flush()
        user_uuid, role_id, perm_id = str(user.uuid), role.id, perm.id

        role.permissions.append(perm)
        user.roles.append(role)
        db_session.flush()

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


def test_system_role_protection(role_service, db_session):
    from flask_devkit.core.exceptions import BusinessLogicError

    sys_role = Role(name="system_role", display_name="System", is_system_role=True)
    db_session.add(sys_role)
    db_session.flush()

    # Attempt to delete the system role
    with pytest.raises(BusinessLogicError):
        role_service.delete(sys_role.id)

    # Attempt to rename the system role
    with pytest.raises(BusinessLogicError):
        role_service.update(sys_role.id, {"name": "new_name"})


def test_get_soft_deleted_users(client, db_session, user_service):
    """Tests that the GET /users/deleted endpoint returns only soft-deleted users."""
    with client.application.app_context():
        # Arrange
        active_user = User(username="active_user")
        active_user.set_password("password")
        deleted_user = User(username="deleted_user")
        deleted_user.set_password("password")
        admin_user = User(username="admin")
        admin_user.set_password("password")
        db_session.add_all([active_user, deleted_user, admin_user])
        db_session.flush()

        user_service.delete(deleted_user.uuid, id_field="uuid")
        db_session.flush()

        token = create_access_token(
            identity=admin_user.uuid, additional_claims={"is_super_admin": True}
        )

    headers = {"Authorization": f"Bearer {token}"}

    # Act
    resp = client.get("/api/v1/users/deleted", headers=headers)

    # Assert
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["pagination"]["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["username"] == "deleted_user"
    assert data["items"][0]["deleted_at"] is not None
