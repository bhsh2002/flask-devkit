# flask_devkit/users/routes.py
from apiflask import APIBlueprint
from flask import current_app, g
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from flask_devkit.helpers.routing import register_custom_route
from flask_devkit.helpers.schemas import MessageSchema
from flask_devkit.users.schemas import (
    AssignRoleSchema,
    AuthTokenSchema,
    ChangePasswordSchema,
    LoginSchema,
    PermissionIdSchema,
    permission_schemas,
    role_schemas,
    user_schemas,
)


def create_all_blueprints(bp: APIBlueprint, routes_config=None):
    routes_config = routes_config or {}

    def is_route_enabled(route_name):
        return routes_config.get(route_name, {}).get("enabled", True)

    auth_bp = APIBlueprint("auth", __name__, url_prefix="/auth")
    users_bp = APIBlueprint("user", __name__, url_prefix="/users")
    roles_bp = APIBlueprint("role", __name__, url_prefix="/roles")
    permissions_bp = APIBlueprint("permission", __name__, url_prefix="/permissions")

    @bp.before_request
    def before_request():
        g.devkit = current_app.extensions["devkit"]

    # Auth Routes
    if is_route_enabled("login"):
        route_cfg = routes_config.get("login", {})

        def login(json_data):
            user, access_token, refresh_token = g.devkit.get_service(
                "user"
            ).login_user(
                username=json_data["username"], password=json_data["password"]
            )
            return {
                "user": user,
                "access_token": access_token,
                "refresh_token": refresh_token,
            }

        register_custom_route(
            auth_bp,
            rule=route_cfg.get("rule", "/login"),
            view_func=login,
            methods=route_cfg.get("methods", ["POST"]),
            input_schemas=route_cfg.get(
                "input_schemas", [{"schema": LoginSchema, "location": "json"}]
            ),
            output_schema=route_cfg.get("output_schema", AuthTokenSchema),
            doc=route_cfg.get("doc", {"summary": "User Login"}),
            apply_unit_of_work=route_cfg.get("apply_unit_of_work", True),
            auth_required=route_cfg.get("auth_required", False),
            permission=route_cfg.get("permission"),
            decorators=route_cfg.get("decorators"),
        )

    if is_route_enabled("whoami"):
        route_cfg = routes_config.get("whoami", {})

        def whoami():
            user_uuid = get_jwt_identity()
            return g.devkit.get_service("user").get_by_uuid(user_uuid)

        register_custom_route(
            auth_bp,
            rule=route_cfg.get("rule", "/me"),
            view_func=whoami,
            methods=route_cfg.get("methods", ["GET"]),
            output_schema=route_cfg.get("output_schema", user_schemas["main"]),
            doc=route_cfg.get("doc", {"summary": "Current Authenticated User"}),
            auth_required=route_cfg.get("auth_required", True),
            permission=route_cfg.get("permission"),
            decorators=route_cfg.get("decorators"),
        )

    if is_route_enabled("refresh"):
        route_cfg = routes_config.get("refresh", {})

        def refresh():
            user_uuid = get_jwt_identity()
            new_access = g.devkit.get_service(
                "user"
            ).generate_fresh_token_for_identity(user_uuid)
            return {"access_token": new_access}

        register_custom_route(
            auth_bp,
            rule=route_cfg.get("rule", "/refresh"),
            view_func=refresh,
            methods=route_cfg.get("methods", ["POST"]),
            output_schema=route_cfg.get("output_schema", AuthTokenSchema),
            doc=route_cfg.get("doc", {"summary": "Refresh Access Token"}),
            auth_required=route_cfg.get("auth_required", False),
            decorators=route_cfg.get("decorators", [jwt_required(refresh=True)]),
            permission=route_cfg.get("permission"),
        )

    # User Routes
    if is_route_enabled("change_password"):
        route_cfg = routes_config.get("change_password", {})

        def change_password(json_data):
            user_uuid = get_jwt_identity()
            g.devkit.get_service("user").change_password(
                user_uuid=user_uuid,
                current_password=json_data["current_password"],
                new_password=json_data["new_password"],
            )
            return {"message": "Password changed successfully"}

        register_custom_route(
            users_bp,
            rule=route_cfg.get("rule", "/change-password"),
            view_func=change_password,
            methods=route_cfg.get("methods", ["POST"]),
            input_schemas=route_cfg.get(
                "input_schemas", [{"schema": ChangePasswordSchema, "location": "json"}]
            ),
            output_schema=route_cfg.get("output_schema", MessageSchema),
            doc=route_cfg.get("doc", {"summary": "Change current user's password"}),
            apply_unit_of_work=route_cfg.get("apply_unit_of_work", True),
            auth_required=route_cfg.get("auth_required", True),
            permission=route_cfg.get("permission"),
            decorators=route_cfg.get("decorators"),
        )

    # Role Routes
    if is_route_enabled("assign_role"):
        route_cfg = routes_config.get("assign_role", {})

        def assign_role(user_uuid, json_data):
            role_id = json_data["role_id"]
            claims = get_jwt()
            current_user_id = claims.get("user_id")
            user_service = g.devkit.get_service("user")
            role_service = g.devkit.get_service("role")
            user = user_service.get_by_uuid(user_uuid)
            role = role_service.get_by_id(role_id)
            role_service.assign_role(
                user=user, role=role, assigned_by_user_id=current_user_id
            )
            return {"message": "Role assigned successfully"}

        register_custom_route(
            roles_bp,
            rule=route_cfg.get("rule", "/users/<string:user_uuid>"),
            view_func=assign_role,
            methods=route_cfg.get("methods", ["POST"]),
            input_schemas=route_cfg.get(
                "input_schemas", [{"schema": AssignRoleSchema, "location": "json"}]
            ),
            output_schema=route_cfg.get("output_schema", MessageSchema),
            doc=route_cfg.get("doc", {"summary": "Assign Role To User"}),
            permission=route_cfg.get("permission", "assign_role:user"),
            apply_unit_of_work=route_cfg.get("apply_unit_of_work", True),
            auth_required=route_cfg.get("auth_required", True),
            decorators=route_cfg.get("decorators"),
        )

    if is_route_enabled("list_user_roles"):
        route_cfg = routes_config.get("list_user_roles", {})

        def list_user_roles(user_uuid):
            user_service = g.devkit.get_service("user")
            role_service = g.devkit.get_service("role")
            user = user_service.get_by_uuid(user_uuid)
            return role_service.get_roles_for_user(user)

        register_custom_route(
            roles_bp,
            rule=route_cfg.get("rule", "/users/<string:user_uuid>"),
            view_func=list_user_roles,
            methods=route_cfg.get("methods", ["GET"]),
            output_schema=route_cfg.get(
                "output_schema", role_schemas["main"](many=True)
            ),
            doc=route_cfg.get("doc", {"summary": "List Roles Assigned To User"}),
            permission=route_cfg.get("permission", "read_roles:user"),
            auth_required=route_cfg.get("auth_required", True),
            decorators=route_cfg.get("decorators"),
        )

    if is_route_enabled("revoke_role"):
        route_cfg = routes_config.get("revoke_role", {})

        def revoke_role(user_uuid, json_data):
            role_id = json_data["role_id"]
            user_service = g.devkit.get_service("user")
            role_service = g.devkit.get_service("role")
            user = user_service.get_by_uuid(user_uuid)
            role = role_service.get_by_id(role_id)
            role_service.revoke_role(user=user, role=role)
            return {"message": "Role revoked successfully"}

        register_custom_route(
            roles_bp,
            rule=route_cfg.get("rule", "/users/<string:user_uuid>"),
            view_func=revoke_role,
            methods=route_cfg.get("methods", ["DELETE"]),
            input_schemas=route_cfg.get(
                "input_schemas", [{"schema": AssignRoleSchema, "location": "json"}]
            ),
            output_schema=route_cfg.get("output_schema", MessageSchema),
            doc=route_cfg.get("doc", {"summary": "Revoke Role From User"}),
            permission=route_cfg.get("permission", "revoke_role:user"),
            apply_unit_of_work=route_cfg.get("apply_unit_of_work", True),
            auth_required=route_cfg.get("auth_required", True),
            decorators=route_cfg.get("decorators"),
        )

    # Permission Routes
    if is_route_enabled("list_role_permissions"):
        route_cfg = routes_config.get("list_role_permissions", {})

        def list_role_permissions(role_id: int):
            return g.devkit.get_service("permission").list_role_permissions(role_id)

        register_custom_route(
            roles_bp,
            rule=route_cfg.get("rule", "/<int:role_id>/permissions"),
            view_func=list_role_permissions,
            methods=route_cfg.get("methods", ["GET"]),
            output_schema=route_cfg.get(
                "output_schema", permission_schemas["main"](many=True)
            ),
            doc=route_cfg.get("doc", {"summary": "List Permissions For Role"}),
            permission=route_cfg.get("permission", "read_permissions:role"),
            auth_required=route_cfg.get("auth_required", True),
            decorators=route_cfg.get("decorators"),
        )

    if is_route_enabled("assign_permission_to_role"):
        route_cfg = routes_config.get("assign_permission_to_role", {})

        def assign_permission(role_id: int, json_data):
            g.devkit.get_service("permission").assign_permission_to_role(
                role_id, json_data["permission_id"]
            )
            return {"message": "Permission assigned to role"}

        register_custom_route(
            roles_bp,
            rule=route_cfg.get("rule", "/<int:role_id>/permissions"),
            view_func=assign_permission,
            methods=route_cfg.get("methods", ["POST"]),
            input_schemas=route_cfg.get(
                "input_schemas", [{"schema": PermissionIdSchema, "location": "json"}]
            ),
            output_schema=route_cfg.get("output_schema", MessageSchema),
            doc=route_cfg.get("doc", {"summary": "Assign Permission To Role"}),
            permission=route_cfg.get("permission", "assign_permission:role"),
            apply_unit_of_work=route_cfg.get("apply_unit_of_work", True),
            auth_required=route_cfg.get("auth_required", True),
            decorators=route_cfg.get("decorators"),
        )

    if is_route_enabled("revoke_permission_from_role"):
        route_cfg = routes_config.get("revoke_permission_from_role", {})

        def revoke_permission(role_id: int, json_data):
            g.devkit.get_service("permission").revoke_permission_from_role(
                role_id, json_data["permission_id"]
            )
            return {"message": "Permission revoked from role"}

        register_custom_route(
            roles_bp,
            rule=route_cfg.get("rule", "/<int:role_id>/permissions"),
            view_func=revoke_permission,
            methods=route_cfg.get("methods", ["DELETE"]),
            input_schemas=route_cfg.get(
                "input_schemas", [{"schema": PermissionIdSchema, "location": "json"}]
            ),
            output_schema=route_cfg.get("output_schema", MessageSchema),
            doc=route_cfg.get("doc", {"summary": "Revoke Permission From Role"}),
            permission=route_cfg.get("permission", "revoke_permission:role"),
            apply_unit_of_work=route_cfg.get("apply_unit_of_work", True),
            auth_required=route_cfg.get("auth_required", True),
            decorators=route_cfg.get("decorators"),
        )

    return auth_bp, users_bp, roles_bp, permissions_bp
