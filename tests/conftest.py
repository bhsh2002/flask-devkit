# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tests.helpers import Base


@pytest.fixture(scope="session")
def engine():
    """Creates a single in-memory SQLite engine for the whole test session."""
    return create_engine("sqlite:///:memory:")


@pytest.fixture(scope="session")
def tables(engine):
    """Creates all tables in the engine once per session."""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(engine, tables):
    """Provides a clean, transactional session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    yield session
    session.close()
    # Roll back the transaction if it's still active.
    if transaction.is_active:
        transaction.rollback()
    connection.close()
