from apiflask import Schema
from apiflask.fields import Integer, Nested, String

from flask_devkit.helpers.schemas import create_crud_schemas

from .models import Permission, Role, User

user_schemas = create_crud_schemas(
    model_class=User,
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


class LoginSchema(Schema):
    username = String(required=True)
    password = String(required=True, load_only=True)


class AuthTokenSchema(Schema):
    access_token = String()
    refresh_token = String()
    user = Nested(user_schemas["main"], metadata={"description": "Authenticated user."})


role_schemas = create_crud_schemas(model_class=Role)


class AssignRoleSchema(Schema):
    role_id = Integer(required=True)


permission_schemas = create_crud_schemas(model_class=Permission)


class ChangePasswordSchema(Schema):
    current_password = String(required=True, load_only=True)
    new_password = String(required=True, load_only=True)


class PermissionIdSchema(Schema):
    permission_id = Integer(required=True)
