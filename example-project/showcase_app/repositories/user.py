# showcase_app/repositories/user.py
from sqlalchemy import func

from flask_devkit.core.repository import BaseRepository
from flask_devkit.users.models import User


class CustomUserRepository(BaseRepository[User]):
    """
    An example of a custom repository that extends the BaseRepository
    to add application-specific database queries.
    """

    def count_active_users(self) -> int:
        """Example of a custom method."""
        return self._query().filter(User.is_active == True).count()
