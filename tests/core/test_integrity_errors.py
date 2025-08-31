# tests/core/test_integrity_errors.py
import pytest
from flask import Flask
from sqlalchemy import Column, Integer, String, UniqueConstraint

from flask_devkit.core.exceptions import DuplicateEntryError
from flask_devkit.core.repository import BaseRepository
from tests.helpers import Base


class UniqueEntity(Base):
    __tablename__ = "unique_entities"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    __table_args__ = (UniqueConstraint("name", name="uq_unique_name"),)


@pytest.fixture
def integrity_repo(db_session):
    Base.metadata.create_all(db_session.bind)
    yield BaseRepository(model=UniqueEntity, db_session=db_session)
    Base.metadata.drop_all(db_session.bind)


def test_duplicate_entry_maps_to_custom_exception(integrity_repo, db_session):
    app = Flask(__name__)
    with app.app_context():
        integrity_repo.create({"name": "A"})
        db_session.commit()

        with pytest.raises(DuplicateEntryError):
            integrity_repo.create({"name": "A"})
            db_session.flush()  # The decorator catches the error on flush/commit
