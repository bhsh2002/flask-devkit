# tests/users/conftest.py
import pytest
from apiflask import APIFlask
from apiflask.fields import String
from flask_jwt_extended import JWTManager

from flask_devkit.helpers.schemas import create_crud_schemas
from flask_devkit.users.models import User
from flask_devkit.users.services import UserService


@pytest.fixture(scope="module")
def app():
    """Provides a minimal Flask app for tests that need an app context."""
    app = APIFlask(__name__)
    app.config["TESTING"] = True
    app.config["JWT_SECRET_KEY"] = "test-secret"
    JWTManager(app)
    return app


@pytest.fixture(scope="session")
def user_schemas():
    """
    Fixture to create user schemas once per test session.
    """
    return create_crud_schemas(
        User,
        custom_fields={"password": String(required=True, load_only=True)},
        exclude_from_main=["password_hash"],
        exclude_from_input=[
            "created_at",
            "updated_at",
            "deleted_at",
            "is_active",
            "last_login_at",
            "password_hash",
            "uuid",
        ],
        exclude_from_update=[
            "created_at",
            "updated_at",
            "deleted_at",
            "last_login_at",
            "password_hash",
            "uuid",
        ],
    )


@pytest.fixture
def user_service(db_session):
    """
    Fixture to create a UserService instance for each test.
    """
    # We need to create the tables for the user model for this session
    User.metadata.create_all(db_session.bind)
    yield UserService(model=User, db_session=db_session)
    User.metadata.drop_all(db_session.bind)
