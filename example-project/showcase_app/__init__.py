import os
from apiflask import APIBlueprint, APIFlask
from dotenv import load_dotenv

from flask_devkit import DevKit

# Import the components we want to customize
from showcase_app.repositories.user import CustomUserRepository


def create_app(config_overrides=None):
    """App factory function."""
    # Manually load .env file to ensure it's available for all commands
    # When running from the root, the cwd is the root, so we need to point to the example project's .env
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(dotenv_path=dotenv_path)

    app = APIFlask(__name__, title="DevKit Showcase API")

    # Load config from .env file (prefixed with FLASK_)
    # and then from any overrides passed to the factory.
    app.config.from_prefixed_env()
    if config_overrides:
        app.config.update(config_overrides)

    # Create a main blueprint that all other blueprints will be registered on
    api_v1_bp = APIBlueprint(
        "api_v1", __name__, url_prefix=app.config.get("DEVKIT_URL_PREFIX", "/api/v1")
    )

    # --- Application-Specific Setup ---
    # Register our application's blueprints onto the main API blueprint first
    from .routes.post import posts_bp
    api_v1_bp.register_blueprint(posts_bp)

    # --- DevKit Setup ---
    # 1. Define a loader to add custom data to JWTs
    def add_custom_claims(user) -> dict:
        # In a real app, you might load this from the user model
        return {"username_initial": user.username[0].upper() if user.username else ""}

    # 2. Instantiate DevKit, passing the custom loader
    devkit = DevKit(additional_claims_loader=add_custom_claims)

    # 3. (Example) Register our custom repository for the user service.
    devkit.register_repository("user", CustomUserRepository)

    # 4. (Example) Make the user list and detail routes public.
    user_routes_config = {
        "list": {"auth_required": False},
        "get": {"auth_required": False},
        "delete": {"permission": "delete:user"}, # Keep delete protected
    }
    devkit.register_routes_config("user", user_routes_config)

    # 5. Initialize DevKit. It will add its own auth routes to our main blueprint
    #    and then register the main blueprint on the app.
    devkit.init_app(app, bp=api_v1_bp)

    return app
