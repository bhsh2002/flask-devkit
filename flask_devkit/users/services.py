from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional, Tuple

from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token

from flask_devkit.core.exceptions import (
    AuthenticationError,
    BusinessLogicError,
    NotFoundError,
)
from flask_devkit.core.service import BaseService

from .models import Permission, Role, User, UserRoleAssociation


class UserService(BaseService[User]):
    def __init__(
        self,
        model: type[User],
        db_session,
        *,
        additional_claims_loader: Optional[Callable] = None,
    ):
        super().__init__(model, db_session)
        self.additional_claims_loader = additional_claims_loader

    @staticmethod
    def _validate_password_strength(password: str) -> None:
        if not password or len(password) < 8:
            raise BusinessLogicError("Password must be at least 8 characters long.")
        has_alpha = any(c.isalpha() for c in password)
        has_digit = any(c.isdigit() for c in password)
        if not (has_alpha and has_digit):
            raise BusinessLogicError("Password must include letters and numbers.")

    def _username_exists(self, username: str) -> bool:
        return (
            self._db_session.query(User).filter(User.username == username).first()
            is not None
        )

    def pre_create_hook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        username = data.get("username")
        if username and self._username_exists(username):
            raise BusinessLogicError("Username already exists.")

        password = data.pop("password", None)
        if password:
            self._validate_password_strength(password)
            temp_user = User()
            temp_user.set_password(password)
            data["password_hash"] = temp_user.password_hash
        return data

    def login_user(self, username: str, password: str) -> Tuple[User, str, str]:
        user = self.repo._query().filter(User.username == username).first()

        if not user or not user.check_password(password):
            raise AuthenticationError("Invalid credentials.")
        if not user.is_active:
            raise AuthenticationError("User account is not active.")
        if getattr(user, "deleted_at", None) is not None:
            raise AuthenticationError("User account has been deleted.")

        user.last_login_at = datetime.now()
        self._db_session.add(user)

        access_token, refresh_token = self.generate_tokens_for_user(user)
        return user, access_token, refresh_token

    def generate_tokens_for_user(self, user: User) -> Tuple[str, str]:
        identity = str(getattr(user, "uuid", user.id))
        roles = list(getattr(user, "roles", []))
        is_super_admin = any(getattr(role, "is_system_role", False) for role in roles)
        permissions = []
        for role in roles:
            for perm in getattr(role, "permissions", []) or []:
                name = getattr(perm, "name", None)
                if name:
                    permissions.append(name)

        additional_claims = {
            "user_id": user.id,
            "roles": [role.name for role in roles],
            "is_super_admin": is_super_admin,
            "permissions": sorted(set(permissions)),
        }

        if self.additional_claims_loader:
            custom_claims = self.additional_claims_loader(user)
            additional_claims.update(custom_claims)

        access_token = create_access_token(
            identity=identity,
            expires_delta=current_app.config.get(
                "JWT_ACCESS_TOKEN_EXPIRES", timedelta(days=1)
            ),
            additional_claims=additional_claims,
        )
        refresh_token = create_refresh_token(identity=identity)
        return access_token, refresh_token

    def generate_fresh_token_for_identity(self, identity: str) -> str:
        user = self.get_by_uuid(identity)
        if not user:
            raise NotFoundError("User", identity)

        # We can regenerate claims to ensure they are fresh
        access_token, _ = self.generate_tokens_for_user(user)
        return access_token

    def change_password(
        self, user_uuid: str, current_password: str, new_password: str
    ) -> None:
        user = self.get_by_uuid(user_uuid)
        if not user or not user.check_password(current_password):
            raise AuthenticationError("Invalid credentials.")
        self._validate_password_strength(new_password)
        user.set_password(new_password)
        self._db_session.add(user)


class RoleService(BaseService[Role]):
    def pre_delete_hook(self, instance: Role) -> None:
        if instance.is_system_role:
            raise BusinessLogicError(
                f"System role '{instance.name}' cannot be deleted."
            )

    def pre_update_hook(self, instance: Role, data: Dict[str, Any]):
        if instance.is_system_role and "name" in data and data["name"] != instance.name:
            raise BusinessLogicError(
                f"System role '{instance.name}' cannot be renamed."
            )
        super().pre_update_hook(instance, data)

    def assign_role(self, user_uuid: str, role_id: int, assigned_by_user_id: int):
        user = self._db_session.query(User).filter(User.uuid == user_uuid).first()
        role = self.get_by_id(role_id)

        if not user:
            raise NotFoundError("User", user_uuid)
        if not role:
            raise NotFoundError("Role", role_id)

        existing = (
            self._db_session.query(UserRoleAssociation)
            .filter_by(user_id=user.id, role_id=role_id)
            .first()
        )
        if existing:
            return

        association = UserRoleAssociation(
            user_id=user.id, role_id=role_id, assigned_by_user_id=assigned_by_user_id
        )
        self._db_session.add(association)

    def get_roles_for_user(self, user_uuid: str):
        user = self._db_session.query(User).filter(User.uuid == user_uuid).first()
        if not user:
            raise NotFoundError("User", user_uuid)
        return user.roles

    def revoke_role(self, user_uuid: str, role_id: int):
        user = self._db_session.query(User).filter(User.uuid == user_uuid).first()
        if not user:
            raise NotFoundError("User", user_uuid)

        assoc = (
            self._db_session.query(UserRoleAssociation)
            .filter_by(user_id=user.id, role_id=role_id)
            .first()
        )
        if assoc:
            self._db_session.delete(assoc)


class PermissionService(BaseService[Permission]):
    def assign_permission_to_role(self, role_id: int, permission_id: int):
        role = self._db_session.get(Role, role_id)
        perm = self.get_by_id(permission_id)
        if not role:
            raise NotFoundError("Role", role_id)
        if not perm:
            raise NotFoundError("Permission", permission_id)

        if perm not in role.permissions:
            role.permissions.append(perm)
            self._db_session.add(role)

    def revoke_permission_from_role(self, role_id: int, permission_id: int):
        role = self._db_session.get(Role, role_id)
        perm = self.get_by_id(permission_id)
        if not role:
            raise NotFoundError("Role", role_id)
        if not perm:
            raise NotFoundError("Permission", permission_id)

        if perm in role.permissions:
            role.permissions.remove(perm)
            self._db_session.add(role)

    def list_role_permissions(self, role_id: int):
        role = self._db_session.get(Role, role_id)
        if not role:
            raise NotFoundError("Role", role_id)
        return role.permissions
