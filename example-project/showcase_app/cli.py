import click
from flask.cli import with_appcontext

from flask_devkit.database import db


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Create all database tables."""
    db.create_all()
    click.echo("Initialized the database.")
