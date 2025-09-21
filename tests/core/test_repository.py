# tests/core/test_repository.py
import pytest
from sqlalchemy import Column, Float, String

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
    yield BaseRepository(model=Product, db_session=db_session)
    Base.metadata.drop_all(db_session.bind)


def test_create_and_get(db_session, product_repo):
    product_data = {"name": "Laptop", "price": 1500.0}
    created_product = product_repo.create(product_data)
    db_session.commit()

    assert created_product.id is not None
    retrieved_product = product_repo.get_by_id(created_product.id)
    assert retrieved_product.id == created_product.id
    assert retrieved_product.name == "Laptop"


def test_soft_delete_logic(db_session, product_repo):
    product = product_repo.create({"name": "Mouse", "price": 50.0})
    db_session.commit()
    product_id = product.id

    product_repo.delete(product, soft=True)
    db_session.commit()

    assert product_repo.get_by_id(product_id) is None
    assert product_repo.get_by_id(product_id, include_soft_deleted=True) is not None


def test_restore_logic(db_session, product_repo):
    product = product_repo.create({"name": "Keyboard", "price": 100.0})
    db_session.commit()

    # Soft delete it first
    product_repo.delete(product, soft=True)
    db_session.commit()
    assert product.deleted_at is not None

    # Now, restore it
    product_repo.restore(product)
    db_session.commit()

    restored_product = product_repo.get_by_id(product.id)
    assert restored_product is not None
    assert restored_product.deleted_at is None


def test_force_delete_logic(db_session, product_repo):
    product = product_repo.create({"name": "Webcam", "price": 150.0})
    db_session.commit()
    product_id = product.id

    # Force delete it
    product_repo.force_delete(product)
    db_session.commit()

    # It should be gone, even when including soft-deleted
    assert product_repo.get_by_id(product_id) is None
    assert product_repo.get_by_id(product_id, include_soft_deleted=True) is None



def test_pagination_and_filtering(db_session, product_repo):
    # Arrange
    product_repo.create({"name": "Book", "price": 20.0})
    product_repo.create({"name": "Pen", "price": 2.0})
    product_repo.create({"name": "Notebook", "price": 5.0})
    db_session.commit()

    # Act: filter by name containing "book"
    result = product_repo.paginate(filters={"name": "ilike__book"})

    # Assert
    assert result.total == 2
    assert len(result.items) == 2
    assert {item.name for item in result.items} == {"Book", "Notebook"}
