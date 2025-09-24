# flask_devkit/core/archive.py
"""
Model for storing archived records from permanent deletions.
"""
from sqlalchemy import JSON, TIMESTAMP, Column, String, Text, func

from flask_devkit.core.mixins import IDMixin
from flask_devkit.database import db


class ArchivedRecord(db.Model, IDMixin):
    """
    A model to store records that have been permanently deleted from their
    original tables.
    """

    __tablename__ = "archived_records"

    original_table = Column(String(128), nullable=False, index=True)
    original_pk = Column(
        Text, nullable=False
    )  # Use Text to accommodate various PK types
    data = Column(JSON, nullable=False)
    archived_at = Column(
        TIMESTAMP, nullable=False, server_default=func.now(), index=True
    )
