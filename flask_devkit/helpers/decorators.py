# flask_devkit/helpers/decorators.py
import copy
from functools import wraps

from flask import current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

SENSITIVE_KEYS = ["password", "token", "secret", "key", "authorization", "bearer"]


def _filter_sensitive_data(data):
    """Recursively filter sensitive keys from a dictionary."""
    if not isinstance(data, dict):
        return data

    clean_data = {}
    for key, value in data.items():
        if isinstance(key, str) and any(
            sensitive_key in key.lower() for sensitive_key in SENSITIVE_KEYS
        ):
            clean_data[key] = "***"
        elif isinstance(value, dict):
            clean_data[key] = _filter_sensitive_data(value)
        elif isinstance(value, list):
            clean_data[key] = [_filter_sensitive_data(item) for item in value]
        else:
            clean_data[key] = value
    return clean_data


def log_activity(f):
    """Logs the entry, exit, and errors of a function call."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Deepcopy kwargs to avoid modifying the original dictionary
        kwargs_for_logging = copy.deepcopy(kwargs)
        filtered_kwargs = _filter_sensitive_data(kwargs_for_logging)

        current_app.logger.info(
            f"Activity: Calling function {f.__name__}"
            f" with args: {args}, kwargs: {filtered_kwargs}"
        )
        try:
            result = f(*args, **kwargs)
            current_app.logger.info(
                f"Activity: Function {f.__name__} finished successfully."
            )
            return result
        except Exception as e:
            current_app.logger.error(
                f"Activity: Error in function {f.__name__}: {str(e)}",
                exc_info=True,
            )
            raise

    return decorated_function


def setup_rate_limiting(app, default_rate: str = "100/minute"):
    """Attach Flask-Limiter to the app with a sane default rate."""
    limiter = Limiter(get_remote_address, app=app, default_limits=[default_rate])
    return limiter