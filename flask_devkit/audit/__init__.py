from flask import Flask

def init_app(app: Flask):
    """
    Initializes the audit logging system by registering event listeners.
    """
    from . import listeners  # noqa
