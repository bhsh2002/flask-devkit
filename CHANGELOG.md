# Changelog

## [Unreleased]

### Changed
- The `logout` endpoint has been removed to avoid providing a false sense of security in a stateless JWT environment. Token invalidation is now the client's responsibility.
- The `DevKit` constructor now accepts a `url_prefix` parameter to allow customization of the API blueprint's URL prefix.
- The `BaseRepository.get_by_id` method now uses the more efficient `session.get()` for primary key lookups.
- The `init_app` method now uses `app.config.setdefault()` for JWT configuration, allowing users to override default settings.
- Refactored user routes to use a `before_request` handler, eliminating repetitive code and adhering to the DRY principle.

### Added
- Added a generic `find_one_by` method to the `BaseRepository` to provide a reusable way to fetch single records by various criteria.
