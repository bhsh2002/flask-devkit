# flask_devkit/core/repository.py
"""
Provides a generic repository pattern for SQLAlchemy models.

This module contains the BaseRepository class which encapsulates common
database operations (CRUD, pagination, filtering) for a given model.
"""

import math
import datetime
from functools import wraps
from typing import Any, Dict, Generic, List, NamedTuple, Optional, Type, TypeVar

from flask import current_app
from sqlalchemy import func, or_, inspect
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import DeclarativeMeta, Session, Query

from flask_devkit.core.archive import ArchivedRecord
from flask_devkit.core.exceptions import DatabaseError, DuplicateEntryError

T = TypeVar("T", bound=DeclarativeMeta)


class PaginationResult(Generic[T], NamedTuple):
    """A structured result for paginated queries."""

    items: List[T]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool


def handle_db_errors(func):
    """Decorator that wraps repository methods to handle SQLAlchemy errors."""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except IntegrityError as e:
            raise DuplicateEntryError(original_exception=e) from e
        except SQLAlchemyError as e:
            current_app.logger.error(
                f"Database error in {func.__name__} for {self.model.__name__}: {e}",
                exc_info=True,
            )
            self._db_session.rollback()
            raise DatabaseError(original_exception=e) from e

    return wrapper


class BaseRepository(Generic[T]):
    """
    Generic repository providing common CRUD operations for a SQLAlchemy model.
    """

    def __init__(self, model: Type[T], db_session: Session):
        self.model = model
        self._db_session = db_session

    def _query(self):
        return self._db_session.query(self.model)

    def _filter_soft_deleted(self, query, deleted_state: str = "active"):
        """Adds a filter to handle soft-deleted records."""
        if hasattr(self.model, "deleted_at"):
            if deleted_state == "active":
                return query.filter(self.model.deleted_at.is_(None))
            elif deleted_state == "deleted_only":
                return query.filter(self.model.deleted_at.is_not(None))
        return query

    def _apply_filters(self, query: Query, filters: Optional[Dict[str, str]]) -> Query:
        if not filters:
            return query

        op_map = {
            "eq": "__eq__",
            "ne": "__ne__",
            "lt": "__lt__",
            "lte": "__le__",
            "gt": "__gt__",
            "gte": "__ge__",
        }

        for field_name, conditions_string in filters.items():
            if not hasattr(self.model, field_name):
                current_app.logger.warning(
                    f"Filter field '{field_name}' does not exist on model '{self.model.__name__}'"
                )
                continue

            column = getattr(self.model, field_name)
            clauses = []

            conditions = conditions_string.split(",")
            for condition in conditions:
                condition = condition.strip()
                if not condition:
                    continue

                parts = condition.split("__", 1)

                if len(parts) == 1:
                    op, value = "eq", parts[0]
                else:
                    op, value = parts

                op = op.strip()
                value = value.strip()

                if op in ("like", "ilike"):
                    clause = (
                        column.ilike(f"%{value}%")
                        if op == "ilike"
                        else column.like(f"%{value}%")
                    )
                    clauses.append(clause)
                elif op == "in":
                    in_values = [v.strip() for v in value.split("|")]
                    clauses.append(column.in_(in_values))
                elif op in op_map:
                    clause = getattr(column, op_map[op])(value)
                    clauses.append(clause)
                else:
                    current_app.logger.warning(f"Unknown filter operator: {op}")

            if clauses:
                query = query.filter(or_(*clauses))

        return query

    def _apply_ordering(self, query, order_by: Optional[List[str]] = None):
        if order_by:
            for field in order_by:
                if field.startswith("-"):
                    column_name = field[1:]
                    if hasattr(self.model, column_name):
                        query = query.order_by(getattr(self.model, column_name).desc())
                else:
                    if hasattr(self.model, field):
                        query = query.order_by(getattr(self.model, field).asc())
        return query

    @handle_db_errors
    def create(self, data: Dict[str, Any]) -> T:
        entity = self.model(**data)
        self._db_session.add(entity)
        self._db_session.flush()
        return entity

    @handle_db_errors
    def get_by_id(self, id_: Any, deleted_state: str = "active") -> Optional[T]:
        query = self._query().filter(self.model.id == id_)
        query = self._filter_soft_deleted(query, deleted_state)
        return query.first()

    @handle_db_errors
    def get_by_uuid(self, uuid: str, deleted_state: str = "active") -> Optional[T]:
        query = self._query().filter_by(uuid=uuid)
        query = self._filter_soft_deleted(query, deleted_state)
        return query.first()

    @handle_db_errors
    def find_one_by(
        self, filters: Dict[str, Any], deleted_state: str = "active"
    ) -> Optional[T]:
        query = self._query()
        query = self._filter_soft_deleted(query, deleted_state)
        query = self._apply_filters(query, filters)
        return query.first()

    @handle_db_errors
    def delete(self, entity: T, soft: bool = True) -> None:
        if soft and hasattr(entity, "deleted_at"):
            entity.deleted_at = func.now()
            self._db_session.add(entity)
        else:
            self._db_session.delete(entity)

    @handle_db_errors
    def force_delete(self, entity: T) -> None:
        pk_name = inspect(entity.__class__).primary_key[0].name
        pk_value = getattr(entity, pk_name)

        data_to_archive = {
            c.name: getattr(entity, c.name) for c in entity.__table__.columns
        }

        for key, value in data_to_archive.items():
            if isinstance(value, datetime.datetime):
                data_to_archive[key] = value.isoformat()

        archived_record = ArchivedRecord(
            original_table=entity.__table__.name,
            original_pk=str(pk_value),
            data=data_to_archive,
        )
        self._db_session.add(archived_record)
        self._db_session.delete(entity)

    @handle_db_errors
    def restore(self, entity: T) -> None:
        if hasattr(entity, "deleted_at"):
            entity.deleted_at = None
            self._db_session.add(entity)

    @handle_db_errors
    def paginate(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
        deleted_state: str = "active",
    ) -> PaginationResult[T]:
        query = self._query()
        query = self._filter_soft_deleted(query, deleted_state)

        filters_copy = filters.copy() if filters else {}
        query = self._apply_filters(query, filters_copy)

        pk_column = inspect(self.model).primary_key[0]
        count_query = query.with_entities(func.count(pk_column))
        total_count = count_query.scalar()

        total_pages = math.ceil(total_count / per_page) if total_count > 0 else 0

        query = self._apply_ordering(query, order_by)
        items = query.offset((page - 1) * per_page).limit(per_page).all()

        return PaginationResult(
            items=items,
            total=total_count,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            has_next=(page < total_pages),
            has_prev=(page > 1),
        )
