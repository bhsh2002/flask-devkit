# flask_devkit/users/cli.py
import os

import click
from apiflask import APIFlask

from flask_devkit.database import db
from flask_devkit.users.bootstrap import seed_default_auth


def build_app() -> APIFlask:
    app = APIFlask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "SQLALCHEMY_DATABASE_URI", "sqlite:///devkit.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    from flask_devkit.users.models import Base as UsersBase

    with app.app_context():
        UsersBase.metadata.create_all(db.engine)
    return app


@click.command(name="devkit-seed")
@click.option(
    "--admin-username",
    default=lambda: os.getenv("DEVKIT_ADMIN_USERNAME", "admin"),
    help="Admin username",
)
@click.option(
    "--admin-password",
    default=lambda: os.getenv("DEVKIT_ADMIN_PASSWORD", "change-me"),
    help="Admin password",
)
def main(admin_username: str, admin_password: str):
    """Seed default auth data (roles, permissions, admin user)."""
    app = build_app()
    with app.app_context():
        res = seed_default_auth(
            db.session, admin_username=admin_username, admin_password=admin_password
        )
        click.echo(f"Seed completed: {res}")


if __name__ == "__main__":
    main()
