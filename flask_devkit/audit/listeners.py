import datetime
from flask import g
from flask_jwt_extended import get_jwt
from sqlalchemy import event
from sqlalchemy.orm import Session, object_session, RelationshipProperty
from sqlalchemy.inspection import inspect

from flask_devkit.audit.models import AuditLog

def get_current_user_id():
    """Tries to get the current user's ID from flask.g or JWT token."""
    try:
        # Attempt to get user_id from request context (g or JWT)
        if hasattr(g, 'user_id'):
            return g.user_id
        return get_jwt()['user_id']
    except RuntimeError:
        # This occurs when not in a Flask request context, e.g., in a CLI command or shell.
        return None
    except KeyError:
        # This occurs if the JWT token is present but doesn't have a 'user_id' claim.
        return None

def _get_pk_value(obj):
    """Gets the primary key value of a model instance as a string."""
    mapper = inspect(obj.__class__)
    pk_cols = [mapper.get_property_by_column(c) for c in mapper.primary_key]
    pk_values = [getattr(obj, prop.key) for prop in pk_cols]
    return ",".join(map(str, pk_values))

def _serialize_value(value):
    """Safely serialize values to be JSON-compatible."""
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    if isinstance(value, datetime.datetime):
        return value.isoformat()
    # For other types (like model instances), return a string representation
    try:
        return str(value)
    except Exception:
        return f"<Unserializable: {type(value).__name__}>"

@event.listens_for(Session, 'before_flush')
def before_flush(session, flush_context, instances):
    """Listen for changes before they are flushed to the database."""
    for instance in session.new:
        if not isinstance(instance, AuditLog):
            _create_audit_log(instance, 'CREATE')

    for instance in session.dirty:
        if not isinstance(instance, AuditLog):
            _create_audit_log(instance, 'UPDATE')

    for instance in session.deleted:
        if not isinstance(instance, AuditLog):
            _create_audit_log(instance, 'DELETE')

def _create_audit_log(instance, action):
    """Helper function to create and add an audit log to the session."""
    session = object_session(instance)
    if not session:
        return

    user_id = get_current_user_id()
    table_name = instance.__tablename__
    record_pk = _get_pk_value(instance)

    old_values = {}
    new_values = {}
    inspr = inspect(instance)

    if action == 'CREATE':
        for attr in inspr.mapper.column_attrs:
            new_values[attr.key] = getattr(instance, attr.key)

    elif action == 'UPDATE':
        for attr in inspr.mapper.column_attrs:
            hist = inspr.get_history(attr.key, True)
            if hist.has_changes():
                old_val = hist.deleted[0] if hist.deleted else None
                new_val = hist.added[0] if hist.added else None
                old_values[attr.key] = _serialize_value(old_val)
                new_values[attr.key] = _serialize_value(new_val)

    elif action == 'DELETE':
        for attr in inspr.mapper.column_attrs:
            old_values[attr.key] = _serialize_value(getattr(instance, attr.key))

    if not old_values and not new_values:
        return  # Don't log if nothing changed

    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        table_name=table_name,
        record_pk=record_pk,
        old_values=old_values,
        new_values=new_values,
    )
    session.add(audit_log)
