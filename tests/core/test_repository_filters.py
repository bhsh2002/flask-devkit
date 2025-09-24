# tests/core/test_repository_filters.py
import pytest
from sqlalchemy import Column, Float, Integer, String

from flask_devkit.core.repository import BaseRepository
from tests.helpers import Base


class Sample(Base):
    __tablename__ = "samples_for_filtering"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    value = Column(Integer)
    price = Column(Float)


@pytest.fixture
def filter_repo(db_session):
    Base.metadata.create_all(db_session.bind)
    repo = BaseRepository(model=Sample, db_session=db_session)
    # Add sample data
    repo.create({"name": "apple", "value": 10, "price": 1.5})
    repo.create({"name": "banana", "value": 20, "price": 2.0})
    repo.create({"name": "orange", "value": 20, "price": 2.5})
    repo.create({"name": "pear", "value": 30, "price": 3.0})
    try:
        yield repo
    finally:
        Base.metadata.drop_all(db_session.bind)


def test_filter_eq(filter_repo):
    result = filter_repo.paginate(filters={"name": "apple"})
    assert result.total == 1
    assert result.items[0].name == "apple"


def test_filter_ne(filter_repo):
    result = filter_repo.paginate(filters={"value": "ne__20"})
    assert result.total == 2
    assert {item.name for item in result.items} == {"apple", "pear"}


def test_filter_gt(filter_repo):
    result = filter_repo.paginate(filters={"value": "gt__20"})
    assert result.total == 1
    assert result.items[0].name == "pear"


def test_filter_gte(filter_repo):
    result = filter_repo.paginate(filters={"value": "gte__20"})
    assert result.total == 3


def test_filter_lt(filter_repo):
    result = filter_repo.paginate(filters={"price": "lt__2.0"})
    assert result.total == 1
    assert result.items[0].name == "apple"


def test_filter_lte(filter_repo):
    result = filter_repo.paginate(filters={"price": "lte__2.0"})
    assert result.total == 2


def test_filter_in_list(filter_repo):
    result = filter_repo.paginate(filters={"name": "in__apple|pear"})
    assert result.total == 2


def test_filter_in_string(filter_repo):
    result = filter_repo.paginate(filters={"name": "in__apple, pear"})
    assert result.total == 2


def test_filter_like(filter_repo):
    result = filter_repo.paginate(filters={"name": "like__an"})
    assert result.total == 2
    assert {item.name for item in result.items} == {"banana", "orange"}


def test_filter_ilike(filter_repo):
    result = filter_repo.paginate(filters={"name": "ilike__OR"})
    assert result.total == 1
    assert result.items[0].name == "orange"


def test_filter_multiple_conditions(filter_repo):
    result = filter_repo.paginate(filters={"value": "20", "price": "gt__2.0"})
    assert result.total == 1
    assert result.items[0].name == "orange"
