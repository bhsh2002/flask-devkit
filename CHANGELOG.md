# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.3] - 2025-09-24

This release introduces a comprehensive database and system event auditing and logging system, and includes a major refactoring of the test suite to improve stability and reliability.

### Added

- **Database Auditing**: A new `DevKitAuditLog` model and corresponding listeners automatically track `CREATE`, `UPDATE`, and `DELETE` operations on all models that use the `BaseRepository`.
- **System Event Logging**: Key security and application events, such as successful/failed logins and unhandled exceptions, are now logged with detailed context.

### Fixed

- **Major Test Suite Refactoring**: Overhauled the entire test suite to fix numerous issues related to database session management and test isolation. This included:
    - Changing the `app` fixture scope to `function` to ensure a clean database for each test.
    - Removing all `db.session.commit()` calls from tests and fixtures, enforcing a transactional testing pattern.
    - Fixing dozens of `no such table` and `AttributeError` errors caused by incorrect fixture setup and session handling.
    - Creating local fixtures for tests with special application configurations to avoid polluting the global test setup.

## [0.2.2] - 2025-09-24

This release introduces a more robust data lifecycle management system, with data archiving and improved endpoints for handling soft-deleted records.

### Added

- **Permanent Deletion Archiving**: When an entity is permanently deleted via `force_delete`, its data is now serialized and moved to a new `archived_records` table instead of being permanently erased from the database. This provides an audit trail for hard deletions.
- **List Soft-Deleted Endpoint**: A new `GET /<resource>/deleted` endpoint has been added to the `register_crud_routes` factory. This allows administrators to view only the items that have been soft-deleted.

### Changed

- **Refactored Soft-Delete Filtering**: The query parameter for controlling soft-delete behavior has been changed from the boolean `include_soft_deleted` to a more flexible `deleted_state` string, which can be `active` (default), `all`, or `deleted_only`. This change was made at the repository, service, and API layers.

## [0.2.1] - 2025-09-21

This release focuses on a comprehensive audit and stabilization of the library, improving code quality, fixing bugs, and enhancing developer ergonomics.

### Added

- **Core DB CLI Commands**: The database management commands (`devkit-init-db`, `devkit-truncate-db`, `devkit-drop-db`) have been moved from the example project into the core library, making them available to all users out-of-the-box.
- **Test Coverage for CLI**: Added a comprehensive test suite for all database CLI commands to ensure their reliability.
- **Test for Manual Service Loader**: Added a specific test to ensure the `additional_claims_loader` is correctly applied even when a `UserService` is registered manually.

### Changed

- **Refactored `RoleService`**: The `RoleService` no longer queries the database directly for `User` or `Role` objects. It now accepts pre-fetched model instances, improving decoupling and making the service layer more consistent.
- **Centralized Config Defaults**: The default `DEVKIT_URL_PREFIX` is now set in a single, dedicated configuration setup function (`_setup_app_config`) for better maintainability.

### Fixed

- **Fixed Failing Test Suite**: Resolved all failing tests, including a critical issue in `test_cli_command` where a Flask app context was not being properly created.
- **`additional_claims_loader` Bug**: Fixed a bug where the `additional_claims_loader` passed to `DevKit` was ignored if a `UserService` was registered manually.
- **Improved `README.md`**: Updated the "Adding a Custom Service" example to be a complete, copy-paste-friendly guide.
- **Multiple Syntax & Logic Errors**: Fixed several cascading bugs and syntax errors that were introduced and discovered during the refactoring process.

## [0.2.0] - 2025-09-20]

This release marks a major refactoring of the library to favor flexibility, extensibility, and developer experience over the previous hard-coded, batteries-included approach.

### Added

- **Selective Module Loading**: The `DevKit` class no longer loads all modules by default. Developers can now instantiate services manually and register them using `devkit.register_service("my_service", my_service_instance)`.
- **Repository Overriding**: Added `devkit.register_repository("service_name", CustomRepoClass)` to allow developers to provide a custom repository class (that inherits from `BaseRepository`) for default services. This enables extending or modifying database logic without forking the library.
- **Read Hooks in `BaseService`**: Introduced `pre_get_hook`, `post_get_hook`, `pre_list_hook`, and `post_list_hook` to `BaseService`, allowing for custom logic injection during read operations (e.g., caching, query modification, entity transformation).
- **Custom Route Factory**: Added a new helper function `register_custom_route` to `flask_devkit.helpers.routing`. It simplifies the creation of custom, non-CRUD endpoints by encapsulating the boilerplate for applying decorators like `jwt_required`, `permission_required`, `unit_of_work`, and schema validation.

### Changed

- **`DevKit` Initialization**: The `DevKit` class is now more flexible. For backward compatibility, if no services are manually registered, it will fall back to loading the default `user`, `role`, and `permission` services.
- **Service `__init__` Methods**: The `UserService`, `RoleService`, and `PermissionService` constructors were updated to accept a `repository_class` argument, enabling the repository override feature.
- **`BaseService` Read Methods**: The `get_by_id`, `get_by_uuid`, and `paginate` methods were updated to integrate the new read hooks.

### Fixed

- Corrected several fragile test setups that were discovered during refactoring, leading to a more robust test suite.
