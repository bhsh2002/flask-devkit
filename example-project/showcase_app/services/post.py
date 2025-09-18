from flask_jwt_extended import get_jwt, get_jwt_identity

from flask_devkit.core.exceptions import PermissionDeniedError
from flask_devkit.core.service import BaseService
from flask_devkit.users.models import User
from showcase_app.models.post import Post


class PostService(BaseService[Post]):
    def pre_create_hook(self, data):
        """Set the author_id from the current user's JWT identity."""
        user_uuid = get_jwt_identity()
        user = self.db_session.query(User).filter_by(uuid=user_uuid).one_or_none()
        if user:
            data["author_id"] = user.id
        return data

    def _check_permission(self, post: Post, required_perm: str):
        """
        Checks if the current user has permission to modify the post.
        Allows action if the user is the author or has the required permission.
        """
        claims = get_jwt()
        user_uuid = get_jwt_identity()
        permissions = claims.get("permissions", [])

        is_author = str(post.author.uuid) == user_uuid
        has_permission = required_perm in permissions

        if not (is_author or has_permission):
            raise PermissionDeniedError(
                f"You must be the author or have the '{required_perm}' permission."
            )

    def pre_update_hook(self, instance, data):
        """Check if the current user can update the post."""
        self._check_permission(instance, "update:post")
        return super().pre_update_hook(instance, data)

    def pre_delete_hook(self, instance):
        """Check if the current user can delete the post."""
        self._check_permission(instance, "delete:post")
        return super().pre_delete_hook(instance)
