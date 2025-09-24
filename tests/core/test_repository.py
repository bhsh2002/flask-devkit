# tests/core/test_repository.py
import pytest
from sqlalchemy import Column, Float, String

from flask_devkit.core.archive import ArchivedRecord
from flask_devkit.core.mixins import (
    IDMixin,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDMixin,
)
from flask_devkit.core.repository import BaseRepository
from tests.helpers import Base


# Define a simple model for testing the repository
class Product(Base, IDMixin, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "products_test"
    name = Column(String(50), nullable=False)
    price = Column(Float, nullable=False)


@pytest.fixture
def product_repo(db_session):
    Base.metadata.create_all(db_session.bind)
    ArchivedRecord.metadata.create_all(db_session.bind)
    repo = BaseRepository(model=Product, db_session=db_session)
    try:
        yield repo
    finally:
        Base.metadata.drop_all(db_session.bind)
        ArchivedRecord.metadata.drop_all(db_session.bind)


def test_create_and_get(db_session, product_repo):
    product_data = {"name": "Laptop", "price": 1500.0}
    created_product = product_repo.create(product_data)

    assert created_product.id is not None
    retrieved_product = product_repo.get_by_id(created_product.id)
    assert retrieved_product.id == created_product.id
    assert retrieved_product.name == "Laptop"


def test_soft_delete_logic(db_session, product_repo):
    product = product_repo.create({"name": "Mouse", "price": 50.0})
    product_id = product.id

    product_repo.delete(product, soft=True)

    assert product_repo.get_by_id(product_id) is None
    assert product_repo.get_by_id(product_id, deleted_state="all") is not None


def test_restore_logic(db_session, product_repo):
    product = product_repo.create({"name": "Keyboard", "price": 100.0})

    # Soft delete it first
    product_repo.delete(product, soft=True)
    assert product.deleted_at is not None

    # Now, restore it
    product_repo.restore(product)

    restored_product = product_repo.get_by_id(product.id)
    assert restored_product is not None
    assert restored_product.deleted_at is None


def test_force_delete_archives_record(db_session, product_repo):
    """
    Tests if force_delete moves the record to the archive table.
    """
    product = product_repo.create({"name": "Monitor", "price": 300.0})
    product_id = product.id
    product_uuid = product.uuid
    product_name = product.name

    # Act: Force delete the product
    product_repo.force_delete(product)

    # Assert: Check that the original product is gone
    assert product_repo.get_by_id(product_id, deleted_state="all") is None

    # Assert: Check that the record was archived
    archived_repo = BaseRepository(model=ArchivedRecord, db_session=db_session)
    archived_records = archived_repo.paginate().items
    assert len(archived_records) == 1

    archived_record = archived_records[0]
    assert archived_record.original_table == "products_test"
    assert archived_record.original_pk == str(product_id)
    assert archived_record.data["uuid"] == str(product_uuid)
    assert archived_record.data["name"] == product_name


def test_pagination_and_filtering(db_session, product_repo):
    # Arrange
    product_repo.create({"name": "Book", "price": 20.0})
    product_repo.create({"name": "Pen", "price": 2.0})
    product_repo.create({"name": "Notebook", "price": 5.0})

    # Act: filter by name containing "book"
    result = product_repo.paginate(filters={"name": "ilike__book"})

    # Assert
    assert result.total == 2
    assert len(result.items) == 2
    assert {item.name for item in result.items} == {"Book", "Notebook"}


def test_pagination_with_deleted_states(db_session, product_repo):
    """Tests pagination with different soft-delete states."""
    # Arrange
    product_repo.create({"name": "Active Product 1", "price": 10.0})
    product_repo.create({"name": "Active Product 2", "price": 20.0})
    p3 = product_repo.create({"name": "Deleted Product", "price": 30.0})
    product_repo.delete(p3, soft=True)

    # Act & Assert: Default (active)
    active_result = product_repo.paginate()
    assert active_result.total == 2
    assert {item.name for item in active_result.items} == {
        "Active Product 1",
        "Active Product 2",
    }

    # Act & Assert: Deleted Only
    deleted_result = product_repo.paginate(deleted_state="deleted_only")
    assert deleted_result.total == 1
    assert deleted_result.items[0].name == "Deleted Product"

    # Act & Assert: All
    all_result = product_repo.paginate(deleted_state="all")
    assert all_result.total == 3
    assert {item.name for item in all_result.items} == {
        "Active Product 1",
        "Active Product 2",
        "Deleted Product",
    }