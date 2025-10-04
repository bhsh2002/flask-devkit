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
    """

    def __init__(
        self,
        model: Type[TModel],
        db_session: Session,
        repository_class: Type[TRepo] = None,
    ):
        self.model = model
        self._db_session = db_session
        repo_cls = repository_class or BaseRepository
        self.repo: TRepo = repo_cls(model=self.model, db_session=self._db_session)

    # --- Write Hooks ---
    def pre_create_hook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return data

    def post_create_hook(self, instance: TModel) -> TModel:
        return instance

    def pre_update_hook(self, instance: TModel, data: Dict[str, Any]):
        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

    def post_update_hook(self, instance: TModel) -> TModel:
        return instance

    def pre_delete_hook(self, instance: TModel, data: Optional[Dict[str, Any]] = None) -> None:
        pass

    def post_delete_hook(self, instance: TModel) -> None:
        pass

    def pre_restore_hook(self, instance: TModel, data: Optional[Dict[str, Any]] = None) -> None:
        pass

    def post_restore_hook(self, instance: TModel) -> TModel:
        return instance

    def pre_force_delete_hook(self, instance: TModel, data: Optional[Dict[str, Any]] = None) -> None:
        pass

    def post_force_delete_hook(self, instance: TModel) -> None:
        pass

    # --- Read Hooks ---
    def pre_get_hook(self, id_: Any, id_field: str) -> None:
        pass

    def post_get_hook(self, entity: Optional[TModel]) -> Optional[TModel]:
        return entity

    def pre_list_hook(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return params

    def post_list_hook(
        self, result: PaginationResult[TModel]
    ) -> PaginationResult[TModel]:
        return result

    # --- Write Operations ---
    def create(self, data: Dict[str, Any]) -> TModel:
        processed_data = self.pre_create_hook(data)
        entity = self.repo.create(processed_data)
        self._db_session.flush()
        self._db_session.refresh(entity)
        return self.post_create_hook(entity)

    def update(
        self, entity_id: Any, data: Dict[str, Any], id_field: str = "id"
    ) -> TModel:
        finder = getattr(self.repo, f"get_by_{id_field}", self.repo.get_by_id)
        entity = finder(entity_id)

        if not entity:
            raise NotFoundError(entity_name=self.model.__name__, entity_id=entity_id)

        self.pre_update_hook(entity, data)
        self._db_session.flush()
        self._db_session.refresh(entity)
        return self.post_update_hook(entity)

    def delete(self, entity_id: Any, id_field: str = "id", soft: bool = True, data: Optional[Dict[str, Any]] = None) -> None:
        finder = getattr(self.repo, f"get_by_{id_field}", self.repo.get_by_id)
        entity = finder(entity_id)

        if not entity:
            raise NotFoundError(entity_name=self.model.__name__, entity_id=entity_id)

        self.pre_delete_hook(entity, data)
        self.repo.delete(entity, soft=soft)
        self.post_delete_hook(entity)
        return None

    def restore(self, entity_id: Any, id_field: str = "id", data: Optional[Dict[str, Any]] = None) -> TModel:
        finder = getattr(self.repo, f"get_by_{id_field}", self.repo.get_by_id)
        entity = finder(entity_id, deleted_state="all")

        if not entity:
            raise NotFoundError(entity_name=self.model.__name__, entity_id=entity_id)

        self.pre_restore_hook(entity, data)
        self.repo.restore(entity)
        self._db_session.flush()
        self._db_session.refresh(entity)
        return self.post_restore_hook(entity)

    def force_delete(self, entity_id: Any, id_field: str = "id", data: Optional[Dict[str, Any]] = None) -> None:
        finder = getattr(self.repo, f"get_by_{id_field}", self.repo.get_by_id)
        entity = finder(entity_id, deleted_state="all")

        if not entity:
            raise NotFoundError(entity_name=self.model.__name__, entity_id=entity_id)

        self.pre_force_delete_hook(entity, data)
        self.repo.force_delete(entity)
        self.post_force_delete_hook(entity)
        return None

    # --- Read Operations ---
    def get_by_id(self, id_: Any, deleted_state: str = "active") -> Optional[TModel]:
        self.pre_get_hook(id_, "id")
        entity = self.repo.get_by_id(id_, deleted_state=deleted_state)
        return self.post_get_hook(entity)

    def get_by_uuid(
        self, uuid_: str, deleted_state: str = "active"
    ) -> Optional[TModel]:
        self.pre_get_hook(uuid_, "uuid")
        entity = self.repo.get_by_uuid(uuid_, deleted_state=deleted_state)
        return self.post_get_hook(entity)

    def paginate(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
        deleted_state: str = "active",
    ) -> PaginationResult[TModel]:
        params = {
            "page": page,
            "per_page": per_page,
            "filters": filters,
            "order_by": order_by,
            "deleted_state": deleted_state,
        }
        processed_params = self.pre_list_hook(params)
        result = self.repo.paginate(**processed_params)
        return self.post_list_hook(result)
