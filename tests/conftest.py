import pytest
from apiflask import APIFlask
from apiflask.fields import String
from flask_jwt_extended import create_access_token, JWTManager

from flask_devkit import DevKit
from flask_devkit.database import db as _db
from flask_devkit.helpers.schemas import create_crud_schemas
from flask_devkit.users.bootstrap import seed_default_auth
from flask_devkit.users.models import User
from flask_devkit.users.services import UserService


@pytest.fixture
def app():
    """Function-wide test Flask application."""
    _app = APIFlask(__name__)
    _app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "JWT_SECRET_KEY": "test-secret",
        }
    )

    # Initialize DevKit and other extensions
    DevKit(_app)

    with _app.app_context():
        _db.create_all()
        yield _app
        _db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """
    Provides a transactional database session for each test.
    Rolls back transactions automatically after each test.
    """
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()
        session = _db.Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def auth_headers(app, db_session):
    """Creates a user and returns JWT auth headers."""
    with app.app_context():
        user = User(username="testuser", is_active=True)
        user.set_password("password")
        db_session.add(user)

        access_token = create_access_token(identity=str(user.uuid))
        return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def admin_auth_headers(app, user_service):
    """Creates an admin user with all permissions and returns JWT auth headers."""
    with app.app_context():
        seed_results = seed_default_auth(
            session=user_service.repo._db_session,
            admin_username="admin",
            admin_password="password",
        )
        admin_user = user_service.repo.find_one_by(
            {"username": seed_results["admin_username"]}
        )

        # Generate token using the service to ensure all claims are loaded
        _, access_token, _ = user_service.login_user("admin", "password")
        return {"Authorization": f"Bearer {access_token}"}


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
    return UserService(model=User, db_session=db_session)
