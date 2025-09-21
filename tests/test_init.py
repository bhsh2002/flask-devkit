# tests/test_init.py
import pytest
from apiflask import APIFlask, APIBlueprint
from flask_devkit import DevKit
from flask_devkit.users.services import UserService

from unittest.mock import patch

import pytest
from apiflask import APIFlask

from flask_devkit import DevKit
from flask_devkit.core.repository import BaseRepository
from flask_devkit.users.models import User
from flask_devkit.users.services import UserService


@pytest.fixture
def app():
    """Provides a basic Flask app for initialization tests."""
    app = APIFlask(__name__)
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    # Add a dummy secret key for JWT
    app.config["JWT_SECRET_KEY"] = "test-secret"
    return app


# A mock service for testing purposes
class MockService:
    def __init__(self, name="mock"):
        self.name = name


def test_devkit_routes_config_override(app):
    """
    Tests that we can override the routes_config for a default service.
    This is expected to FAIL until the feature is implemented.
    """
    devkit = DevKit()

    # 1. Define a custom routes config
    custom_config = {"list": {"auth_required": False}}

    # 2. Register the override
    devkit.register_routes_config("user", custom_config)

    # 3. Patch the function that uses the config to check if it was passed
    with patch("flask_devkit.helpers.routing.register_crud_routes") as mock_register_crud:
        devkit.init_app(app)

        # 4. Assert that register_crud_routes was called with our custom config
        # We find the call for the 'user' service and inspect its kwargs.
        found_call = False
        for call in mock_register_crud.call_args_list:
            if call.kwargs.get("entity_name") == "user":
                assert call.kwargs.get("routes_config") == custom_config
                found_call = True
                break
        assert found_call, "register_crud_routes was not called for the user entity"


def test_devkit_default_service_with_custom_repo(app):
    """
    Tests that we can override the repository for a default service.
    """
    # 1. Define a custom repository that inherits from the base
    class CustomUserRepo(BaseRepository):
        def get_by_id(self, id_, include_soft_deleted=False):
            # Override to return a specific known object for the test
            user = User(id=id_, username="custom_repo_user")
            return user

    # 2. Instantiate DevKit and register the custom repo for the "user" service
    devkit = DevKit()
    devkit.register_repository("user", CustomUserRepo)

    # 3. Init the app. This should trigger default service loading,
    # but with our custom repo for the user service.
    devkit.init_app(app)

    # 4. Get the user service and check its behavior
    user_service = devkit.get_service("user")
    assert user_service is not None

    # This call should now be handled by our CustomUserRepo
    user = user_service.get_by_id(999)

    # 5. Assert that the custom repository was indeed used
    assert user.username == "custom_repo_user"


def test_devkit_lazy_initialization_with_defaults(app):
    """
    Tests that DevKit can be instantiated and then initialized,
    loading the default services automatically.
    """
    devkit = DevKit()
    # Services should not exist before init_app
    assert devkit.get_service("user") is None

    devkit.init_app(app)

    # Default services should be loaded
    assert isinstance(devkit.get_service("user"), UserService)
    assert devkit.get_service("role") is not None
    assert devkit.get_service("permission") is not None
    assert "devkit" in app.extensions

def test_devkit_selective_module_registration():
    """
    Tests that a developer can selectively register a custom service
    and the DevKit initializes only that one.
    """
    app = APIFlask(__name__)
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    # 1. Instantiate DevKit
    devkit = DevKit()

    # 2. Create and register a custom service
    mock_user_service = MockService(name="custom_user_service")
    devkit.register_service("user", mock_user_service)

    # 3. Initialize the app
    # Because we registered a service, the default services should NOT be loaded.
    devkit.init_app(app)

    # 4. Assert that our custom service is there
    retrieved_service = devkit.get_service("user")
    assert isinstance(retrieved_service, MockService)
    assert retrieved_service.name == "custom_user_service"

    # 5. Assert that other default services were NOT loaded
    assert devkit.get_service("role") is None
    assert devkit.get_service("permission") is None

def test_devkit_no_modules_registered():
    """
    Tests that if we register an empty set of services, nothing is loaded.
    """
    app = APIFlask(__name__)
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    devkit = DevKit()
    # By registering at least one service, we disable the default loading
    devkit.register_service("dummy", MockService())
    devkit.services.pop("dummy") # But then we remove it, leaving services empty

    devkit.init_app(app)

    assert devkit.get_service("user") is None
    assert devkit.get_service("role") is None
    assert devkit.get_service("permission") is None

def test_devkit_applies_loader_to_manual_user_service(app):
    """
    Tests that the additional_claims_loader is applied to a manually
    registered UserService instance.
    """
    # 1. Define a dummy loader
    def my_loader(user):
        return {"custom_claim": "is_present"}

    # 2. Init DevKit with the loader
    devkit = DevKit(additional_claims_loader=my_loader)

    # 3. Manually create and register a real UserService
    # We need an app context to get the db session
    with app.app_context():
        from flask_devkit.database import db

        user_service = UserService(model=User, db_session=db.session)
        devkit.register_service("user", user_service)

    # 4. Init the app, which should apply the loader
    devkit.init_app(app)

    # 5. Assert that the loader was set on the manually registered service
    manual_service = devkit.get_service("user")
    assert manual_service.additional_claims_loader is not None
    assert manual_service.additional_claims_loader == my_loader
