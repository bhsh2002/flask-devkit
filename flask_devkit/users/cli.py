import os
import click
from flask import current_app
from flask.cli import with_appcontext
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

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


@click.command("devkit-init-db")
@with_appcontext
def init_db_command():
    """Create all database tables."""
    db.create_all()
    click.echo("Initialized the database.")


@click.command("devkit-truncate-db")
@with_appcontext
def truncate_db_command():
    """Truncate all tables in the database."""
    if "sqlite" in db.engine.url.drivername:
        db.session.execute(text("PRAGMA foreign_keys=OFF"))
    elif "mysql" in db.engine.url.drivername:
        db.session.execute(text("SET FOREIGN_KEY_CHECKS=0"))

    # Truncate tables in reverse order of dependency
    for table in reversed(db.metadata.sorted_tables):
        db.session.execute(table.delete())
        click.echo(f"Truncated table: {table.name}")

    if "sqlite" in db.engine.url.drivername:
        db.session.execute(text("PRAGMA foreign_keys=ON"))
    elif "mysql" in db.engine.url.drivername:
        db.session.execute(text("SET FOREIGN_KEY_CHECKS=1"))

    db.session.commit()
    click.echo("All tables have been truncated.")


@click.command("devkit-drop-db")
@with_appcontext
def drop_db_command():
    """Drop the database file (SQLite) or schema (MySQL)."""
    db_uri = current_app.config.get("SQLALCHEMY_DATABASE_URI")
    if not db_uri:
        click.echo("SQLALCHEMY_DATABASE_URI is not set.")
        return

    url = make_url(db_uri)

    if "sqlite" in url.drivername:
        # The path is after the third slash
        db_path = db_uri[10:]
        if os.path.exists(db_path):
            click.echo(f"Deleting database file at: {db_path}")
            os.remove(db_path)
            click.echo("Database file deleted.")
        else:
            click.echo("Database file not found.")

    elif "mysql" in url.drivername:
        db_name = url.database
        if not click.confirm(
            f"""Are you sure you want to drop the entire database '{db_name}'?
This action cannot be undone."""
        ):
            click.echo("Database drop cancelled.")
            return

        # Connect to the server without a specific DB
        server_url = url._replace(database=None)
        engine = create_engine(server_url)
        with engine.connect() as conn:
            # Use text() for safe execution
            conn.execute(text(f"DROP DATABASE IF EXISTS `{db_name}`"))
            conn.commit()
        click.echo(f"Database '{db_name}' dropped.")

    else:
        click.echo(f"Driver '{url.drivername}' is not supported by this command.")