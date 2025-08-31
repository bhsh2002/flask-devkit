# flask_devkit/core/unit_of_work.py
from functools import wraps

from flask import current_app

from flask_devkit.database import db


def unit_of_work(f):
    """
    A decorator that wraps a function in a transactional block.
    It commits the session if the function executes successfully and rolls back
    on any exception.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            result = f(*args, **kwargs)
            db.session.commit()
            return result
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Transaction failed in {f.__name__}. Rolling back. Error: {e}",
                exc_info=True,
            )
            raise

    return decorated_function
