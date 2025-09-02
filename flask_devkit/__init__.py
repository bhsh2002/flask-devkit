# flask_devkit/__init__.py
from typing import Callable, Optional

from flask import Flask
from flask_jwt_extended import JWTManager

from flask_devkit.database import db
from flask_devkit.users.models import Permission, Role, User
from flask_devkit.users.services import PermissionService, RoleService, UserService


class DevKit:
    def __init__(
        self,
        app: Optional[Flask] = None,
        additional_claims_loader: Optional[Callable] = None,
    ):
        self.additional_claims_loader = additional_claims_loader
        self.user_service: Optional[UserService] = None
        self.role_service: Optional[RoleService] = None
        self.permission_service: Optional[PermissionService] = None

        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask):
        """Initialize the extension with the Flask app."""
        if not hasattr(app, "extensions"):
            app.extensions = {}
        app.extensions["devkit"] = self

        # Initialize db and jwt
        db.init_app(app)
        app.config["JWT_TOKEN_LOCATION"] = ["headers"]
        JWTManager(app)

        # Initialize services
        self.user_service = UserService(
            model=User,
            db_session=db.session,
            additional_claims_loader=self.additional_claims_loader,
        )
        self.role_service = RoleService(model=Role, db_session=db.session)
        self.permission_service = PermissionService(
            model=Permission, db_session=db.session
        )

        # Create and register blueprints
        self._register_blueprints(app)

    def _register_blueprints(self, app: Flask):
        """Register all blueprints for the auth system."""
        from flask_devkit.helpers.routing import (
            register_crud_routes,
            register_error_handlers,
        )
        from flask_devkit.users.routes import create_all_blueprints
        from flask_devkit.users.schemas import (
            permission_schemas,
            role_schemas,
            user_schemas,
        )

        auth_bp, users_bp, roles_bp, permissions_bp = create_all_blueprints()

        # Register CRUD routes for models
        register_crud_routes(
            bp=users_bp,
            service=self.user_service,
            schemas=user_schemas,
            entity_name="user",
            id_field="uuid",
        )
        register_crud_routes(
            bp=roles_bp,
            service=self.role_service,
            schemas=role_schemas,
            entity_name="role",
            id_field="id",
        )
        register_crud_routes(
            bp=permissions_bp,
            service=self.permission_service,
            schemas=permission_schemas,
            entity_name="permission",
            id_field="id",
        )

        # Register error handlers for all blueprints
        for bp in [auth_bp, users_bp, roles_bp, permissions_bp]:
            register_error_handlers(bp)

        # Register blueprints on the app
        app.register_blueprint(auth_bp)
        app.register_blueprint(users_bp)
        app.register_blueprint(roles_bp)
        app.register_blueprint(permissions_bp)
