# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-09-20

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
