# flask_devkit/core/repository.py
"""
Provides a generic repository pattern for SQLAlchemy models.

This module contains the BaseRepository class which encapsulates common
database operations (CRUD, pagination, filtering) for a given model.
"""

import math
from functools import wraps
from typing import Any, Dict, Generic, List, NamedTuple, Optional, Type, TypeVar

from flask import current_app
from sqlalchemy import func, or_, and_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import DeclarativeMeta, Session

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
            current_app.logger.warning(
                f"Integrity error in {func.__name__} for {self.model.__name__}: {e}",
                exc_info=True,
            )
            self._db_session.rollback()
            # Surface a friendlier duplicate entry error
            raise DuplicateEntryError(
                "Duplicate key or unique constraint violated."
            ) from e
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

    This repository is designed to be used within a Flask application context,
    as it relies on `db.session` from Flask-SQLAlchemy and `current_app.logger`.

    Transactions (commits) are not handled by the repository itself and should
    be managed by the Service layer.
    """

    def __init__(self, model: Type[T], db_session: Session):
        """
        Initializes the repository with a specific SQLAlchemy model and session.

        Args:
            model: The SQLAlchemy model class.
            db_session: The SQLAlchemy Session object.
        """
        self.model = model
        self._db_session = db_session

    def _query(self):
        """Returns a base query object for the repository's model."""
        return self._db_session.query(self.model)

    def _filter_soft_deleted(self, query, include_soft_deleted: bool):
        """Adds a filter to exclude or include soft-deleted records."""
        if not include_soft_deleted and hasattr(self.model, "deleted_at"):
            return query.filter(self.model.deleted_at.is_(None))
        return query


    def _apply_filters(self, query, filters: Optional[Dict[str, Any]]):
        """
        Applies structured filters to the query.
    
        filters format example:
        {
            "name": {
                "ilike": ["cola", "pepsi"],   # multiple values allowed
                "ne": "fanta"                 # exclude specific value
            },
            "price": {
                "gte": 10,
                "lte": 50
            }
        }
    
        Supported operators:
        - eq, ne, lt, lte, gt, gte
        - like, ilike
        - in
        """
        if not filters:
            return query
    
        # map simple ops to SQLAlchemy operator names
        op_map = {
            "eq": "__eq__",
            "ne": "__ne__",
            "lt": "__lt__",
            "lte": "__le__",
            "gt": "__gt__",
            "gte": "__ge__",
        }
    
        for field_name, conditions in filters.items():
            if not hasattr(self.model, field_name):
                current_app.logger.warning(f"Unknown filter field: {field_name}")
                continue
    
            column = getattr(self.model, field_name)
    
            # allow shorthand: {"field": "value"} → {"eq": value}
            if not isinstance(conditions, dict):
                conditions = {"eq": conditions}
    
            for op, value in conditions.items():
                if value is None:
                    continue
    
                # normalize single values to list for uniform handling
                values = value if isinstance(value, (list, tuple, set)) else [value]
    
                if op in ("like", "ilike"):
                    clauses = []
                    for v in values:
                        expr = column.like(f"%{v}%") if op == "like" else column.ilike(f"%{v}%")
                        clauses.append(expr)
                    query = query.filter(or_(*clauses))  # match ANY
                elif op == "in":
                    query = query.filter(column.in_(values))
                elif op in op_map:
                    clauses = [getattr(column, op_map[op])(v) for v in values]
                    query = query.filter(or_(*clauses))
                else:
                    current_app.logger.warning(f"Unknown filter operator: {op}")
    
        return query

    def _apply_ordering(self, query, order_by: Optional[List[str]] = None):
        """Applies sorting to the query based on a list of fields."""
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
        """Creates a new model instance and flushes it to the session."""
        entity = self.model(**data)
        self._db_session.add(entity)
        self._db_session.flush()  # Flush to trigger potential IntegrityError
        return entity

    @handle_db_errors
    def get_by_id(self, id_: Any, include_soft_deleted: bool = False) -> Optional[T]:
        """Fetches a single record by its primary key."""
        query = self._query().filter_by(id=id_)
        query = self._filter_soft_deleted(query, include_soft_deleted)
        return query.first()

    @handle_db_errors
    def get_by_uuid(self, uuid: str, include_soft_deleted: bool = False) -> Optional[T]:
        """Fetches a single record by its UUID."""
        query = self._query().filter_by(uuid=uuid)
        query = self._filter_soft_deleted(query, include_soft_deleted)
        return query.first()

    @handle_db_errors
    def delete(self, entity: T, soft: bool = True) -> None:
        """
        Deletes a model instance.

        Args:
            entity: The model instance to delete.
            soft: If True and the model has `deleted_at`, performs a soft delete.
                  Otherwise, performs a hard delete.
        """
        if soft and hasattr(entity, "deleted_at"):
            entity.deleted_at = func.now()
            self._db_session.add(entity)
        else:
            self._db_session.delete(entity)

    @handle_db_errors
    def paginate(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
        include_soft_deleted: bool = False,
    ) -> PaginationResult[T]:
        """
        Performs a paginated query.

        Args:
            page: The page number to retrieve.
            per_page: The number of items per page.
            filters: A dictionary of filters to apply to the query.
            order_by: A list of fields to sort by.
            include_soft_deleted: Whether to include soft-deleted items.

        Returns:
            A PaginationResult named tuple containing the items and pagination info.
        """
        query = self._query()
        query = self._filter_soft_deleted(query, include_soft_deleted)

        filters_copy = filters.copy() if filters else {}
        query = self._apply_filters(query, filters_copy)

        # Using a subquery for count for performance on complex queries
        count_query = query.with_entities(func.count(self.model.id))
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
