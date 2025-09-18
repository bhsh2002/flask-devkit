# Changelog

## [Unreleased]

### Fixed
- **Security:** The `log_activity` decorator no longer logs sensitive information (like passwords) from function arguments.
- **Performance:** Fixed an N+1 query issue in the `seed_default_auth` function when seeding default permissions.
- **Robustness:** The `paginate` method in the `BaseRepository` now correctly handles models with custom primary key names.
- **Robustness:** Replaced a broad `except Exception` with a more specific `except ImportError` for optional `flask-jwt-extended` imports.

### Changed
- **Flexibility:** The `url_prefix` for the DevKit blueprint is now configurable via the `DEVKIT_URL_PREFIX` app config variable. This replaces the previous `url_prefix` constructor argument.
- **Refactor:** Simplified the complex `register_crud_routes` function for better readability and maintainability.
- **Refactor:** Removed unsafe `getattr` calls in the `generate_tokens_for_user` service method in favor of direct attribute access.
- The `logout` endpoint has been removed to avoid providing a false sense of security in a stateless JWT environment. Token invalidation is now the client's responsibility.
- The `BaseRepository.get_by_id` method now uses the more efficient `session.get()` for primary key lookups.
- The `init_app` method now uses `app.config.setdefault()` for JWT configuration, allowing users to override default settings.
- Refactored user routes to use a `before_request` handler, eliminating repetitive code and adhering to the DRY principle.

### Added
- Added a generic `find_one_by` method to the `BaseRepository` to provide a reusable way to fetch single records by various criteria.