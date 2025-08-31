# tests/users/test_schemas.py
import pytest
from marshmallow import ValidationError

from flask_devkit.users.models import User


def test_user_main_schema_dumps_correctly(user_schemas):
    MainSchema = user_schemas["main"]()
    user = User(id=1, username="test_dump", password_hash="this_should_not_be_dumped")
    result = MainSchema.dump(user)
    assert result["id"] == 1
    assert result["username"] == "test_dump"
    assert "password_hash" not in result


def test_user_input_schema_loads_correctly(user_schemas):
    InputSchema = user_schemas["input"]()
    data = {"username": "test_load", "password": "a_password"}
    loaded_data = InputSchema.load(data)
    assert isinstance(loaded_data, dict)
    assert loaded_data["username"] == "test_load"
    assert loaded_data["password"] == "a_password"


def test_user_input_schema_raises_on_missing_required_field(user_schemas):
    input_schema = user_schemas["input"]()
    invalid_data = {"password": "a_password"}
    with pytest.raises(ValidationError):
        input_schema.load(invalid_data)


def test_user_update_schema_allows_partial_data(user_schemas):
    update_schema = user_schemas["update"]()
    partial_data = {"username": "new_username"}
    loaded_data = update_schema.load(partial_data, partial=True)
    assert loaded_data["username"] == "new_username"
