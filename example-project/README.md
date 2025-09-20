# DevKit Showcase Project

This project is a comprehensive demonstration of the `flask-devkit` library, showcasing its advanced, extensible features in a simple blog-like API.

It serves as a practical guide and a template for building your own applications with DevKit.

## A Tour of the Features

This project is explicitly configured to demonstrate the power of `flask-devkit`. Here’s a tour of what to look for in the code:

-   **Centralized Application Factory (`showcase_app/__init__.py`)**
    -   Shows the recommended pattern for initializing `flask-devkit` and its components.
    -   Demonstrates how to register application-specific blueprints alongside DevKit's.

-   **Custom Repository (`showcase_app/repositories/user.py`)**
    -   `CustomUserRepository` inherits from `BaseRepository` to add a new method, `count_active_users`.
    -   This custom class is registered with `DevKit` in the app factory, showcasing the **Repository Overriding** feature.

-   **Custom Service with Hooks (`showcase_app/services/post.py`)**
    -   `PostService` inherits from `BaseService`.
    -   It uses `pre_create_hook` to automatically assign the post's author from the JWT.
    -   It uses `post_get_hook` and `post_list_hook` to dynamically add a calculated `read_time_minutes` field to posts when they are fetched, demonstrating the **Service Read Hooks** feature.

-   **Custom and CRUD Routes (`showcase_app/routes/post.py`)**
    -   Demonstrates the use of `register_crud_routes` to generate a full set of endpoints for the `Post` model.
    -   Shows how to use the `register_custom_route` helper to add a clean, boilerplate-free, non-CRUD endpoint (`/posts/meta/stats`), showcasing the **Custom Route Factory**.

-   **Custom CLI Commands (`showcase_app/cli.py`)**
    -   Includes several custom commands for database management: `init-db`, `truncate-db`, and `drop-db` (with support for SQLite and MySQL).

## Project Setup

1.  **Install Dependencies:**
    Make sure you have [Poetry](https://python-poetry.org/) installed.

    ```bash
    poetry install
    ```

2.  **Environment Variables:**
    Copy the `.env.example` file to a new file named `.env`. This file is loaded automatically when you run `flask` commands.

    ```bash
    cp .env.example .env
    ```
    *It is highly recommended to change `FLASK_JWT_SECRET_KEY` in your new `.env` file.*

3.  **Initialize and Seed the Database:**
    Run the following commands to create the database tables and populate them with default roles, permissions, and an admin user.

    ```bash
    # Create the database and tables
    poetry run flask init-db

    # Seed the database with an admin user
    poetry run flask devkit-seed --admin-username admin --admin-password your_chosen_password
    ```

## Running the Application

```bash
poetry run flask run
```

The API will be available at `http://127.0.0.1:5000`.

### API Documentation (Swagger UI)

This project uses `APIFlask`, which automatically generates interactive API documentation.

Once the application is running, navigate to **http://127.0.0.1:5000/docs** to view and test all available endpoints.

## Custom CLI Commands

This project includes helpful commands for managing your database during development.

-   **`poetry run flask truncate-db`**: Deletes all data from all tables, leaving the structure intact.
-   **`poetry run flask drop-db`**: Deletes the entire database file (SQLite) or schema (MySQL). **Use with caution.**

## Running Tests

```bash
poetry run pytest
```