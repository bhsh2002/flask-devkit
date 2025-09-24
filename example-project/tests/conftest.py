# example-project/tests/conftest.py
import pytest
from showcase_app import create_app
from flask_devkit.database import db as _db


@pytest.fixture(scope="session")
def app():
    """Session-wide test Flask application."""
    _app = create_app(
        config_overrides={
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SERVER_NAME": "localhost.localdomain",
        }
    )
    with _app.app_context():
        _db.create_all()
        yield _app
        _db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """
    Provides a transactional database session for each test.
    Rolls back transactions automatically after each test.
    """
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()
        session = _db.Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()
