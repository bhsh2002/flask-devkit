# flask_devkit/core/service.py
"""
Provides a generic BaseService for handling business logic.

This module contains the BaseService class, which orchestrates repository
operations and manages database transactions.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy.orm import Session

from flask_devkit.core.exceptions import NotFoundError
from flask_devkit.core.repository import BaseRepository, PaginationResult

TModel = TypeVar("TModel")
# Allow TRepo to be any subclass of BaseRepository
TRepo = TypeVar("TRepo", bound=BaseRepository)


class BaseService(Generic[TModel]):
    """
    A generic service layer that encapsulates business logic and manages transactions.

    It creates its own repository instance (or accepts a custom one) and ensures
    that all operations are performed within a single database session.
    """

    def __init__(
        self,
        model: Type[TModel],
        db_session: Session,
        repository_class: Type[TRepo] = None,
    ):
        """
        Initializes the service and its underlying repository.

        Args:
            model: The SQLAlchemy model class this service will manage.
            db_session: The SQLAlchemy session to be used for all operations.
            repository_class (optional): A custom repository class to use.
                                         Defaults to BaseRepository.
        """
        self.model = model
        self._db_session = db_session

        # Use the provided repository class or default to BaseRepository
        repo_cls = repository_class or BaseRepository
        self.repo: TRepo = repo_cls(model=self.model, db_session=self._db_session)

    def pre_create_hook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Optional hook to modify data before creating an entity."""
        return data

    def pre_update_hook(self, instance: TModel, data: Dict[str, Any]):
        """Optional hook to apply updates to an entity instance."""
        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

    def pre_delete_hook(self, instance: TModel) -> None:
        """Optional hook to run checks before deleting an entity."""
        pass

    def create(self, data: Dict[str, Any]) -> TModel:
        """Creates a new entity after processing it through the pre-create hook."""
        processed_data = self.pre_create_hook(data)
        entity = self.repo.create(processed_data)
        self._db_session.flush()  # Use flush to get the ID before commit
        self._db_session.refresh(entity)
        return entity

    def update(
        self, entity_id: Any, data: Dict[str, Any], id_field: str = "id"
    ) -> TModel:
        """Updates an existing entity after finding it by the specified field."""
        finder = getattr(self.repo, f"get_by_{id_field}", self.repo.get_by_id)
        entity = finder(entity_id)

        if not entity:
            raise NotFoundError(entity_name=self.model.__name__, entity_id=entity_id)

        self.pre_update_hook(entity, data)
        self._db_session.flush()  # Flush changes to the DB
        return entity

    def delete(self, entity_id: Any, id_field: str = "id", soft: bool = True) -> None:
        """Deletes an entity after finding it by the specified field."""
        finder = getattr(self.repo, f"get_by_{id_field}", self.repo.get_by_id)
        entity = finder(entity_id)

        if not entity:
            raise NotFoundError(entity_name=self.model.__name__, entity_id=entity_id)

        self.pre_delete_hook(entity)
        self.repo.delete(entity, soft=soft)
        return None

    # The rest of the methods are read-only and can delegate directly to the repository
    def get_by_id(
        self, id_: Any, include_soft_deleted: bool = False
    ) -> Optional[TModel]:
        """Fetches a single record by its ID."""
        return self.repo.get_by_id(id_, include_soft_deleted)

    def get_by_uuid(
        self, uuid_: str, include_soft_deleted: bool = False
    ) -> Optional[TModel]:
        """Fetches a single record by its UUID."""
        return self.repo.get_by_uuid(uuid_, include_soft_deleted)

    def paginate(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
        include_soft_deleted: bool = False,
    ) -> PaginationResult[TModel]:
        """Fetches records with pagination."""
        return self.repo.paginate(
            page, per_page, filters, order_by, include_soft_deleted
        )
