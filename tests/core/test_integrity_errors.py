# tests/core/test_integrity_errors.py
import pytest
from apiflask import APIFlask
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
    repo = BaseRepository(model=UniqueEntity, db_session=db_session)
    try:
        yield repo
    finally:
        Base.metadata.drop_all(db_session.bind)


    def test_duplicate_entry_maps_to_custom_exception(integrity_repo):
        app = APIFlask(__name__)
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        with app.app_context():        from flask_devkit.database import db
        db.init_app(app)
        from sqlalchemy.orm import sessionmaker
        engine = db.engine
        Session = sessionmaker(bind=engine)
        session = Session()
        repo = BaseRepository(model=UniqueEntity, db_session=session)

        repo.create({"name": "A"})
        session.commit()

        with pytest.raises(DuplicateEntryError):
            repo.create({"name": "A"})
            session.flush()
