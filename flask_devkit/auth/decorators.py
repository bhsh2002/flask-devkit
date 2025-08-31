# flask_devkit/auth/decorators.py
from functools import wraps

from flask_jwt_extended import get_jwt, verify_jwt_in_request

from flask_devkit.core.exceptions import PermissionDeniedError


def permission_required(permission: str):
    """
    Decorator factory to ensure a user has a specific permission in their JWT.
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_permissions = claims.get("permissions", [])
            is_super_admin = claims.get("is_super_admin", False)

            if not is_super_admin and permission not in user_permissions:
                raise PermissionDeniedError(
                    f"Required permission '{permission}' is missing."
                )
            return fn(*args, **kwargs)

        return wrapper

    return decorator
