# Flask-DevKit: The Extensible Flask API Toolkit

`Flask-DevKit` is a powerful, unopinionated toolkit designed to accelerate the development of secure, scalable, and maintainable APIs with Flask. It provides a solid architectural foundation based on proven design patterns like Repository and Unit of Work, while offering complete flexibility to customize, replace, or extend any part of the system.

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
