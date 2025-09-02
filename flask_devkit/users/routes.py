# flask_devkit/users/routes.py
# flask_devkit/users/routes.py
from apiflask import APIBlueprint
from flask import current_app
from flask_jwt_extended import (
    get_jwt,
    get_jwt_identity,
    jwt_required,
)

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

# Create blueprint objects here, they will be configured and registered in the factory
auth_bp = APIBlueprint("auth", __name__, url_prefix="/auth")
users_bp = APIBlueprint("users", __name__, url_prefix="/users")
roles_bp = APIBlueprint("roles", __name__, url_prefix="/roles")
permissions_bp = APIBlueprint("permissions", __name__, url_prefix="/permissions")


def _get_devkit_extension():
    return current_app.extensions["devkit"]


def create_all_blueprints():
    auth_bp = APIBlueprint("auth", __name__, url_prefix="/auth")
    users_bp = APIBlueprint("users", __name__, url_prefix="/users")
    roles_bp = APIBlueprint("roles", __name__, url_prefix="/roles")
    permissions_bp = APIBlueprint("permissions", __name__, url_prefix="/permissions")

    @roles_bp.post("/users/<string:user_uuid>")
    @roles_bp.input(AssignRoleSchema)
    @roles_bp.output(MessageSchema)
    @roles_bp.doc(summary="Assign Role To User")
    @jwt_required()
    @permission_required("assign_role:user")
    @unit_of_work
    def assign_role(user_uuid, json_data):
        role_id = json_data["role_id"]
        claims = get_jwt()
        current_user_id = claims.get("user_id")
        devkit = _get_devkit_extension()
        devkit.role_service.assign_role(
            user_uuid=user_uuid, role_id=role_id, assigned_by_user_id=current_user_id
        )
        return {"message": "Role assigned successfully"}

    @roles_bp.get("/users/<string:user_uuid>")
    @roles_bp.output(role_schemas["main"](many=True))
    @roles_bp.doc(summary="List Roles Assigned To User")
    @jwt_required()
    @permission_required("read_roles:user")
    def list_user_roles(user_uuid):
        devkit = _get_devkit_extension()
        return devkit.role_service.get_roles_for_user(user_uuid)

    @auth_bp.post("/login")
    @auth_bp.input(LoginSchema)
    @auth_bp.output(AuthTokenSchema)
    @auth_bp.doc(summary="User Login")
    @unit_of_work
    def login(json_data):
        devkit = _get_devkit_extension()
        user, access_token, refresh_token = devkit.user_service.login_user(
            username=json_data["username"], password=json_data["password"]
        )
        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    @auth_bp.get("/me")
    @auth_bp.output(user_schemas["main"])
    @auth_bp.doc(summary="Current Authenticated User")
    @auth_bp.auth_required("jwt")
    @jwt_required()
    def whoami():
        user_uuid = get_jwt_identity()
        devkit = _get_devkit_extension()
        user = devkit.user_service.get_by_uuid(user_uuid)
        return user

    @auth_bp.post("/refresh")
    @jwt_required(refresh=True)
    @auth_bp.output(AuthTokenSchema)
    @auth_bp.doc(summary="Refresh Access Token")
    def refresh():
        user_uuid = get_jwt_identity()
        devkit = _get_devkit_extension()
        new_access = devkit.user_service.generate_fresh_token_for_identity(user_uuid)
        return {"access_token": new_access}

    @auth_bp.post("/logout")
    @jwt_required(optional=True)
    @roles_bp.output(MessageSchema)
    @roles_bp.doc(summary="Logout and clear tokens")
    def logout():
        return {"message": "Logged out"}

    @roles_bp.delete("/users/<string:user_uuid>")
    @roles_bp.input(AssignRoleSchema)
    @roles_bp.output(MessageSchema)
    @roles_bp.doc(summary="Revoke Role From User")
    @jwt_required()
    @permission_required("revoke_role:user")
    @unit_of_work
    def revoke_role(user_uuid, json_data):
        role_id = json_data["role_id"]
        devkit = _get_devkit_extension()
        devkit.role_service.revoke_role(user_uuid=user_uuid, role_id=role_id)
        return {"message": "Role revoked successfully"}

    @roles_bp.get("/<int:role_id>/permissions")
    @roles_bp.output(permission_schemas["main"](many=True))
    @roles_bp.doc(summary="List Permissions For Role")
    @jwt_required()
    @permission_required("read_permissions:role")
    def list_role_permissions(role_id: int):
        devkit = _get_devkit_extension()
        return devkit.permission_service.list_role_permissions(role_id)

    @roles_bp.post("/<int:role_id>/permissions")
    @roles_bp.input(PermissionIdSchema)
    @roles_bp.output(MessageSchema)
    @roles_bp.doc(summary="Assign Permission To Role")
    @jwt_required()
    @permission_required("assign_permission:role")
    @unit_of_work
    def assign_permission(role_id: int, json_data):
        devkit = _get_devkit_extension()
        devkit.permission_service.assign_permission_to_role(
            role_id, json_data["permission_id"]
        )
        return {"message": "Permission assigned to role"}

    @roles_bp.delete("/<int:role_id>/permissions")
    @roles_bp.input(PermissionIdSchema)
    @roles_bp.output(MessageSchema)
    @roles_bp.doc(summary="Revoke Permission From Role")
    @jwt_required()
    @permission_required("revoke_permission:role")
    @unit_of_work
    def revoke_permission(role_id: int, json_data):
        devkit = _get_devkit_extension()
        devkit.permission_service.revoke_permission_from_role(
            role_id, json_data["permission_id"]
        )
        return {"message": "Permission revoked from role"}

    @users_bp.post("/change-password")
    @users_bp.input(ChangePasswordSchema)
    @users_bp.output(MessageSchema)
    @users_bp.doc(summary="Change current user's password")
    @jwt_required()
    @unit_of_work
    def change_password(json_data):
        user_uuid = get_jwt_identity()
        devkit = _get_devkit_extension()
        devkit.user_service.change_password(
            user_uuid=user_uuid,
            current_password=json_data["current_password"],
            new_password=json_data["new_password"],
        )
        return {"message": "Password changed successfully"}

    return auth_bp, users_bp, roles_bp, permissions_bp


@roles_bp.get("/users/<string:user_uuid>")
@roles_bp.output(role_schemas["main"](many=True))
@roles_bp.doc(summary="List Roles Assigned To User")
@jwt_required()
@permission_required("read_roles:user")
def list_user_roles(user_uuid):
    devkit = _get_devkit_extension()
    return devkit.role_service.get_roles_for_user(user_uuid)


@auth_bp.post("/login")
@auth_bp.input(LoginSchema)
@auth_bp.output(AuthTokenSchema)
@auth_bp.doc(summary="User Login")
@unit_of_work
def login(json_data):
    devkit = _get_devkit_extension()
    user, access_token, refresh_token = devkit.user_service.login_user(
        username=json_data["username"], password=json_data["password"]
    )
    return {
        "user": user,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


@auth_bp.get("/me")
@auth_bp.output(user_schemas["main"])
@auth_bp.doc(summary="Current Authenticated User")
@auth_bp.auth_required("jwt")
@jwt_required()
def whoami():
    user_uuid = get_jwt_identity()
    devkit = _get_devkit_extension()
    user = devkit.user_service.get_by_uuid(user_uuid)
    return user


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
@auth_bp.output(AuthTokenSchema)
@auth_bp.doc(summary="Refresh Access Token")
def refresh():
    user_uuid = get_jwt_identity()
    devkit = _get_devkit_extension()
    new_access = devkit.user_service.generate_fresh_token_for_identity(user_uuid)
    return {"access_token": new_access}


@auth_bp.post("/logout")
@jwt_required(optional=True)
@roles_bp.output(MessageSchema)
@roles_bp.doc(summary="Logout and clear tokens")
def logout():
    return {"message": "Logged out"}


@roles_bp.delete("/users/<string:user_uuid>")
@roles_bp.input(AssignRoleSchema)
@roles_bp.output(MessageSchema)
@roles_bp.doc(summary="Revoke Role From User")
@jwt_required()
@permission_required("revoke_role:user")
@unit_of_work
def revoke_role(user_uuid, json_data):
    role_id = json_data["role_id"]
    devkit = _get_devkit_extension()
    devkit.role_service.revoke_role(user_uuid=user_uuid, role_id=role_id)
    return {"message": "Role revoked successfully"}


@roles_bp.get("/<int:role_id>/permissions")
@roles_bp.output(permission_schemas["main"](many=True))
@roles_bp.doc(summary="List Permissions For Role")
@jwt_required()
@permission_required("read_permissions:role")
def list_role_permissions(role_id: int):
    devkit = _get_devkit_extension()
    return devkit.permission_service.list_role_permissions(role_id)


@roles_bp.post("/<int:role_id>/permissions")
@roles_bp.input(PermissionIdSchema)
@roles_bp.output(MessageSchema)
@roles_bp.doc(summary="Assign Permission To Role")
@jwt_required()
@permission_required("assign_permission:role")
@unit_of_work
def assign_permission(role_id: int, json_data):
    devkit = _get_devkit_extension()
    devkit.permission_service.assign_permission_to_role(
        role_id, json_data["permission_id"]
    )
    return {"message": "Permission assigned to role"}


@roles_bp.delete("/<int:role_id>/permissions")
@roles_bp.input(PermissionIdSchema)
@roles_bp.output(MessageSchema)
@roles_bp.doc(summary="Revoke Permission From Role")
@jwt_required()
@permission_required("revoke_permission:role")
@unit_of_work
def revoke_permission(role_id: int, json_data):
    devkit = _get_devkit_extension()
    devkit.permission_service.revoke_permission_from_role(
        role_id, json_data["permission_id"]
    )
    return {"message": "Permission revoked from role"}


@users_bp.post("/change-password")
@users_bp.input(ChangePasswordSchema)
@users_bp.output(MessageSchema)
@users_bp.doc(summary="Change current user's password")
@jwt_required()
@unit_of_work
def change_password(json_data):
    user_uuid = get_jwt_identity()
    devkit = _get_devkit_extension()
    devkit.user_service.change_password(
        user_uuid=user_uuid,
        current_password=json_data["current_password"],
        new_password=json_data["new_password"],
    )
    return {"message": "Password changed successfully"}
