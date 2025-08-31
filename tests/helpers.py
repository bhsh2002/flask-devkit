# tests/helpers.py
from sqlalchemy.orm import declarative_base

# Define a single, shared Base for all test models
Base = declarative_base()
