import click
from flask.cli import with_appcontext

from flask_devkit.database import db
from flask_devkit.users.bootstrap import seed_default_auth


@click.command("devkit-seed")
@click.option(
    "--admin-username", default="admin", help="The username for the admin user."
)
@click.password_option("--admin-password", help="The password for the admin user.")
@with_appcontext
def main(admin_username, admin_password):
    """Seeds the database with default permissions, roles, and an admin user."""
    if not admin_password:
        admin_password = click.prompt("Enter password for admin user", hide_input=True)
    results = seed_default_auth(
        session=db.session, admin_username=admin_username, admin_password=admin_password
    )
    click.echo(f"Seed completed: {results}")
