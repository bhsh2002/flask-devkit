# Flask-DevKit Showcase Application

This project is a showcase application demonstrating the features and usage patterns of the `flask-devkit` library. It is a fully functional API with users, roles, permissions, and a custom `Post` model.

This project is intended to be a practical, real-world example that complements the main library's [documentation](../README.md).

---

## Setup and Running

1.  **Navigate into the project directory:**
    ```bash
    cd example-project
    ```

2.  **Install dependencies:**
    This project uses Poetry for dependency management.
    ```bash
    poetry install
    ```

3.  **Initialize the database:**
    The `flask-devkit` library provides built-in CLI commands for database management.
    ```bash
    poetry run flask devkit-init-db
    ```

4.  **Seed the database with default data:**
    This command creates default permissions, an admin role, and an initial admin user.
    ```bash
    poetry run flask devkit-seed --admin-password a_good_password
    ```

5.  **Run the application:**
    ```bash
    poetry run flask run
    ```
    The API will be available at `http://127.0.0.1:5000`.

---

## Features Demonstrated

This showcase application demonstrates the following `flask-devkit` features:

-   **Default Authentication**: The app uses the default, out-of-the-box authentication and RBAC system.

-   **Repository Overriding**: In `showcase_app/__init__.py`, we register a `CustomUserRepository` to show how you can add custom database logic to default services.

-   **Route Config Overriding**: We make the `GET /users` and `GET /users/{uuid}` endpoints public by registering a custom route configuration.

-   **Custom Service (`PostService`)**: The application includes a `Post` model with its own service, schemas, and routes, demonstrating how to manage your own application models with DevKit's tools.

-   **Advanced Service Hooks**: `services/post.py` shows how to use hooks for business logic:
    -   `pre_create_hook`: To automatically set the `author_id` from the JWT.
    -   `pre_delete_hook`: To prevent the deletion of a post that has been published.
    -   `post_get_hook` & `post_list_hook`: To dynamically add a calculated `read_time_minutes` to the post's API response.

-   **Custom Non-CRUD Route**: `routes/post.py` demonstrates how to create a custom `POST /posts/{uuid}/publish` endpoint using the `register_custom_route` helper.

-   **Custom JWT Claims**: `showcase_app/__init__.py` shows how to use the `additional_claims_loader` to add custom data (`username_initial`) to JWTs.
