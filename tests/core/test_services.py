# tests/core/test_services.py
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import Column, String
from flask_devkit.core.service import BaseService
from flask_devkit.core.exceptions import DatabaseError, NotFoundError
from flask_devkit.core.mixins import IDMixin
from tests.helpers import Base

# A mock model for testing
class MockModel:
    def __init__(self, id, name):
        self.id = id
        self.name = name

# New Test Class for Service Hooks
class TestBaseServiceHooks:
    @pytest.fixture
    def mock_repo(self):
        repo = MagicMock()
        repo.get_by_id.return_value = MockModel(id=1, name="test_item")
        return repo

    def test_post_get_hook_modifies_entity(self, mock_repo):
        """
        This test will FAIL until the post_get_hook is implemented in BaseService.
        It checks if a hook can modify an entity after it has been retrieved.
        """
        
        class CustomServiceWithHooks(BaseService):
            def post_get_hook(self, entity):
                # This hook should be called by get_by_id and get_by_uuid
                if entity:
                    entity.computed_field = "hook_was_here"
                return entity

        # We need to mock the repository on the service
        service = CustomServiceWithHooks(model=MockModel, db_session=MagicMock())
        service.repo = mock_repo

        # Call the service method
        item = service.get_by_id(1)

        # Assert that the hook was called and modified the item
        assert item is not None
        assert item.computed_field == "hook_was_here"


class TestBaseService:
    @pytest.fixture
    def mock_repo(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_repo):
        # Configure the mock model with a __name__ attribute
        mock_model = MagicMock()
        mock_model.__name__ = "MockModel"
        # We need to mock the repository on the service
        service = BaseService(model=mock_model, db_session=MagicMock())
        service.repo = mock_repo
        return service

    def test_create_calls_repo_create(self, service, mock_repo):
        data = {"name": "test"}
        service.create(data)
        mock_repo.create.assert_called_once_with(data)

    def test_update_fetches_and_updates(self, service, mock_repo):
        mock_entity = MagicMock()
        mock_repo.get_by_id.return_value = mock_entity
        data = {"name": "updated"}
        
        updated_entity = service.update(1, data)
        
        mock_repo.get_by_id.assert_called_once_with(1)
        assert updated_entity is not None
        # Check if the pre_update_hook logic was applied (default behavior)
        assert mock_entity.name == "updated"

    def test_update_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(NotFoundError):
            service.update(1, {"name": "updated"})

    def test_delete_fetches_and_deletes(self, service, mock_repo):
        mock_entity = MagicMock()
        mock_repo.get_by_id.return_value = mock_entity
        
        service.delete(1)
        
        mock_repo.get_by_id.assert_called_once_with(1)
        mock_repo.delete.assert_called_once_with(mock_entity, soft=True)

    def test_delete_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(NotFoundError):
            service.delete(1)

    def test_get_by_id_delegates_to_repo(self, service, mock_repo):
        service.get_by_id(123)
        mock_repo.get_by_id.assert_called_once_with(123, deleted_state="active")

    def test_paginate_delegates_to_repo(self, service, mock_repo):
        service.paginate(page=2, per_page=10)
        mock_repo.paginate.assert_called_once_with(page=2, per_page=10, filters=None, order_by=None, deleted_state="active")

    def test_restore_fetches_soft_deleted_and_restores(self, service, mock_repo):
        mock_entity = MagicMock()
        mock_repo.get_by_id.return_value = mock_entity

        restored_entity = service.restore(1)

        # Verify it searched for the entity including soft-deleted ones
        mock_repo.get_by_id.assert_called_once_with(1, deleted_state="all")
        # Verify the repo's restore method was called
        mock_repo.restore.assert_called_once_with(mock_entity)
        assert restored_entity == mock_entity

    def test_force_delete_fetches_and_hard_deletes(self, service, mock_repo):
        mock_entity = MagicMock()
        mock_repo.get_by_id.return_value = mock_entity

        service.force_delete(1)

        # Verify it searched for the entity including soft-deleted ones
        mock_repo.get_by_id.assert_called_once_with(1, deleted_state="all")
        # Verify the repo's force_delete method was called
        mock_repo.force_delete.assert_called_once_with(mock_entity)



# Define a simple model for testing the service
class ServiceTestModel(Base, IDMixin):
    __tablename__ = "service_test_models"
    name = Column(String)


@pytest.fixture
def test_service(db_session):
    Base.metadata.create_all(db_session.bind)
    yield BaseService(model=ServiceTestModel, db_session=db_session)
    Base.metadata.drop_all(db_session.bind)


def test_create_persists_data(db_session, test_service):
    """Tests that the create method persists data."""
    created_entity = test_service.create({"name": "Bahaa"})
    db_session.commit()
    assert created_entity.id is not None

    fetched_entity = (
        db_session.query(ServiceTestModel).filter_by(id=created_entity.id).one()
    )
    assert fetched_entity.name == "Bahaa"


def test_update_not_found_raises_error(test_service):
    """Tests that updating a non-existent entity raises an error."""
    with pytest.raises(NotFoundError):
        test_service.update(entity_id=999, data={"name": "Ghost"})


def test_service_rolls_back_on_repo_error(db_session, test_service):
    """Tests that the service layer doesn't commit if the repo fails."""
    # Arrange: Create an entity and commit it to start with a clean state.
    initial_entity = ServiceTestModel(name="Initial Name")
    db_session.add(initial_entity)
    db_session.commit()
    entity_id = initial_entity.id

    # Re-fetch to ensure it's in a clean session state for the update
    db_session.query(ServiceTestModel).get(entity_id)

    # Action: Mock a repository method to simulate a failure during the update.
    with patch.object(
        test_service.repo, "get_by_id", side_effect=DatabaseError("Simulated DB Error")
    ):
        with pytest.raises(DatabaseError):
            test_service.update(entity_id=entity_id, data={"name": "Changed Name"})

    # Assert: After the failed operation,
    # the object in the session should have its original name
    # because the transaction managed by the test fixture will be rolled back.
    # We query it again to see its state before the final fixture rollback.
    entity_after_failed_update = db_session.query(ServiceTestModel).get(entity_id)
    assert entity_after_failed_update.name == "Initial Name"
