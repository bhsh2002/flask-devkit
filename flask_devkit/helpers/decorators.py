# flask_devkit/helpers/decorators.py
from functools import wraps

from flask import current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


def log_activity(f):
    """Logs the entry, exit, and errors of a function call."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_app.logger.info(
            f"Activity: Calling function {f.__name__}"
            f" with args: {args}, kwargs: {kwargs}"
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
