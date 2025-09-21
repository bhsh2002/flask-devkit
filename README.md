# Flask-DevKit: The Extensible Flask API Toolkit

`Flask-DevKit` is a powerful, unopinionated toolkit designed to accelerate the development of secure, scalable, and maintainable APIs with Flask. Thoroughly tested with **over 90% code coverage**, it provides a solid architectural foundation based on proven design patterns like Repository and Unit of Work, while offering complete flexibility to customize, replace, or extend any part of the system.

Unlike rigid frameworks, DevKit is a collection of tools that you can adopt incrementally or use as a complete starting point. It comes with a default, full-featured authentication and RBAC module that can be used out-of-the-box, selectively enabled, or completely replaced with your own logic.

---

## Core Concepts

-   **You are in control:** The library makes no assumptions about your application's needs. Every major component—services, repositories, routes—can be overridden or extended.
-   **Convention over configuration, but configuration when you need it:** Sensible defaults allow for rapid development, but a rich set of registration methods provides hooks to inject your custom logic wherever it's needed.
-   **Solid Architecture:** By providing clean abstractions for the service layer, repository pattern, and unit of work, DevKit helps you build robust applications that are easy to test and maintain.

---

## Usage Guide

This guide covers common use cases, from a quick start to advanced customization.

### Scenario 1: Quick Start with Default Auth

If you need a full-featured authentication and RBAC system immediately, just initialize `DevKit` without registering any of your own services. It will automatically load its default `user`, `role`, and `permission` modules.

```python
# In your app factory (e.g., create_app)
from flask import Flask
from apiflask import APIBlueprint
from flask_devkit import DevKit
from .database import db

def create_app():
    app = Flask(__name__)
    # ... app config ...
    db.init_app(app)

    # 1. Create a master blueprint for your API version
    api_v1_bp = APIBlueprint("api_v1", __name__, url_prefix="/api/v1")

    # 2. Instantiate DevKit
    devkit = DevKit()

    # 3. Initialize. DevKit will load default services and register
    #    their routes (auth, users, roles, etc.) on the blueprint.
    devkit.init_app(app, bp=api_v1_bp)

    return app
```
This will instantly give you endpoints like `/api/v1/auth/login`, `/api/v1/users`, `/api/v1/roles`, etc.

### Scenario 2: Adding Your Own Application Service

This is the most common use case. Here, we add a `Post` model and its related service, schemas, and routes. Because we are registering a service manually, DevKit will **not** load the default auth services.

```python
# In your application factory (e.g., create_app)

# 1. Import your custom service and blueprint
from .services.post import post_service
from .routes.post import posts_bp

# 2. Instantiate DevKit and register your service
devkit = DevKit()
devkit.register_service("post", post_service)

# 3. Initialize the app and DevKit
# ...
devkit.init_app(app) # No blueprint needed if not using default routes

# 4. Register your application's blueprint
app.register_blueprint(posts_bp, url_prefix="/api/v1/posts")

### Important Note on Standalone Usage

As soon as you register even one service manually via `devkit.register_service()`, the automatic loading of the default modules (User, Role, Permission) is **disabled**. This is by design and allows you to use `flask-devkit`'s core features (like `BaseService`, `register_crud_routes`, etc.) for your own models without being tied to the built-in authentication system.

If you want to use your own services **and** the default auth system, you must register the default services manually yourself before calling `init_app`.

```python
from flask_devkit.users.services import UserService, RoleService, PermissionService

devkit = DevKit()
devkit.register_service("user", UserService(...))
devkit.register_service("role", RoleService(...))
devkit.register_service("permission", PermissionService(...))
# ... register your own services
devkit.init_app(app, bp=api_v1_bp)
```

### Core Mixins for Models

To reduce boilerplate in your SQLAlchemy models, DevKit provides several reusable mixins from `flask_devkit.core.mixins`.

-   `Timestamped`: Automatically adds `created_at` and `updated_at` columns to your model, which are managed by the database.

```python
# In your_app/models.py
from flask_devkit.core.mixins import Timestamped
from .database import db

class MyModel(db.Model, Timestamped):
    id = db.Column(db.Integer, primary_key=True)
    # created_at and updated_at are now available on this model
```

---

## Developer Workflow & CLI

Beyond the code-level abstractions, DevKit provides a suite of tools to streamline the entire development lifecycle.

### Database Migrations (Alembic)

The library comes pre-configured with [Alembic](https://alembic.sqlalchemy.org/) to manage your database schema. After changing your SQLAlchemy models, you can generate and apply migrations with standard Alembic commands.

```bash
# 1. Generate a new migration script
poetry run alembic revision --autogenerate -m "Add post model"

# 2. Apply the migration to your database
poetry run alembic upgrade head
```

### Command-Line Interface (CLI)

DevKit includes a powerful CLI for common administrative tasks, built on top of Flask's native CLI. This is exposed via `flask_devkit.users.cli`.

-   **Create Users:** `poetry run flask users create-user <email> --password <password> --is-superuser`
-   **Manage Roles:** `poetry run flask users create-role <name>`
-   **Assign Permissions:** `poetry run flask users grant-permission <role_name> <permission_name>`

This allows you to manage your application from the terminal without needing a UI or direct database access.

### Initial Data Bootstrapping

The `flask_devkit.users.bootstrap` module can be used to seed your database with essential starting data, such as default roles ("admin", "editor") or a superuser account. This is critical for setting up new development or production environments quickly.

```python
# In your app's startup script
from flask_devkit.users.bootstrap import bootstrap_roles

with app.app_context():
    bootstrap_roles()
```

---

## Advanced Usage

### Adding Relationships to Default Models

What if you want to link your own model back to a default DevKit model? For example, you have a `Post` model and you want to be able to access `user.posts`. 

Because Python modules are singletons, you can import the `User` model from the library and attach a SQLAlchemy `relationship` to it *before* your app runs. This is a clean way to extend the default models without modifying the library's source code.

The `example-project` does exactly this:

```python
# In your_app/models/post.py

from sqlalchemy.orm import relationship
from flask_devkit.database import db

class Post(db.Model, ...):
    # ... your columns
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    author = relationship("User", back_populates="posts")

# --- The Magic --- #
# Import the User model from the library
from flask_devkit.users.models import User

# Attach the new relationship to the User class
User.posts = relationship("Post", back_populates="author", lazy="dynamic")
```

### Adding Fields to Default Models (The Profile Pattern)

Directly modifying the tables of default models (e.g., adding a column to the `users` table) is not recommended, as it can lead to conflicts with future library updates. The recommended approach is to create a separate `Profile` model with a one-to-one relationship to the `User` model.

This pattern is highly flexible and keeps your application-specific user data separate from the core authentication data.

```python
# In your_app/models/user_profile.py

from sqlalchemy.orm import relationship
from flask_devkit.database import db
from flask_devkit.users.models import User

class UserProfile(db.Model):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Your custom fields
    full_name = Column(String(100))
    bio = Column(String(255))

    # Create the one-to-one relationship
    user = relationship("User", backref=backref("profile", uselist=False))

# You can then access the profile via `user.profile`
```

---

## Core Utilities & Decorators

DevKit includes several helper decorators and functions to reduce boilerplate.

### `@unit_of_work`

This decorator, found in `flask_devkit.core.unit_of_work`, wraps a function in a database transaction. It automatically handles the session lifecycle for you:

-   **On Success:** It commits the `db.session`.
-   **On Exception:** It rolls back the `db.session`.

It should be applied to any view function that performs database writes (create, update, delete).

```python
from flask_devkit.core.unit_of_work import unit_of_work

@bp.post("/")
@unit_of_work
def create_item(json_data):
    # ... your service logic that writes to the DB ...
    return new_item
```

### `@log_activity`

This decorator from `flask_devkit.helpers.decorators` provides basic logging for function calls. It logs the function name, arguments, and success or failure. For security, it automatically redacts any keyword argument containing the following substrings: `password`, `token`, `secret`, `key`, `authorization`, `bearer`.

### `setup_rate_limiting`

This helper function in `flask_devkit.helpers.decorators` initializes [Flask-Limiter](https://flask-limiter.readthedocs.io/) for your application with a sensible default rate.

```python
# In your app factory
from flask_devkit.helpers.decorators import setup_rate_limiting

def create_app():
    app = Flask(__name__)
    # ...
    setup_rate_limiting(app, default_rate="60/minute")
    return app
```

### Automatic Error Handling

The `register_crud_routes` and `register_custom_route` helpers automatically register a set of error handlers on your blueprint. These handlers catch common exceptions and return structured JSON error responses with the correct HTTP status codes:

-   `NotFoundError` -> `404 Not Found`
-   `BusinessLogicError` / `PermissionDeniedError` -> `400 Bad Request` / `403 Forbidden`
-   `ValidationError` (from Marshmallow) -> `422 Unprocessable Entity`
-   `NoAuthorizationError` (from Flask-JWT-Extended) -> `401 Unauthorized`


# --- In your services/post.py ---
# from flask_devkit.core.service import BaseService
# from ..database import db
# from ..models import Post
# class PostService(BaseService[Post]): ...
# post_service = PostService(model=Post, db_session=db.session)

# --- In your routes/post.py ---
# from apiflask import APIBlueprint
# from flask_devkit.helpers.routing import register_crud_routes
# from ..services.post import post_service
# from ..schemas.post import post_schemas
# posts_bp = APIBlueprint("posts", __name__)
# register_crud_routes(bp=posts_bp, service=post_service, ...)
```

### Scenario 3: Customizing the Default Services

You can use the default auth services but override parts of their behavior.

#### 3.1. Overriding a Repository

Add a custom query method to the `User` repository.

```python
# 1. Define your custom repository
from flask_devkit.core.repository import BaseRepository

class CustomUserRepository(BaseRepository):
    def find_all_active_users(self):
        return self._query().filter_by(is_active=True).all()

# 2. Register it with DevKit before init_app
devkit = DevKit()
devkit.register_repository("user", CustomUserRepository)
devkit.init_app(app, bp=api_v1_bp) # Still init with default services

# 3. Access it from your app
with app.app_context():
    user_service = devkit.get_service("user")
    active_users = user_service.repo.find_all_active_users()
```

#### 3.2. Overriding Route Configurations

Make the user list public and change the permission needed to delete a user.

```python
# 1. Define your custom route config
public_user_routes = {
    "list": {"auth_required": False},
    "get": {"auth_required": False},
    "delete": {"permission": "delete:user_override"}, # Default is delete:user
}

# 2. Register it with DevKit before init_app
devkit = DevKit()
devkit.register_routes_config("user", public_user_routes)
devkit.init_app(app, bp=api_v1_bp)
```

### Scenario 4: Advanced Service Logic with Hooks

Use hooks in your service to inject business logic without rewriting CRUD methods.

```python
# In your services/post.py
from flask_devkit.core.service import BaseService
from flask_devkit.core.exceptions import BusinessLogicError
from flask_jwt_extended import get_jwt_identity

class PostService(BaseService[Post]):
    # Use a hook to inject the author's ID before creating a post
    def pre_create_hook(self, data: dict) -> dict:
        data["author_id"] = get_jwt_identity()
        return data

    # Use a hook to prevent deletion of a published post
    def pre_delete_hook(self, instance: Post) -> None:
        if instance.is_published:
            raise BusinessLogicError("Cannot delete a post that is already published.")
```

### Scenario 5: Creating a Custom, Non-CRUD Route

Create a custom endpoint to `/posts/{id}/publish` that changes a post's status.

```python
# In your routes/post.py
from apiflask import APIBlueprint
from flask_devkit.helpers.routing import register_custom_route
from ..services.post import post_service
from ..schemas.post import post_schema

posts_bp = APIBlueprint("posts", __name__)

# This function will contain the core logic for the endpoint
def publish_post_logic(post_id: int):
    post_service.publish(post_id) # Assume you created a `publish` method
    return {"message": "Post published successfully."}

# The helper function wires up the route, decorators, and logic
register_custom_route(
    bp=posts_bp,
    view_func=publish_post_logic,
    rule="/<int:post_id>/publish",
    methods=["POST"],
    permission="publish:post",
    output_schema=MessageSchema,
)
```

### Scenario 6: Advanced Filtering

The `BaseRepository` supports powerful filtering out-of-the-box. You can pass filters in the query string of any `list` endpoint.

**URL:** `/api/v1/posts?username=eq__john&likes=gte__10&status=in__draft|review`

This URL translates to:
- Posts where `username` equals `john`
- **AND** `likes` are greater than or equal to `10`
- **AND** `status` is in the list `["draft", "review"]`

**Supported Operators:**
- `eq`: equals
- `ne`: not equals
- `lt`: less than
- `lte`: less than or equal to
- `gt`: greater than
- `gte`: greater than or equal to
- `in`: in a `|`-separated list
- `like`: case-sensitive like (`%value%`)
- `ilike`: case-insensitive like (`%value%`)

### Scenario 7: Extending JWT with Custom Claims

You can add your own data to JWT access tokens.

```python
# 1. Define a loader function that takes a User object and returns a dict
def add_custom_claims(user: User) -> dict:
    return {"tenant_id": str(user.tenant_id)}

# 2. Pass it to the DevKit constructor
devkit = DevKit(additional_claims_loader=add_custom_claims)
devkit.init_app(app, bp=api_v1_bp)

# The resulting JWT payload will now contain your custom claim:
# { ..., "roles": ["admin"], "tenant_id": "some-uuid", ... }
```

### Scenario 8: Soft Deleting & Restoration

For applications requiring data to be recoverable, DevKit provides a powerful, built-in soft-delete mechanism.

#### 1. Enabling Soft Deletes on a Model

To make a model "soft-deletable," simply add the `SoftDeleteMixin` from `flask_devkit.core.mixins`. This adds a `deleted_at` nullable timestamp column.

```python
from flask_devkit.core.mixins import SoftDeleteMixin, Timestamped
from .database import db

class MyAuditableModel(db.Model, Timestamped, SoftDeleteMixin):
    id = db.Column(db.Integer, primary_key=True)
    # ... other columns
```

#### 2. How It Works

Once a model uses `SoftDeleteMixin`, the `BaseService` and `BaseRepository` automatically change their behavior:

-   **`service.delete(id)`**: Instead of a `DELETE` statement, this now performs an `UPDATE`, setting the `deleted_at` timestamp. The item is now considered "soft-deleted".
-   **Read Operations**: All read operations (`get_by_id`, `list`, etc.) will **automatically** exclude soft-deleted items from their results.

#### 3. Querying for Soft-Deleted Items

To retrieve a list of items that includes the soft-deleted ones, use the `include_soft_deleted` query parameter on any list endpoint.

**URL:** `/api/v1/my-auditable-models?include_soft_deleted=true`

#### 4. Restoring an Item

You can restore a soft-deleted item using the service layer, which sets its `deleted_at` field back to `NULL`.

```python
# In your application code
from ..services import my_auditable_model_service

my_auditable_model_service.restore(item_id)
```

You can also enable a `/restore` endpoint via the routing helpers. This is **disabled by default**.

```python
# In your routes file
from flask_devkit.helpers.routing import register_crud_routes

crud_config = {
    "restore": {"enabled": True, "permission": "restore:my_model"},
}

register_crud_routes(
    bp=my_bp,
    service=my_service,
    schemas=my_schemas,
    crud_config=crud_config,
)
```
This will create a `POST /my-auditable-models/<id>/restore` endpoint.

#### 5. Permanent Deletion

If you need to permanently delete a record, bypassing the soft-delete mechanism, use the `force_delete` method.

```python
# In your application code
my_auditable_model_service.force_delete(item_id)
```
