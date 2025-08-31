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
        Base.metadata.create_all(db.engine)
        res1 = seed_default_auth(
            db.session, admin_username="admin", admin_password="a_good_password123"
        )
        res2 = seed_default_auth(
            db.session, admin_username="admin", admin_password="a_good_password123"
        )

        assert res1["admin_role_id"] == res2["admin_role_id"]
        assert db.session.query(Permission).count() >= 10
        assert db.session.query(Role).filter_by(name="admin").first() is not None
        assert db.session.query(User).filter_by(username="admin").first() is not None


def test_cli_command(tmp_path):
    runner = CliRunner()
    db_path = tmp_path / "test_cli.db"
    env = {
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "DEVKIT_ADMIN_PASSWORD": "cli_password_123",
    }
    result = runner.invoke(cli_main, ["--admin-username", "cli_admin"], env=env)
    assert result.exit_code == 0
    assert "Seed completed" in result.output
