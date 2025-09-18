# tests/core/test_repository_pk.py
import pytest
from sqlalchemy import Column, Integer, String
from flask_devkit.core.repository import BaseRepository
from tests.helpers import Base

# 1. Define a model with a custom primary key
class CustomPKWidget(Base):
    __tablename__ = "custom_pk_widgets"
    widget_id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)

# 2. Test that pagination works with the custom PK
def test_paginate_with_custom_pk(db_session):
    """
    Tests that the repository's paginate method works correctly with a
    model that has a non-standard primary key name.
    """
    # Arrange
    repo = BaseRepository(model=CustomPKWidget, db_session=db_session)
    db_session.add(CustomPKWidget(name="Widget 1"))
    db_session.add(CustomPKWidget(name="Widget 2"))
    db_session.commit()

    # Act
    pagination_result = repo.paginate(page=1, per_page=5)

    # Assert
    assert pagination_result.total == 2
    assert len(pagination_result.items) == 2
    assert pagination_result.items[0].name == "Widget 1"
