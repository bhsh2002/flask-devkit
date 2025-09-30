# flask_devkit/audit/models.py
import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from flask_devkit.database import db


class AuditLog(db.Model):
    """
    Represents a log of a single CUD operation on a database model.
    """

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", name="fk_audit_log_user_id"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(
        String(10), nullable=False, index=True
    )  # CREATE, UPDATE, DELETE
    table_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    record_pk: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    old_values: Mapped[dict] = mapped_column(JSON, nullable=True)
    new_values: Mapped[dict] = mapped_column(JSON, nullable=True)

    user = db.relationship("User", backref="audit_logs")

    def __repr__(self):
        return (
            f"<AuditLog id={self.id} action='{self.action}' "
            f"table='{self.table_name}' record_pk='{self.record_pk}'>"
        )
