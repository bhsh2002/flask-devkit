# flask_devkit/core/mixins.py
"""
Reusable SQLAlchemy model mixins for common patterns.

These mixins can be combined with a declarative base model (like db.Model)
to quickly add common columns and functionality to your models.
"""

import uuid

from sqlalchemy import CHAR, INTEGER, TIMESTAMP, Column, func, text
from sqlalchemy.orm import declarative_mixin


def generate_uuid() -> str:
    """Generates a string representation of a UUID4."""
    return str(uuid.uuid4())


@declarative_mixin
class IDMixin:
    """Adds a standard integer primary key column named 'id'."""

    id = Column(INTEGER, primary_key=True, autoincrement=True)


@declarative_mixin
class UUIDMixin:
    """Adds a unique, indexed, and auto-generating UUID column."""

    uuid = Column(
        CHAR(36), unique=True, nullable=False, index=True, default=generate_uuid
    )


@declarative_mixin
class TimestampMixin:
    """Adds `created_at` and `updated_at` timestamp columns.

    `created_at` is set on creation, and `updated_at` is updated automatically
    on any modification.
    """

    created_at = Column(
        TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"), index=True
    )
    updated_at = Column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=func.now(),
    )


@declarative_mixin
class SoftDeleteMixin:
    """Adds a `deleted_at` timestamp for implementing soft deletes."""

    deleted_at = Column(TIMESTAMP, nullable=True, index=True)
