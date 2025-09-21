# flask_devkit/users/routes.py
from apiflask import APIBlueprint
from flask import current_app, g
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from flask_devkit.auth.decorators import permission_required
from flask_devkit.core.unit_of_work import unit_of_work
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


def create_all_blueprints(bp: APIBlueprint):
    auth_bp = APIBlueprint("auth", __name__, url_prefix="/auth")
    users_bp = APIBlueprint("user", __name__, url_prefix="/users")
    roles_bp = APIBlueprint("role", __name__, url_prefix="/roles")
    permissions_bp = APIBlueprint("permission", __name__, url_prefix="/permissions")

    @bp.before_request
    def before_request():
        g.devkit = current_app.extensions["devkit"]

    @roles_bp.post("/users/<string:user_uuid>")
    @roles_bp.input(AssignRoleSchema)
    @roles_bp.output(MessageSchema)
    @roles_bp.doc(summary="Assign Role To User", security="bearerAuth")
    @jwt_required()
    @permission_required("assign_role:user")
    @unit_of_work
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

    @roles_bp.get("/users/<string:user_uuid>")
    @roles_bp.output(role_schemas["main"](many=True))
    @roles_bp.doc(summary="List Roles Assigned To User", security="bearerAuth")
    @jwt_required()
    @permission_required("read_roles:user")
    def list_user_roles(user_uuid):
        user_service = g.devkit.get_service("user")
        role_service = g.devkit.get_service("role")
        user = user_service.get_by_uuid(user_uuid)
        return role_service.get_roles_for_user(user)

    @auth_bp.post("/login")
    @auth_bp.input(LoginSchema)
    @auth_bp.output(AuthTokenSchema)
    @auth_bp.doc(summary="User Login")
    @unit_of_work
    def login(json_data):
        user, access_token, refresh_token = g.devkit.get_service("user").login_user(
            username=json_data["username"], password=json_data["password"]
        )
        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    @auth_bp.get("/me")
    @auth_bp.output(user_schemas["main"])
    @auth_bp.doc(summary="Current Authenticated User", security="bearerAuth")
    @jwt_required()
    def whoami():
        user_uuid = get_jwt_identity()
        user = g.devkit.get_service("user").get_by_uuid(user_uuid)
        return user

    @auth_bp.post("/refresh")
    @auth_bp.output(AuthTokenSchema)
    @auth_bp.doc(summary="Refresh Access Token", security="bearerAuth")
    @jwt_required(refresh=True)
    def refresh():
        user_uuid = get_jwt_identity()
        new_access = g.devkit.get_service("user").generate_fresh_token_for_identity(
            user_uuid
        )
        return {"access_token": new_access}

    @roles_bp.delete("/users/<string:user_uuid>")
    @roles_bp.input(AssignRoleSchema)
    @roles_bp.output(MessageSchema)
    @roles_bp.doc(summary="Revoke Role From User", security="bearerAuth")
    @jwt_required()
    @permission_required("revoke_role:user")
    @unit_of_work
    def revoke_role(user_uuid, json_data):
        role_id = json_data["role_id"]
        user_service = g.devkit.get_service("user")
        role_service = g.devkit.get_service("role")

        user = user_service.get_by_uuid(user_uuid)
        role = role_service.get_by_id(role_id)

        role_service.revoke_role(user=user, role=role)
        return {"message": "Role revoked successfully"}

    @roles_bp.get("/<int:role_id>/permissions")
    @roles_bp.output(permission_schemas["main"](many=True))
    @roles_bp.doc(summary="List Permissions For Role", security="bearerAuth")
    @jwt_required()
    @permission_required("read_permissions:role")
    def list_role_permissions(role_id: int):
        return g.devkit.get_service("permission").list_role_permissions(role_id)

    @roles_bp.post("/<int:role_id>/permissions")
    @roles_bp.input(PermissionIdSchema)
    @roles_bp.output(MessageSchema)
    @roles_bp.doc(summary="Assign Permission To Role", security="bearerAuth")
    @jwt_required()
    @permission_required("assign_permission:role")
    @unit_of_work
    def assign_permission(role_id: int, json_data):
        g.devkit.get_service("permission").assign_permission_to_role(
            role_id, json_data["permission_id"]
        )
        return {"message": "Permission assigned to role"}

    @roles_bp.delete("/<int:role_id>/permissions")
    @roles_bp.input(PermissionIdSchema)
    @roles_bp.output(MessageSchema)
    @roles_bp.doc(summary="Revoke Permission From Role", security="bearerAuth")
    @jwt_required()
    @permission_required("revoke_permission:role")
    @unit_of_work
    def revoke_permission(role_id: int, json_data):
        g.devkit.get_service("permission").revoke_permission_from_role(
            role_id, json_data["permission_id"]
        )
        return {"message": "Permission revoked from role"}

    @users_bp.post("/change-password")
    @users_bp.input(ChangePasswordSchema)
    @users_bp.output(MessageSchema)
    @users_bp.doc(summary="Change current user's password", security="bearerAuth")
    @jwt_required()
    @unit_of_work
    def change_password(json_data):
        user_uuid = get_jwt_identity()
        g.devkit.get_service("user").change_password(
            user_uuid=user_uuid,
            current_password=json_data["current_password"],
            new_password=json_data["new_password"],
        )
        return {"message": "Password changed successfully"}

    return auth_bp, users_bp, roles_bp, permissions_bp
