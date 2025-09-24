# tests/test_cli.py

from apiflask import APIFlask
from click.testing import CliRunner

from flask_devkit.database import db
from flask_devkit.users.bootstrap import seed_default_auth
from flask_devkit.users.cli import main as cli_main
from flask_devkit.users.models import Base, Permission, Role, User


def test_seed_default_auth_idempotent(tmp_path):
    app = APIFlask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{tmp_path}/seed.db"
    db.init_app(app)
    with app.app_context():
        db.create_all()
        res1 = seed_default_auth(
            session=db.session, admin_username="admin", admin_password="a_good_password123"
        )
        res2 = seed_default_auth(
            session=db.session, admin_username="admin", admin_password="a_good_password123"
        )

        assert res1["admin_role_id"] == res2["admin_role_id"]
        assert db.session.query(Permission).count() >= 10
        admin_role = db.session.query(Role).filter_by(name="admin").first()
        assert admin_role is not None
        admin_user = db.session.query(User).filter_by(username="admin").first()
        assert admin_user is not None
        # Verify the admin user has the admin role
        assert admin_role in admin_user.roles


def test_cli_command(tmp_path):
    app = APIFlask(__name__)
    db_path = tmp_path / "test_cli.db"
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["TESTING"] = True
    db.init_app(app)
    app.cli.add_command(cli_main)

    with app.app_context():
        db.create_all()

    runner = app.test_cli_runner()
    result = runner.invoke(
        cli_main,
        ["--admin-username", "cli_admin", "--admin-password", "cli_password_123"],
    )
    assert result.exit_code == 0
    assert "Seed completed" in result.output


import os
from flask_devkit.users.cli import main as cli_main
from flask_devkit.core.cli import (
    init_db_command,
    truncate_db_command,
    drop_db_command,
)
from flask_devkit.users.bootstrap import seed_default_auth

def test_db_commands(app, db_session):
    """Tests the init-db, truncate-db, and drop-db CLI commands."""
    runner = app.test_cli_runner()

    # 1. Test init-db (should run without error, it's idempotent)
    result_init = runner.invoke(init_db_command)
    assert result_init.exit_code == 0
    assert "Initialized the database" in result_init.output

    # 2. Test truncate-db (and seed some data first)
    runner.invoke(init_db_command)  # Ensure tables are created
    with app.app_context():
        seed_default_auth(
            session=db_session, admin_username="admin", admin_password="password"
        )

    result_truncate = runner.invoke(truncate_db_command)
    assert result_truncate.exit_code == 0
    assert "All tables have been truncated" in result_truncate.output

    # 3. Test drop-db (should not fail, but won't delete in-memory db file)
    result_drop = runner.invoke(drop_db_command)
    assert result_drop.exit_code == 0
    assert "Database file not found" in result_drop.output
