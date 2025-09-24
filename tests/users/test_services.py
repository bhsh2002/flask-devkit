# tests/users/test_services.py
import pytest

from flask_devkit.core.exceptions import (
    AuthenticationError,
    BusinessLogicError,
    NotFoundError,
)
from flask_devkit.users.models import Permission, Role, User
from flask_devkit.users.services import PermissionService, RoleService

# The user_service fixture is injected from tests/users/conftest.py


def test_create_user_persists_data(db_session, user_service):
    user_data = {"username": "testuser", "password": "a_good_password123"}
    created_user = user_service.create(user_data)
    db_session.commit()

    assert created_user.id is not None
    assert created_user.username == "testuser"
    assert created_user.password_hash is not None

    fetched_user = db_session.query(User).filter_by(id=created_user.id).one()
    assert fetched_user is not None
    assert fetched_user.username == "testuser"


def test_get_user_by_id(db_session, user_service):
    user_data = {"username": "get_user", "password": "a_good_password123"}
    created_user = user_service.create(user_data)
    db_session.commit()

    fetched_user = user_service.get_by_id(created_user.id)
    assert fetched_user is not None
    assert fetched_user.id == created_user.id


def test_update_user(db_session, user_service):
    user_data = {"username": "original_name", "password": "a_good_password123"}
    created_user = user_service.create(user_data)
    db_session.commit()
    user_id = created_user.id

    update_data = {"username": "updated_name"}
    updated_user = user_service.update(entity_id=user_id, data=update_data)
    db_session.commit()

    assert updated_user is not None
    assert updated_user.id == user_id
    assert updated_user.username == "updated_name"


def test_update_nonexistent_user_raises_error(user_service):
    with pytest.raises(NotFoundError):
        user_service.update(entity_id=9999, data={"username": "ghost_user"})


def test_create_user_with_duplicate_username_raises_error(db_session, user_service):
    user_data = {"username": "duplicate", "password": "a_good_password123"}
    user_service.create(user_data)
    db_session.commit()

    with pytest.raises(BusinessLogicError, match="Username already exists."):
        user_service.create(user_data)


def test_password_strength_validation(user_service):
    with pytest.raises(BusinessLogicError, match="at least 8 characters long"):
        user_service.create({"username": "user1", "password": "short"})

    with pytest.raises(BusinessLogicError, match="letters and numbers"):
        user_service.create({"username": "user2", "password": "onlyletters"})

    # This should pass
    user_service.create({"username": "user3", "password": "a_good_password123"})


# --- Tests for Login ---
def test_login_user_success(app, db_session, user_service):
    with app.app_context():
        user_data = {"username": "login_user", "password": "a_good_password123"}
        user_service.create(user_data)
        db_session.commit()

        user, access_token, refresh_token = user_service.login_user(
            "login_user", "a_good_password123"
        )
        assert user is not None
        assert access_token is not None
        assert refresh_token is not None
        assert user.username == "login_user"


def test_login_user_invalid_credentials(db_session, user_service):
    user_data = {"username": "login_fail", "password": "a_good_password123"}
    user_service.create(user_data)
    db_session.commit()

    with pytest.raises(AuthenticationError, match="Invalid credentials"):
        user_service.login_user("login_fail", "wrong_password")


# --- Tests for Change Password ---
def test_change_password(app, db_session, user_service):
    with app.app_context():
        user_data = {"username": "changepw", "password": "old_password123"}
        user = user_service.create(user_data)
        db_session.commit()

        user_service.change_password(user.uuid, "old_password123", "new_password456")
        db_session.commit()

        # Try to login with the new password
        user, _, _ = user_service.login_user("changepw", "new_password456")
        assert user is not None


# --- Tests for RoleService and PermissionService ---
@pytest.fixture
def role_permission_services(app, db_session):
    with app.app_context():
        from flask_devkit.users.models import Base

    
        yield (
            RoleService(model=Role, db_session=db_session),
            PermissionService(model=Permission, db_session=db_session),
        )
        Base.metadata.drop_all(db_session.bind)


def test_assign_and_get_roles(app, db_session, user_service, role_permission_services):
    with app.app_context():
        role_service, _ = role_permission_services
        user = user_service.create(
            {"username": "role_user", "password": "a_good_password123"}
        )
        assigner = user_service.create(
            {"username": "role_assigner", "password": "a_good_password123"}
        )
        db_session.commit()

        role = role_service.create({"name": "editor", "display_name": "Editor"})
        db_session.commit()

        role_service.assign_role(user, role, assigner.id)
        db_session.commit()

        user_roles = role_service.get_roles_for_user(user)
        assert len(user_roles) == 1
        assert user_roles[0].name == "editor"


# --- Tests for Schemas Coverage ---
def test_login_schema_loads():
    from flask_devkit.users.schemas import LoginSchema

    data = {"username": "u", "password": "p"}
    assert LoginSchema().load(data)


def test_change_password_schema_loads():
    from flask_devkit.users.schemas import ChangePasswordSchema

    data = {"current_password": "p", "new_password": "p2"}
    assert ChangePasswordSchema().load(data)
