# Flask-DevKit: The Extensible Flask API Toolkit

`Flask-DevKit` is a powerful, unopinionated toolkit designed to accelerate the development of secure, scalable, and maintainable APIs with Flask. It provides a solid architectural foundation based on proven design patterns like Repository and Unit of Work, while offering complete flexibility to customize, replace, or extend any part of the system.

Unlike rigid frameworks, DevKit is a collection of tools that you can adopt incrementally or use as a complete starting point. It comes with a default, full-featured authentication and RBAC module that can be used out-of-the-box, selectively enabled, or completely replaced with your own logic.

---

## Philosophy: Extensibility First

-   **You are in control:** The library makes no assumptions about your application's needs. Every major component—services, repositories, routes—can be overridden or extended.
-   **Convention over configuration, but configuration when you need it:** Sensible defaults allow for rapid development, but a rich set of registration methods provides hooks to inject your custom logic wherever it's needed.
-   **Solid Architecture:** By providing clean abstractions for the service layer, repository pattern, and unit of work, DevKit helps you build robust applications that are easy to test and maintain.

## Core Components

At its heart, Flask-DevKit consists of several key components that work together.

### 1. The `DevKit` Class

This is the main entry point for the extension. It acts as a central registry for your services and configurations.

-   `devkit.init_app(app, bp)`: Initializes the extension and registers its components.
-   `devkit.register_service(name, service_instance)`: Registers a custom or default service (e.g., `UserService`).
-   `devkit.register_repository(service_name, CustomRepoClass)`: Overrides the default `BaseRepository` for a specific service.
-   `devkit.register_routes_config(service_name, config_dict)`: Overrides the default route settings (e.g., auth requirements) for a service's CRUD endpoints.

### 2. `BaseService`

A generic class for encapsulating business logic. Your own services should inherit from this.

-   **Manages a Repository:** Each service instance holds a repository instance (`self.repo`) for database access.
-   **Lifecycle Hooks:** Provides a rich set of hooks to inject logic before or after operations:
    -   `pre_create_hook`, `pre_update_hook`, `pre_delete_hook`
    -   `pre_get_hook`, `post_get_hook`, `pre_list_hook`, `post_list_hook`

### 3. `BaseRepository`

A generic implementation of the Repository Pattern for SQLAlchemy models.

-   **Encapsulates DB Logic:** Provides standard methods like `create`, `get_by_id`, `paginate`, `delete`, etc.
-   **Extensible:** Create your own repository class inheriting from `BaseRepository` to add custom queries (e.g., `find_by_email`).
-   **Error Handling:** Automatically handles common SQLAlchemy errors and wraps them in custom application exceptions.

### 4. Route Helpers

These functions in `flask_devkit.helpers.routing` dramatically reduce boilerplate when creating API endpoints.

-   `register_crud_routes(...)`: Automatically generates a full set of RESTful CRUD endpoints for a service.
-   `register_custom_route(...)`: A factory for creating custom, non-CRUD endpoints while consistently applying decorators for auth, permissions, validation, and transaction management.

### 5. Unit of Work

The `@unit_of_work` decorator abstracts away session management. It automatically commits the database session on success and rolls back on any exception, ensuring that each request is atomic.

---

## Getting Started: A Practical Guide

Here are common scenarios for using `flask-devkit`.

### Scenario 1: Quick Start with Default Auth

If you need a full-featured authentication and RBAC system immediately, just initialize `DevKit` without registering any services. It will automatically load its default `user`, `role`, and `permission` modules.

```python
# In your app factory
from flask_devkit import DevKit

devkit = DevKit()
# This will load default services and register their routes on api_v1_bp
devkit.init_app(app, bp=api_v1_bp)
```

### Scenario 2: Overriding the User Repository

To add a custom query to the `User` model, you can provide your own repository.

```python
# 1. Define your custom repository
class CustomUserRepository(BaseRepository):
    def find_all_active_users(self):
        return self._query().filter_by(is_active=True).all()

# 2. Register it with DevKit
devkit = DevKit()
devkit.register_repository("user", CustomUserRepository)
devkit.init_app(app, bp=api_v1_bp)

# 3. Access it from your app
with app.app_context():
    user_service = devkit.get_service("user")
    active_users = user_service.repo.find_all_active_users()
```

### Scenario 3: Making User Profiles Public

By default, the user endpoints require authentication. You can change this using `register_routes_config`.

```python
devkit = DevKit()

public_user_routes = {
    "list": {"auth_required": False},  # Make the user list public
    "get": {"auth_required": False},   # Make user detail public
}
devkit.register_routes_config("user", public_user_routes)

devkit.init_app(app, bp=api_v1_bp)
```

### Scenario 4: Adding a Custom Service and Routes

This is the most common scenario: using DevKit's tools to manage your own application models.

```python
# 1. Define your model, schemas, service, and blueprint
class Post(db.Model, ...): ...

post_schemas = create_crud_schemas(Post, ...)

class PostService(BaseService[Post]):
    # Optional: Add custom logic with hooks
    def pre_create_hook(self, data):
        data["author_id"] = get_jwt_identity()
        return data

posts_bp = APIBlueprint("posts", __name__, url_prefix="/posts")
post_service = PostService(model=Post, db_session=db.session)

# 2. Register CRUD routes for your service
register_crud_routes(
    bp=posts_bp,
    service=post_service,
    schemas=post_schemas,
    entity_name="post"
)

# 3. Register your blueprint with the app
app.register_blueprint(posts_bp)
```