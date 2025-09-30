# flask_devkit/__init__.py
from typing import Callable, Dict, Optional, Type

from apiflask import APIBlueprint, APIFlask
from flask_jwt_extended import JWTManager

# Import default components that a user might want to use or extend
from flask_devkit.core.repository import BaseRepository
from flask_devkit.core.service import BaseService
from flask_devkit.database import db
from flask_devkit.users.models import Permission, Role, User
from flask_devkit.users.services import PermissionService, RoleService, UserService


class DevKit:
    def __init__(
        self,
        app: Optional[APIFlask] = None,
        additional_claims_loader: Optional[Callable] = None,
    ):
        self.additional_claims_loader = additional_claims_loader
        self.services: Dict[str, BaseService] = {}
        self.repository_overrides: Dict[str, Type[BaseRepository]] = {}
        self.routes_config_overrides: Dict[str, Dict] = {}
        self._services_manually_registered: bool = False

        if app is not None:
            self.init_app(app)

    def register_service(self, name: str, service: BaseService):
        """Registers a service instance with the DevKit."""
        self.services[name] = service
        self._services_manually_registered = True

    def get_service(self, name: str) -> Optional[BaseService]:
        """Gets a registered service by name."""
        return self.services.get(name)

    def register_repository(self, service_name: str, repo_class: Type[BaseRepository]):
        """Registers a custom repository class for a given default service."""
        self.repository_overrides[service_name] = repo_class

    def register_routes_config(self, service_name: str, config: Dict):
        """Registers a custom routes_config dictionary for a default service."""
        self.routes_config_overrides[service_name] = config

    def init_app(self, app: APIFlask, bp: Optional[APIBlueprint] = None):
        """Initialize the extension with the Flask app."""
        if not hasattr(app, "extensions"):
            app.extensions = {}
        app.extensions["devkit"] = self

        self._setup_app_config(app)

        if bp is None:
            url_prefix = app.config.get("DEVKIT_URL_PREFIX")
            bp = APIBlueprint("api_v1", __name__, url_prefix=url_prefix)

        db.init_app(app)
        JWTManager(app)

        # Initialize audit logging
        from flask_devkit import audit

        audit.init_app(app)

        # Initialize logging
        from flask_devkit import logging

        logging.init_app(app)

        # If no services are manually registered, register the defaults
        if not self._services_manually_registered:
            self._register_default_services()

        # Ensure loader is passed to user service, even if manually registered
        user_service = self.get_service("user")
        if user_service and self.additional_claims_loader:
            if hasattr(user_service, "additional_claims_loader"):
                user_service.additional_claims_loader = self.additional_claims_loader

        self._register_cli(app)
        self._register_blueprints(bp)

        app.register_blueprint(bp)

    def _register_default_services(self):
        """Registers the default services, using overrides if provided."""
        user_repo_cls = self.repository_overrides.get("user")
        role_repo_cls = self.repository_overrides.get("role")
        perm_repo_cls = self.repository_overrides.get("permission")

        self.register_service(
            "user",
            UserService(
                model=User,
                db_session=db.session,
                repository_class=user_repo_cls,
                additional_claims_loader=self.additional_claims_loader,
            ),
        )
        self.register_service(
            "role",
            RoleService(
                model=Role, db_session=db.session, repository_class=role_repo_cls
            ),
        )
        self.register_service(
            "permission",
            PermissionService(
                model=Permission,
                db_session=db.session,
                repository_class=perm_repo_cls,
            ),
        )

    def _setup_app_config(self, app: APIFlask):
        """Sets up default security schemes and JWT config."""
        app.config.setdefault("DEVKIT_URL_PREFIX", "/api/v1")

        security_schemes = {
            "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
        }
        existing_schemes = app.config.get("SECURITY_SCHEMES")
        if isinstance(existing_schemes, dict):
            existing_schemes.update(security_schemes)
            app.config["SECURITY_SCHEMES"] = existing_schemes
        else:
            app.config["SECURITY_SCHEMES"] = security_schemes
        app.config.setdefault("JWT_TOKEN_LOCATION", ["headers"])

    def _register_cli(self, app: APIFlask):
        """Register CLI commands."""
        from .core.cli import drop_db_command, init_db_command, truncate_db_command

        app.cli.add_command(init_db_command)
        app.cli.add_command(truncate_db_command)
        app.cli.add_command(drop_db_command)

        if self.get_service("user"):
            from .users.cli import main as seed_command

            app.cli.add_command(seed_command, "devkit-seed")

    def _register_blueprints(self, bp: APIBlueprint):
        """Register blueprints for all registered services."""
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

        if self.get_service("user"):
            user_routes_config = self.routes_config_overrides.get("user")
            auth_bp, users_bp, roles_bp, permissions_bp = create_all_blueprints(
                bp, routes_config=user_routes_config
            )

            register_crud_routes(
                bp=users_bp,
                service=self.get_service("user"),
                schemas=user_schemas,
                entity_name="user",
                id_field="uuid",
                routes_config=user_routes_config,
            )

            if self.get_service("role"):
                role_routes_config = self.routes_config_overrides.get("role")
                register_crud_routes(
                    bp=roles_bp,
                    service=self.get_service("role"),
                    schemas=role_schemas,
                    entity_name="role",
                    id_field="id",
                    routes_config=role_routes_config,
                )

            if self.get_service("permission"):
                perm_routes_config = self.routes_config_overrides.get("permission")
                register_crud_routes(
                    bp=permissions_bp,
                    service=self.get_service("permission"),
                    schemas=permission_schemas,
                    entity_name="permission",
                    id_field="id",
                    routes_config=perm_routes_config,
                )

            for sub_bp in [auth_bp, users_bp, roles_bp, permissions_bp]:
                register_error_handlers(sub_bp)
                bp.register_blueprint(sub_bp)
