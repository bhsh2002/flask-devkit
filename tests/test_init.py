# tests/test_init.py
from apiflask import APIFlask
import pytest

from flask_devkit import DevKit

@pytest.fixture
def app():
    app = APIFlask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['JWT_SECRET_KEY'] = 'init-secret'
    return app

def test_devkit_uses_default_url_prefix(app):
    """
    Tests that DevKit uses the default '/api/v1' prefix if not specified.
    """
    DevKit(app)
    assert 'api_v1' in app.blueprints
    assert app.blueprints['api_v1'].url_prefix == '/api/v1'

def test_devkit_uses_custom_url_prefix_from_config(app):
    """
    Tests that DevKit uses a custom URL prefix from the app's config.
    """
    app.config["DEVKIT_URL_PREFIX"] = "/custom/api"
    DevKit(app)
    assert 'api_v1' in app.blueprints
    assert app.blueprints['api_v1'].url_prefix == "/custom/api"
