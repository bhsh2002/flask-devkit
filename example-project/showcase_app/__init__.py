import os

from apiflask import APIBlueprint, APIFlask
from dotenv import load_dotenv

from flask_devkit import DevKit


def create_app(config_overrides=None):
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

    app = APIFlask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")
    app.config.from_prefixed_env()

    if config_overrides:
        app.config.update(config_overrides)

    # Create a main blueprint that all other blueprints will be registered on
    main_bp = APIBlueprint(
        "main_api", __name__, url_prefix=app.config.get("DEVKIT_URL_PREFIX", "/api/v1")
    )

    # Import and register the posts blueprint
    # on the main blueprint *before* initializing DevKit
    from .routes.post import posts_bp

    main_bp.register_blueprint(posts_bp)

    # Initialize extensions, passing the main blueprint to DevKit
    # DevKit will handle registering main_bp on the app
    DevKit(app, bp=main_bp)

    # Register CLI commands
    from . import cli

    app.cli.add_command(cli.init_db_command)

    return app
