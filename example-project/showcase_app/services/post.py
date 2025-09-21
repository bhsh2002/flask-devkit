from datetime import datetime
from flask import current_app
from flask_jwt_extended import get_jwt, get_jwt_identity

from flask_devkit.core.exceptions import BusinessLogicError, PermissionDeniedError
from flask_devkit.core.repository import PaginationResult
from flask_devkit.core.service import BaseService
from flask_devkit.users.models import User
from showcase_app.models.post import Post


class PostService(BaseService[Post]):
    def _calculate_read_time(self, post: Post):
        """Calculates the estimated read time in minutes."""
        if not post or not post.content:
            return 0
        words_per_minute = current_app.config.get("WORDS_PER_MINUTE_READ_SPEED", 200)
        word_count = len(post.content.split())
        return max(1, round(word_count / words_per_minute))

    def post_get_hook(self, entity: Post | None) -> Post | None:
        """After getting a single post, add the calculated read time."""
        if entity:
            entity.read_time_minutes = self._calculate_read_time(entity)
        return entity

    def post_list_hook(self, result: PaginationResult[Post]) -> PaginationResult[Post]:
        """After getting a list of posts, add the read time to each one."""
        for item in result.items:
            item.read_time_minutes = self._calculate_read_time(item)
        return result

    def pre_create_hook(self, data):
        """Set the author_id from the current user's JWT identity."""
        user_uuid = get_jwt_identity()
        # In a real app, you might want to fetch the user object more robustly
        user = self.repo._db_session.query(User).filter_by(uuid=user_uuid).first()
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
        super().pre_update_hook(instance, data)

    def pre_delete_hook(self, instance: Post):
        """Check if the current user can delete the post and if it is published."""
        if instance.is_published:
            raise BusinessLogicError("Cannot delete a post that is already published.")
        self._check_permission(instance, "delete:post")
        super().pre_delete_hook(instance)

    def publish(self, post_uuid: str) -> Post:
        """Sets a post to published."""
        post = self.repo.get_by_uuid(post_uuid)
        if not post:
            raise BusinessLogicError(f"Post with UUID {post_uuid} not found.")

        self._check_permission(post, "publish:post")

        if post.is_published:
            return post  # Already published, do nothing

        post.is_published = True
        post.published_at = datetime.utcnow()
        self.repo._db_session.add(post)
        return post
