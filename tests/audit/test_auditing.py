"""
Tests for the database auditing functionality.
"""
import pytest
from flask_devkit.audit.models import AuditLog
from flask_devkit.users.models import User


def test_create_audit(client, db_session, admin_auth_headers):
    """Test that creating a new user creates an audit log entry."""
    db_session.query(AuditLog).delete()
    db_session.commit()

    user_data = {"username": "audit_user_create", "password": "password123"}
    response = client.post("/api/v1/users/", json=user_data, headers=admin_auth_headers)
    assert response.status_code == 201

    audit_logs = db_session.query(AuditLog).all()
    assert len(audit_logs) >= 1  # Can be more than 1 due to other test users
    log = audit_logs[-1]  # Check the last log entry
    assert log.action == "CREATE"
    assert log.table_name == "users"
    assert log.new_values['username'] == "audit_user_create"


def test_update_audit(client, db_session, admin_auth_headers):
    """Test that updating a user creates an audit log entry."""
    user = User(username="audit_user_update", password_hash="x")
    db_session.add(user)
    db_session.commit()

    db_session.query(AuditLog).delete()
    db_session.commit()

    update_data = {"is_active": False}
    response = client.patch(
        f"/api/v1/users/{user.uuid}", json=update_data, headers=admin_auth_headers
    )
    assert response.status_code == 200

    audit_logs = db_session.query(AuditLog).filter(AuditLog.action == 'UPDATE').all()
    assert len(audit_logs) >= 1
    log = audit_logs[-1]
    assert log.action == "UPDATE"
    assert log.table_name == "users"
    assert log.record_pk == str(user.id)
    assert log.old_values['is_active'] is True
    assert log.new_values['is_active'] is False


def test_delete_audit(client, db_session, admin_auth_headers):
    """Test that deleting a user creates an audit log entry."""
    user = User(username="audit_user_delete", password_hash="x")
    db_session.add(user)
    db_session.commit()

    db_session.query(AuditLog).delete()
    db_session.commit()

    response = client.delete(f"/api/v1/users/{user.uuid}", headers=admin_auth_headers)
    assert response.status_code == 200

    audit_logs = db_session.query(AuditLog).filter(AuditLog.action == 'UPDATE').all()
    assert len(audit_logs) >= 1
    log = audit_logs[-1]
    assert log.action == "UPDATE"
    assert log.table_name == "users"
    assert log.record_pk == str(user.id)
    assert log.new_values['deleted_at'] is not None
