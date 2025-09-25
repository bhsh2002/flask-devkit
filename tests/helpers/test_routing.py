# tests/helpers/test_routing.py
import pytest
from unittest.mock import patch, MagicMock
from apiflask import APIBlueprint, APIFlask
from flask_jwt_extended import create_access_token
from sqlalchemy import Column, String
from apiflask.fields import String as StringField
from apiflask import Schema

from flask_devkit import DevKit
from flask_devkit.core.mixins import IDMixin, UUIDMixin
from flask_devkit.core.service import BaseService
from flask_devkit.database import db
from flask_devkit.helpers.routing import register_custom_route
from flask_devkit.helpers.schemas import create_crud_schemas


# 1. Define a test model and schemas
class Widget(db.Model, IDMixin, UUIDMixin):
    __tablename__ = "widgets"
    name = Column(String(50), nullable=False)


widget_schemas = create_crud_schemas(Widget)


@pytest.fixture
def app():
    app = APIFlask(__name__)
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["JWT_SECRET_KEY"] = "routing-secret"

    # We need a custom DevKit setup for this test to register a new model
    devkit = DevKit()
    devkit.init_app(app)

    # Manually initialize services for the test model
    widget_service = BaseService(model=Widget, db_session=db.session)

    # Register a new blueprint for the test model
    widget_bp = APIBlueprint("widgets", __name__, url_prefix="/widgets")
    from flask_devkit.helpers.routing import register_crud_routes

    register_crud_routes(
        bp=widget_bp,
        service=widget_service,
        schemas=widget_schemas,
        entity_name="widget",
        id_field="uuid",
        routes_config={
            "create": {"permission": "create:widget"},
            "update": {"permission": "update:widget"},
            "delete": {"permission": "delete:widget"},
            "list": {"auth_required": True},
            "get": {"auth_required": True},
        },
    )

    # register the custom blueprint
    app.register_blueprint(widget_bp)

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers(app):
    """Creates JWT auth headers with full permissions."""
    with app.app_context():
        claims = {"permissions": ["create:widget", "update:widget", "delete:widget"]}
        access_token = create_access_token(
            identity="test-user", additional_claims=claims
        )
    return {"Authorization": f"Bearer {access_token}"}


def test_create_and_get_widget(client, auth_headers):
    """Tests POST to create a widget and then GET to retrieve it."""
    create_resp = client.post(
        "/widgets/",
        json={"name": "MyWidget"},
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    assert create_resp.json["name"] == "MyWidget"
    widget_uuid = create_resp.json["uuid"]

    get_resp = client.get(f"/widgets/{widget_uuid}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json["name"] == "MyWidget"


def test_list_widgets(client, auth_headers):
    client.post("/widgets/", json={"name": "WidgetA"}, headers=auth_headers)
    client.post("/widgets/", json={"name": "WidgetB"}, headers=auth_headers)

    list_resp = client.get("/widgets/", headers=auth_headers)
    assert list_resp.status_code == 200
    assert list_resp.json["pagination"]["total"] == 2


def test_update_widget(client, auth_headers):
    create_resp = client.post(
        "/widgets/", json={"name": "Original"}, headers=auth_headers
    )
    widget_uuid = create_resp.json["uuid"]

    patch_resp = client.patch(
        f"/widgets/{widget_uuid}",
        json={"name": "Updated"},
        headers=auth_headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json["name"] == "Updated"


def test_delete_widget(client, auth_headers):
    create_resp = client.post(
        "/widgets/", json={"name": "ToDelete"}, headers=auth_headers
    )
    widget_uuid = create_resp.json["uuid"]

    del_resp = client.delete(f"/widgets/{widget_uuid}", headers=auth_headers)
    assert del_resp.status_code == 200

    get_resp = client.get(f"/widgets/{widget_uuid}", headers=auth_headers)
    assert get_resp.status_code == 404


def test_permission_denied_for_create(app, client):
    """Tests that a user without permissions gets a 403 error."""
    with app.app_context():
        # Token with no permissions
        access_token = create_access_token(identity="no-perms-user")
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client.post(
        "/widgets/",
        json={"name": "Illegal Widget"},
        headers=headers,
    )
    assert response.status_code == 403


def test_register_custom_route_applies_decorators():
    """
    Tests that register_custom_route correctly applies all decorators.
    This test will fail until the function is implemented.
    """
    bp = MagicMock(spec=APIBlueprint)
    view_func = MagicMock()

    # Mock the decorators to assert they are called
    with (
        patch("flask_devkit.helpers.routing.unit_of_work") as mock_uow,
        patch("flask_devkit.helpers.routing.permission_required") as mock_perm,
        patch("flask_devkit.helpers.routing.jwt_required") as mock_jwt,
    ):
        
        # Configure mocks to return a callable
        mock_uow.return_value = lambda f: f
        mock_perm.return_value = lambda f: f
        mock_jwt.return_value = lambda f: f

        register_custom_route(
            bp=bp,
            rule="/custom",
            view_func=view_func,
            methods=["POST"],
            apply_unit_of_work=True,
            permission="custom:perm",
            auth_required=True
        )

        # Assert that our decorators were called
        mock_uow.assert_called_once()
        mock_perm.assert_called_once_with("custom:perm")
        mock_jwt.assert_called_once()

        # Assert that the final decorated view was registered with the blueprint
        bp.route.assert_called_once_with("/custom", methods=["POST"])


class QuerySchema(Schema):
    param = StringField(required=True)

class BodySchema(Schema):
    data = StringField(required=True)

class OutputSchema(Schema):
    param = StringField()
    data = StringField()

def test_custom_route_with_multiple_schemas(app, client, auth_headers):
    custom_bp = APIBlueprint("custom", __name__, url_prefix="/custom")

    # 1. Define a simple view function without decorators
    def multi_input_view(query_args, body_args):
        """A view that takes input from query and body."""
        return {"param": query_args["param"], "data": body_args["data"]}

    # 2. Use the helper to register the route
    register_custom_route(
        bp=custom_bp,
        rule="/multi-registered",
        view_func=multi_input_view,
        methods=["POST"],
        auth_required=False, # Simplified for this test
        input_schemas=[
            {"schema": QuerySchema, "location": "query", "arg_name": "query_args"},
            {"schema": BodySchema, "location": "json", "arg_name": "body_args"},
        ],
        output_schema=OutputSchema,
    )

    app.register_blueprint(custom_bp)

    # 3. Make a request to the registered route
    response = client.post(
        "/custom/multi-registered?param=from_query",
        json={"data": "from_body"},
        headers=auth_headers,
    )

    # 4. Assert the response is correct
    assert response.status_code == 200
    assert response.json == {"param": "from_query", "data": "from_body"}


def test_fresh_token_required_returns_401(app, client):
    """Tests that a request to a fresh-token-required endpoint with a non-fresh token returns 401."""
    from flask_jwt_extended import jwt_required, create_access_token
    from apiflask import APIBlueprint
    from flask_devkit.helpers.routing import register_error_handlers

    # Create a dedicated blueprint for this test to ensure error handlers are registered
    test_bp = APIBlueprint("fresh_test", __name__, url_prefix="/fresh-test")
    register_error_handlers(test_bp) # Apply the handlers we want to test

    @test_bp.route("/protected")
    @jwt_required(fresh=True)
    def fresh_protected_route():
        return {"message": "success"}

    app.register_blueprint(test_bp)

    with app.app_context():
        # Create a non-fresh access token
        non_fresh_token = create_access_token(identity="test-user", fresh=False)
    
    headers = {"Authorization": f"Bearer {non_fresh_token}"}
    response = client.get("/fresh-test/protected", headers=headers)

    assert response.status_code == 401
    assert response.json["error_code"] == "FRESH_TOKEN_REQUIRED"



def test_expired_token_returns_401(app, client):
    """Tests that a request with an expired token returns a 401 error."""
    from datetime import timedelta
    with app.app_context():
        expired_token = create_access_token(
            identity="test-user", expires_delta=timedelta(seconds=-10)
        )
    
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get("/widgets/", headers=headers)

    assert response.status_code == 401
    assert response.json["error_code"] == "TOKEN_EXPIRED"