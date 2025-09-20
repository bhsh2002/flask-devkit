from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from flask_devkit.core.mixins import TimestampMixin, UUIDMixin
from flask_devkit.database import db


class Post(db.Model, TimestampMixin, UUIDMixin):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    title = Column(String(120), nullable=False)
    content = Column(String, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    author = relationship("User", back_populates="posts")


# Add the posts relationship to the User model dynamically
from flask_devkit.users.models import User  # noqa: E402

User.posts = relationship("Post", back_populates="author", lazy="dynamic")

