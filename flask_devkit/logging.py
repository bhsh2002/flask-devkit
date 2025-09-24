import logging
from logging.handlers import RotatingFileHandler
import os
from flask import Flask

def init_app(app: Flask):
    """
    Initializes the application's logging configuration.
    Sets up a file handler for production and keeps the default stream handler.
    """
    # Create a formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s [in %(pathname)s:%(lineno)d]'
    )

    # Add a file handler for when not in debug mode
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            try:
                os.mkdir('logs')
            except OSError:
                pass  # Avoid race conditions
        
        file_handler = RotatingFileHandler('logs/server.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

    # Set the level for the default handler (console)
    # The default handler is added by Flask automatically.
    app.logger.setLevel(logging.INFO)
    app.logger.info('Logging system initialized')
