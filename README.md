# Flask-DevKit: The Extensible Flask API Toolkit

`Flask-DevKit` is a powerful, unopinionated toolkit designed to accelerate the development of secure, scalable, and maintainable APIs with Flask. It provides a solid architectural foundation and a suite of tools to handle common boilerplate, letting you focus on your application's unique business logic.

---

## Documentation

**This README provides a brief overview. For the complete, detailed documentation, please [Click here to view the full documentation](./docs/README.md).**

---

## Key Features

-   **Layered Architecture:** Enforces a clean separation of concerns with a pre-defined Service Layer, Repository Pattern, and Unit of Work.
-   **Automatic CRUD Generation:** Automatically generate full REST API endpoints and corresponding validation schemas from your SQLAlchemy models.
-   **Built-in Auth & RBAC:** A full-featured authentication and Role-Based Access Control system out-of-the-box, including JWT management, user/role/permission models, and permission-based route protection.
-   **Automatic Auditing:** Automatically logs all `CREATE`, `UPDATE`, and `DELETE` operations to an audit trail with no configuration required.
-   **Extensible by Design:** Nearly every component, from services and repositories to routes and JWT claims, can be overridden or extended to fit your needs.
-   **Helper Utilities:** Includes a suite of helpers for database management (CLI commands), error handling, rate limiting, and more.

---

## Quick Start

This example demonstrates setting up a Flask application with the default authentication and user management system provided by `Flask-DevKit`.

1.  **Install the library:**
    ```bash
    poetry add flask-devkit
    ```

2.  **Create your application factory:**

    The library manages the `SQLAlchemy` instance for you. You only need to instantiate `DevKit` and initialize it.

    ```python
    # your_project/app.py
    from apiflask import APIFlask
    from flask_devkit import DevKit

    def create_app():
        app = APIFlask(__name__)

        # Configure your app
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
        app.config["SECRET_KEY"] = "your-super-secret-key-for-jwt"

        # Instantiate and initialize DevKit.
        # This single call handles database setup, auth, routes, and more.
        devkit = DevKit()
        devkit.init_app(app)

        return app
    ```

3.  **Define your models:**

    When defining your own models, import the pre-configured `db` object directly from the library. This ensures your models use the same database session and metadata as the rest of the DevKit.

    ```python
    # your_project/models.py
    from flask_devkit.database import db

    class MyModel(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100))
        # ... your other fields
    ```

4.  **Initialize and seed the database:**
    ```bash
    # Create all database tables
    flask devkit-init-db

    # Create default permissions, an admin role, and an admin user
    flask devkit-seed
    ```

Your application now has a fully functional API at `/api/v1` for logging in, managing users, roles, and permissions.

---

For more advanced scenarios, such as creating your own services, customizing behavior, and using other features, please refer to the **[full documentation](./docs/README.md)**.