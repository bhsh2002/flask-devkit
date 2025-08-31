# Flask-DevKit

A comprehensive Flask extension for rapid, secure API development with built-in JWT authentication and RBAC.

## Features

*   **Flask Extension Pattern**: Integrates seamlessly with your Flask app using the standard `init_app` pattern.
*   **Structured Architecture**: Enforces a clear separation of concerns between the data access layer (Repository), business logic (Service), and the API (Routes).
*   **Automatic CRUD Generation**: Provides powerful factories to generate complete CRUD API endpoints from your models.
*   **Centralized Transaction Management**: Uses a Unit of Work pattern to ensure database operations are atomic.
*   **Generic Repository & Service Layers**: Encapsulates common database and business logic for reusability.
*   **Reusable Database Components**: Comes with ready-to-use SQLAlchemy Mixins for common fields (`id`, `uuid`, timestamps, soft deletes).
*   **Unified Exception System**: Provides custom exceptions that automatically translate into consistent JSON error responses.
*   **Built-in Security**: Includes decorators to verify JWT authentication and permissions at the route level.
*   **Database Migrations**: Integrated with Alembic for easy database schema management.

## Requirements

*   Python 3.11+
*   Flask & APIFlask
*   SQLAlchemy & Flask-SQLAlchemy
*   Flask-JWT-Extended
*   Alembic

## Installation

1.  Ensure you have Poetry installed.
2.  Install the dependencies from your project's root:
    ```bash
    poetry install
    ```

## Quick Start

`Flask-DevKit` is designed to be the foundation for your Flask project's authentication and authorization system. Here’s how to integrate it.

**In your main `app.py`:**
```python
from apiflask import APIFlask
from flask_devkit import DevKit
from flask_devkit.database import db
from flask_devkit.users.bootstrap import seed_default_auth

app = APIFlask(__name__)

# 1. Configure your database and JWT secret key
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["JWT_SECRET_KEY"] = "your-super-secret-key"

# 2. Initialize the extension
dev_kit = DevKit(app)

# 3. (Optional) Create tables and seed default data
with app.app_context():
    db.create_all()
    # Seed the database with default permissions, admin role, and an admin user
    seed_default_auth(db.session, admin_username="admin", admin_password="your_password")
```

This sets up all the necessary endpoints for authentication, user management, and RBAC.

## Advanced Usage

### Custom JWT Claims

You can add custom data to your JWT access tokens by providing a loader function during initialization.

```python
from flask_devkit.users.models import User

def add_custom_claims(user: User) -> dict:
    """Returns a dictionary of custom claims to add to the JWT."""
    return {"organization_id": user.organization_id} # Example

# When initializing
dev_kit = DevKit(app, additional_claims_loader=add_custom_claims)
```

## Database Migrations

This library is integrated with Alembic to manage database schema changes.

-   **Set Database URL**: Before running Alembic commands, ensure the `SQLALCHEMY_DATABASE_URI` environment variable is set.
    ```bash
    export SQLALCHEMY_DATABASE_URI="your-database-uri"
    ```
-   **Generate a New Migration**: After changing your SQLAlchemy models, generate a new migration script automatically:
    ```bash
    poetry run alembic revision --autogenerate -m "A description of your changes"
    ```
-   **Apply Migrations**: Apply the latest migrations to your database.
    ```bash
    poetry run alembic upgrade head
    ```

## Running Tests

The project comes with a comprehensive test suite. To run it:
```bash
poetry run pytest
```