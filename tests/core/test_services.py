# tests/core/test_services.py
from unittest.mock import patch

import pytest
from sqlalchemy import Column, String

from flask_devkit.core.exceptions import DatabaseError, NotFoundError
from flask_devkit.core.mixins import IDMixin
from flask_devkit.core.service import BaseService
from tests.helpers import Base


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
