# flask_devkit/helpers/routing.py
"""
Provides a powerful factory function to auto-generate CRUD REST endpoints.
"""

from typing import Any, Callable, Dict, List, Optional, Type

from apiflask import APIBlueprint
from apiflask.exceptions import HTTPError, _ValidationError
from flask import current_app
from flask_jwt_extended import jwt_required
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from marshmallow.exceptions import ValidationError
from werkzeug.exceptions import HTTPException

from flask_devkit.core.exceptions import AppBaseException, NotFoundError

try:
    from flask_jwt_extended.exceptions import (
        CSRFError,
        FreshTokenRequired,
        NoAuthorizationError,
        RevokedTokenError,
        WrongTokenError,
    )
except ImportError:
    NoAuthorizationError = None
    CSRFError = None
    FreshTokenRequired = None
    RevokedTokenError = None
    WrongTokenError = None
from flask_devkit.auth.decorators import permission_required
from flask_devkit.core.service import BaseService
from flask_devkit.core.unit_of_work import unit_of_work
from flask_devkit.helpers.schemas import MessageSchema


def register_error_handlers(bp: APIBlueprint):
    """Registers standard error handlers for the blueprint."""

    @bp.errorhandler(NotFoundError)
    def handle_not_found(error):
        current_app.logger.info(f"Resource not found: {error.message}")
        return error.to_dict(), 404

    @bp.errorhandler(AppBaseException)
    def handle_app_exception(error):
        current_app.logger.warning(
            f"Application exception: {error.message} (Code: {error.error_code})",
            exc_info=True,
        )
        return error.to_dict(), error.status_code

    @bp.errorhandler(ExpiredSignatureError)
    def handle_expired_token_error(error):
        current_app.logger.info("Request with expired token.")
        return {
            "message": "Token has expired.",
            "error_code": "TOKEN_EXPIRED",
        }, 401

    @bp.errorhandler(InvalidTokenError)
    def handle_invalid_token_error(error):
        current_app.logger.info(f"Request with invalid token: {error}")
        return {
            "message": "Invalid token.",
            "error_code": "INVALID_TOKEN",
        }, 401

    if NoAuthorizationError is not None:

        @bp.errorhandler(NoAuthorizationError)
        def handle_no_auth_error(error):
            current_app.logger.warning("Authorization missing for a request.")
            return {
                "message": "Missing authorization",
                "error_code": "AUTH_REQUIRED",
            }, 401

    if CSRFError is not None:

        @bp.errorhandler(CSRFError)
        def handle_csrf_error(error):
            current_app.logger.warning("CSRF validation failed for a request.")
            return {
                "message": "CSRF validation failed",
                "error_code": "CSRF_FAILED",
            }, 401

    if FreshTokenRequired is not None:

        @bp.errorhandler(FreshTokenRequired)
        def handle_fresh_token_required(error):
            current_app.logger.info("Request requires a fresh token.")
            return {
                "message": "Fresh token required.",
                "error_code": "FRESH_TOKEN_REQUIRED",
            }, 401

    if RevokedTokenError is not None:

        @bp.errorhandler(RevokedTokenError)
        def handle_revoked_token(error):
            current_app.logger.warning("Attempt to use a revoked token.")
            return {
                "message": "Token has been revoked.",
                "error_code": "TOKEN_REVOKED",
            }, 401

    if WrongTokenError is not None:

        @bp.errorhandler(WrongTokenError)
        def handle_wrong_token(error):
            current_app.logger.warning("Attempt to use a wrong token type.")
            return {
                "message": "Wrong token type.",
                "error_code": "WRONG_TOKEN_TYPE",
            }, 401

    @bp.errorhandler(ValidationError)
    def handle_validation_error(error):
        current_app.logger.info(f"Validation failed for request: {error.messages}")
        return {"message": "Validation failed", "errors": error.messages}, 422

    @bp.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handles Werkzeug HTTP exceptions."""
        current_app.logger.info(
            f"HTTP exception: {error.code} {error.name} - {error.description}"
        )
        error_code = error.name.replace(" ", "_").upper()
        return {"message": error.description, "error_code": error_code}, error.code

    @bp.errorhandler(_ValidationError)
    def handle_apifask_validation_error(error):
        """Handles APIFlask validation exceptions."""
        current_app.logger.info(f"APIFlask validation error: {error.message}")
        return {"message": "Validation failed", "errors": error.detail}, 422

    @bp.errorhandler(HTTPError)
    def handle_apifask_http_error(error):
        """Handles APIFlask HTTP exceptions."""
        current_app.logger.info(
            f"APIFlask HTTP exception: {error.status_code} - {error.message}"
        )
        error_code = error.status_code or "HTTP_ERROR"
        return {"message": error.message, "error_code": error_code}, error.status_code

    @bp.errorhandler(Exception)
    def handle_general_error(error):
        current_app.logger.critical("An unhandled exception occurred", exc_info=True)
        return {
            "message": "An internal server error occurred.",
            "error_code": "INTERNAL_SERVER_ERROR",
        }, 500


def _get_schema_details(schema_info, default_location=None):
    """
    Parses a schema definition, which can be a schema class or a dictionary
    with schema, location, and arg_name.
    """
    if isinstance(schema_info, dict):
        schema = schema_info["schema"]
        location = schema_info.get("location", default_location)
        arg_name = schema_info.get("arg_name")
        return schema, location, arg_name
    return schema_info, default_location, None


def _prepare_input_schemes(
    route_cfg: Dict[str, Any], default_schema: Any, http_method: str
) -> List[Dict[str, Any]]:
    """Normalizes input schema config to a list of dicts, injecting default location."""
    input_schema_config = route_cfg.get("input_schema", default_schema)
    if not input_schema_config:
        return []

    configs = (
        input_schema_config
        if isinstance(input_schema_config, list)
        else [input_schema_config]
    )

    normalized_configs = []
    default_location = "query" if http_method == "GET" else "json"

    for config in configs:
        schema_dict = config if isinstance(config, dict) else {"schema": config}
        
        if "location" not in schema_dict:
            schema_dict["location"] = default_location
            
        normalized_configs.append(schema_dict)

    return normalized_configs


def _merge_schema_data(
    schema_configs: List[Dict[str, Any]], **kwargs
) -> Dict[str, Any]:
    """Merges data from multiple schema locations in kwargs."""
    merged_data = {}
    for config in schema_configs:
        _, location, arg_name = _get_schema_details(config)
        # Determine the argument name APIFlask will use
        effective_arg_name = arg_name or f"{location}_data"
        if effective_arg_name in kwargs:
            merged_data.update(kwargs[effective_arg_name])
    return merged_data


def register_crud_routes(
    bp: APIBlueprint,
    service: BaseService,
    schemas: Dict[str, Any],
    entity_name: str,
    *,
    id_field: str = "uuid",
    routes_config: Dict[str, Dict[str, Any]] | None = None,
):
    """
    Registers a standard set of CRUD routes for a given entity.
    This version allows for custom schemas and flexible data location per route.
    """
    register_error_handlers(bp)

    cfg: Dict[str, Dict[str, Any]] = routes_config or {}

    # --- Helper to build a decorated view ---
    def build_view(
        route_name: str,
        view_logic: Callable,
        http_method: str,
        rule: str,
        default_input: Any,
        default_output: Any,
        status_code: int,
        uow: bool,
    ):
        route_cfg = cfg.get(route_name, {})
        if not route_cfg.get("enabled", True):
            return

        auth_required = route_cfg.get("auth_required", True)
        permission = route_cfg.get(
            "permission",
            f"{route_name}:{entity_name}"
            if route_name in ["create", "update", "delete", "restore", "force_delete"]
            else None,
        )
        decorators = route_cfg.get("decorators")

        input_schema_configs = _prepare_input_schemes(route_cfg, default_input, http_method)
        output_schema_info = route_cfg.get("output_schema", default_output)
        output_schema, _, _ = _get_schema_details(output_schema_info)

        def view_wrapper(**kwargs):
            data = _merge_schema_data(input_schema_configs, **kwargs)
            return view_logic(data=data, **kwargs)

        # Assign a unique name to the wrapper function to avoid endpoint conflicts
        view_wrapper.__name__ = f"{route_name}_{entity_name}_view"

        view = view_wrapper
        if uow:
            view = unit_of_work(view)

        if decorators:
            for decorator in reversed(decorators):
                view = decorator(view)
        if permission:
            view = permission_required(permission)(view)
        if auth_required:
            view = jwt_required()(view)

        doc_params = {
            "summary": f"{route_name.replace('_', ' ').capitalize()} {entity_name}"
        }
        if auth_required:
            doc_params["security"] = "bearerAuth"

        final_view = bp.doc(**doc_params)(view)
        if output_schema:
            final_view = bp.output(output_schema, status_code=status_code)(final_view)

        for config in reversed(input_schema_configs):
            schema, location, arg_name = _get_schema_details(config)
            schema_instance = schema(partial=True) if route_name == "update" else schema

            final_view = bp.input(
                schema_instance, location=location, arg_name=arg_name
            )(final_view)

        bp.route(rule, methods=[http_method])(final_view)

    # --- Define View Logics ---
    def list_logic(data, **kwargs):
        filters = data.copy()
        page = filters.pop("page", 1)
        per_page = filters.pop("per_page", 10)
        sort_by_str = filters.pop("sort_by", None)
        deleted_state = filters.pop("deleted_state", "active")
        order_by = [s.strip() for s in sort_by_str.split(",")] if sort_by_str else None
        return service.paginate(
            page=page,
            per_page=per_page,
            filters=filters,
            order_by=order_by,
            deleted_state=deleted_state,
        ), 200

    def list_deleted_logic(data, **kwargs):
        filters = data.copy()
        page = filters.pop("page", 1)
        per_page = filters.pop("per_page", 10)
        sort_by_str = filters.pop("sort_by", None)
        order_by = [s.strip() for s in sort_by_str.split(",")] if sort_by_str else None
        filters.pop("deleted_state", None)
        return service.paginate(
            page=page,
            per_page=per_page,
            filters=filters,
            order_by=order_by,
            deleted_state="deleted_only",
        ), 200

    def get_logic(data, **kwargs):
        item_id = kwargs[id_field]
        item = getattr(service, f"get_by_{id_field}")(item_id)
        if item is None:
            raise NotFoundError(entity_name, item_id)
        return item

    def create_logic(data, **kwargs):
        return service.create(data)

    def update_logic(data, **kwargs):
        item_id = kwargs[id_field]
        return service.update(item_id, data, id_field=id_field)

    def delete_logic(data, **kwargs):
        item_id = kwargs[id_field]
        service.delete(entity_id=item_id, id_field=id_field, data=data)
        return {"message": f"{entity_name.capitalize()} deleted successfully."}

    def restore_logic(data, **kwargs):
        item_id = kwargs[id_field]
        return service.restore(entity_id=item_id, id_field=id_field, data=data)

    def force_delete_logic(data, **kwargs):
        item_id = kwargs[id_field]
        service.force_delete(entity_id=item_id, id_field=id_field, data=data)
        return {"message": f"{entity_name.capitalize()} permanently deleted."}

    # --- Register Routes ---
    build_view(
        "list",
        list_logic,
        "GET",
        "/",
        schemas.get("query"),
        schemas.get("pagination_out"),
        200,
        False,
    )
    build_view(
        "list_deleted",
        list_deleted_logic,
        "GET",
        "/deleted",
        schemas.get("query"),
        schemas.get("pagination_out"),
        200,
        False,
    )
    build_view(
        "get", get_logic, "GET", f"/<{id_field}>", None, schemas.get("main"), 200, False
    )
    build_view(
        "create",
        create_logic,
        "POST",
        "/",
        schemas.get("input"),
        schemas.get("main"),
        201,
        True,
    )
    build_view(
        "update",
        update_logic,
        "PATCH",
        f"/<{id_field}>",
        schemas.get("update"),
        schemas.get("main"),
        200,
        True,
    )
    build_view(
        "delete",
        delete_logic,
        "DELETE",
        f"/<{id_field}>",
        None,
        MessageSchema,
        200,
        True,
    )
    build_view(
        "restore",
        restore_logic,
        "POST",
        f"/<{id_field}>/restore",
        None,
        schemas.get("main"),
        200,
        True,
    )
    build_view(
        "force_delete",
        force_delete_logic,
        "DELETE",
        f"/<{id_field}>/force",
        None,
        MessageSchema,
        200,
        True,
    )


def register_custom_route(
    bp: APIBlueprint,
    rule: str,
    view_func: Callable,
    methods: List[str],
    *,
    input_schemas: Optional[List[Dict[str, Any]]] = None,
    output_schema: Optional[Type] = None,
    permission: Optional[str] = None,
    auth_required: bool = True,
    apply_unit_of_work: bool = False,
    status_code: int = 200,
    doc: Optional[Dict] = None,
    decorators: Optional[List[Callable]] = None,
):
    """
    Registers a custom view function with a standard set of decorators.

    This helper simplifies creating custom endpoints by encapsulating common
    patterns like auth, permissions, schema validation, and transactions.

    Args:
        bp: The APIBlueprint to register the route on.
        rule: The URL rule string.
        view_func: The view function to decorate and register.
        methods: A list of HTTP methods (e.g., ["GET", "POST"]).
        input_schemas: A list of dictionaries for request validation, where
                       each dict contains a 'schema' (Marshmallow schema) and
                       'location' (e.g., 'json', 'query').
        output_schema: The Marshmallow schema for response formatting.
        permission: The permission string required to access the endpoint.
        auth_required: Whether JWT authentication is required. Defaults to True.
        apply_unit_of_work: Whether to wrap the view in a database transaction.
                              Defaults to False.
        status_code: The HTTP status code for a successful response.
        doc: A dictionary for additional OpenAPI documentation.
        decorators: A list of custom decorators to apply to the view function.
    """
    view = view_func

    if decorators:
        for decorator in reversed(decorators):
            view = decorator(view)

    if apply_unit_of_work:
        view = unit_of_work(view)
    if permission:
        view = permission_required(permission)(view)
    if auth_required:
        view = jwt_required()(view)

    doc_params = doc or {}
    if auth_required and "security" not in doc_params:
        doc_params["security"] = "bearerAuth"

    final_view = bp.doc(**doc_params)(view)
    if output_schema:
        final_view = bp.output(output_schema, status_code=status_code)(final_view)

    if input_schemas:
        for input_spec in reversed(input_schemas):
            schema = input_spec["schema"]
            location = input_spec["location"]
            arg_name = input_spec.get("arg_name")
            final_view = bp.input(schema, location=location, arg_name=arg_name)(
                final_view
            )

    bp.route(rule, methods=methods)(final_view)
