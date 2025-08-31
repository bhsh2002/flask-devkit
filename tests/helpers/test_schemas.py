# tests/helpers/test_schemas.py
import datetime

import pytest
from marshmallow import ValidationError
from sqlalchemy import Column, Float, String

from flask_devkit.core.mixins import IDMixin, TimestampMixin, UUIDMixin
from flask_devkit.core.repository import PaginationResult
from flask_devkit.helpers.schemas import create_crud_schemas
from tests.helpers import Base


# 1. Define a test model
class Product(Base, IDMixin, UUIDMixin, TimestampMixin):
    __tablename__ = "schema_test_products"
    name = Column(String(50), nullable=False)
    price = Column(Float, nullable=False)


# 2. Create the schemas once for all tests in this file
schemas = create_crud_schemas(Product)


def test_create_crud_schemas_returns_dict_of_schemas():
    assert isinstance(schemas, dict)
    assert all(
        k in schemas for k in ["main", "input", "update", "query", "pagination_out"]
    )


def test_main_schema_dumps_correctly():
    MainSchema = schemas["main"]
    now = datetime.datetime.now(datetime.timezone.utc)
    product = Product(id=1, name="Laptop", price=1200, created_at=now, updated_at=now)
    result = MainSchema().dump(product)
    assert result["id"] == 1
    assert "uuid" in result
    assert result["name"] == "Laptop"


def test_input_schema_loads_correctly():
    InputSchema = schemas["input"]
    data = {"name": "Keyboard", "price": 75.0}
    loaded_data = InputSchema().load(data)
    assert isinstance(loaded_data, dict)
    assert loaded_data["name"] == "Keyboard"


def test_input_schema_raises_on_missing_required_field():
    InputSchema = schemas["input"]
    data = {"price": 75.0}  # Missing 'name'
    with pytest.raises(ValidationError):
        InputSchema().load(data)


def test_update_schema_allows_partial_data():
    UpdateSchema = schemas["update"]
    data = {"price": 80.0}
    loaded_data = UpdateSchema().load(data, partial=True)
    assert loaded_data["price"] == 80.0


def test_update_schema_fails_on_empty_data():
    UpdateSchema = schemas["update"]
    with pytest.raises(ValidationError):
        UpdateSchema().load({})


def test_pagination_out_schema_works():
    PaginationOutSchema = schemas["pagination_out"]
    product1 = Product(id=1, name="Laptop", price=1200)
    paginated_result = PaginationResult(
        items=[product1],
        total=1,
        page=1,
        per_page=10,
        total_pages=1,
        has_next=False,
        has_prev=False,
    )
    result = PaginationOutSchema().dump(paginated_result)
    assert len(result["items"]) == 1
    assert result["items"][0]["name"] == "Laptop"
    assert result["pagination"]["total"] == 1
