# tests/core/test_mixins.py
import pytest
from sqlalchemy import Column, String

from flask_devkit.core.mixins import (
    IDMixin,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDMixin,
)
from tests.helpers import Base


# Define the test model here so it's available for the test function
class SampleEntity(Base, IDMixin, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "sample_entities"
    name = Column(String, default="test")


@pytest.fixture
def sample_entity_repo(db_session):
    Base.metadata.create_all(db_session.bind)
    try:
        yield db_session
    finally:
        Base.metadata.drop_all(db_session.bind)


def test_mixins_populate_fields_on_create(sample_entity_repo):
    """
    Tests if all mixins correctly populate their respective fields
    when a new entity is created, using the fixture-provided session.
    """
    # Action: Create an instance of our test entity and save it
    new_entity = SampleEntity()
    sample_entity_repo.add(new_entity)
    sample_entity_repo.flush()
    sample_entity_repo.refresh(new_entity)

    # Assert: Check that all mixin-provided fields have values
    assert new_entity.id is not None
    assert isinstance(new_entity.id, int)
    assert new_entity.uuid is not None
    assert len(str(new_entity.uuid)) == 36
    assert new_entity.created_at is not None
    assert new_entity.updated_at is not None
    assert new_entity.deleted_at is None