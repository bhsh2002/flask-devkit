# DevKit Showcase Project

This project is a demonstration of the `flask-devkit` library, showcasing its features in a simple blog-like API.

## Features

-   **User Authentication:** Login, refresh tokens, and user management provided by `flask-devkit`.
-   **RBAC:** Role-based access control for creating, updating, and deleting posts.
-   **CRUD Operations:** A full set of CRUD endpoints for a `Post` model.
-   **Configurable:** Demonstrates how to configure `flask-devkit` using environment variables.

## Setup

1.  **Install Dependencies:**
    Make sure you have [Poetry](https://python-poetry.org/) installed.

    ```bash
    poetry install
    ```

2.  **Environment Variables:**
    Copy the `.env.example` file to `.env` and update the `JWT_SECRET_KEY`.

    ```bash
    cp .env.example .env
    # Open .env and change the secret key
    ```

3.  **Initialize Database:**
    The database will be created automatically. To create the tables, run the following command:

    ```bash
    poetry run flask init-db
    ```

4.  **Seed the Database:**
    Seed the database with default permissions, roles, and an admin user. You will be prompted to set a password for the admin user.

    ```bash
    poetry run flask devkit-seed
    ```

## Running the Application

```bash
poetry run flask --app showcase_app run
```

The API will be available at `http://127.0.0.1:5000`. The `flask-devkit` routes are under `/api/v1` (as configured in `.env`) and the posts routes are under `/posts`.

## Running Tests

```bash
poetry run pytest
```
