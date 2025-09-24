# flask_devkit/helpers/routing.py
"""
Provides a powerful factory function to auto-generate CRUD REST endpoints.
"""

from typing import Any, Callable, Dict, List, Optional, Type

from apiflask import APIBlueprint
from flask import current_app
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from flask_devkit.core.exceptions import AppBaseException, NotFoundError

try:
    from flask_jwt_extended.exceptions import CSRFError, NoAuthorizationError
except ImportError:
    NoAuthorizationError = None
    CSRFError = None
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

    @bp.errorhandler(ValidationError)
    def handle_validation_error(error):
        current_app.logger.info(f"Validation failed for request: {error.messages}")
        return {"message": "Validation failed", "errors": error.messages}, 422

    @bp.errorhandler(Exception)
    def handle_general_error(error):
        current_app.logger.critical("An unhandled exception occurred", exc_info=True)
        return {
            "message": "An internal server error occurred.",
            "error_code": "INTERNAL_SERVER_ERROR",
        }, 500


def register_crud_routes(
    bp: APIBlueprint,
    service: BaseService,
    schemas: Dict[str, Type],
    entity_name: str,
    *,
    id_field: str = "uuid",
    routes_config: Dict[str, Dict[str, Any]] | None = None,
):
    """
    Registers a standard set of CRUD routes for a given entity.
    This refactored version applies decorators directly for better readability.
    """
    register_error_handlers(bp)

    main_schema = schemas["main"]
    input_schema = schemas["input"]
    update_schema = schemas["update"]
    query_schema = schemas["query"]
    pagination_out_schema = schemas["pagination_out"]

    if id_field not in {"id", "uuid"}:
        raise ValueError("id_field must be either 'id' or 'uuid'")

    cfg: Dict[str, Dict[str, Any]] = routes_config or {}

    # --- Route: List ---
    if cfg.get("list", {}).get("enabled", True):
        route_cfg = cfg.get("list", {})
        auth_required = route_cfg.get("auth_required", True)
        permission = route_cfg.get("permission")
        decorators = route_cfg.get("decorators")

        def list_items(query_data):
            """Retrieve a paginated list of items."""
            filters = query_data.copy()
            page = filters.pop("page", 1)
            per_page = filters.pop("per_page", 10)
            sort_by_str = filters.pop("sort_by", None)
            deleted_state = filters.pop("deleted_state", "active")
            order_by = (
                [s.strip() for s in sort_by_str.split(",") if s.strip()]
                if sort_by_str
                else None
            )

            return (
                service.paginate(
                    page=page,
                    per_page=per_page,
                    filters=filters,
                    order_by=order_by,
                    deleted_state=deleted_state,
                ),
                200,
            )

        view = list_items
        if decorators:
            for decorator in reversed(decorators):
                view = decorator(view)
        if permission:
            view = permission_required(permission)(view)
        if auth_required:
            view = jwt_required()(view)

        doc_params = {"summary": f"List all {entity_name}s"}
        if auth_required:
            doc_params["security"] = "bearerAuth"

        bp.get("/")(
            bp.input(query_schema, location="query")(
                bp.output(pagination_out_schema)(bp.doc(**doc_params)(view))
            )
        )

    # --- Route: List Deleted ---
    if cfg.get("list_deleted", {}).get("enabled", False):
        route_cfg = cfg.get("list_deleted", {})
        auth_required = route_cfg.get("auth_required", True)
        permission = route_cfg.get("permission", f"list_deleted:{entity_name}")
        decorators = route_cfg.get("decorators")

        def list_deleted_items(query_data):
            """Retrieve a paginated list of soft-deleted items."""
            filters = query_data.copy()
            page = filters.pop("page", 1)
            per_page = filters.pop("per_page", 10)
            sort_by_str = filters.pop("sort_by", None)
            order_by = (
                [s.strip() for s in sort_by_str.split(",") if s.strip()]
                if sort_by_str
                else None
            )
            filters.pop("deleted_state", None)  # Remove to avoid conflict

            return (
                service.paginate(
                    page=page,
                    per_page=per_page,
                    filters=filters,
                    order_by=order_by,
                    deleted_state="deleted_only",
                ),
                200,
            )

        view = list_deleted_items
        if decorators:
            for decorator in reversed(decorators):
                view = decorator(view)
        if permission:
            view = permission_required(permission)(view)
        if auth_required:
            view = jwt_required()(view)

        doc_params = {"summary": f"List all soft-deleted {entity_name}s"}
        if auth_required:
            doc_params["security"] = "bearerAuth"

        bp.get("/deleted")(
            bp.input(query_schema, location="query")(
                bp.output(pagination_out_schema)(bp.doc(**doc_params)(view))
            )
        )

    # --- Route: Get ---
    if cfg.get("get", {}).get("enabled", True):
        route_cfg = cfg.get("get", {})
        auth_required = route_cfg.get("auth_required", True)
        permission = route_cfg.get("permission")
        decorators = route_cfg.get("decorators")

        def get_item(**kwargs):
            """Retrieve a single item by its ID or UUID."""
            item_id = kwargs[id_field]
            method_to_call = getattr(service, f"get_by_{id_field}")
            item = method_to_call(item_id)
            if item is None:
                raise NotFoundError(entity_name, item_id)
            return item

        view = get_item
        if decorators:
            for decorator in reversed(decorators):
                view = decorator(view)
        if permission:
            view = permission_required(permission)(view)
        if auth_required:
            view = jwt_required()(view)

        doc_params = {"summary": f"Get a single {entity_name}"}
        if auth_required:
            doc_params["security"] = "bearerAuth"

        bp.get(f"/<{id_field}>")(
            bp.output(main_schema)(bp.doc(**doc_params)(view))
        )

    # --- Route: Create ---
    if cfg.get("create", {}).get("enabled", True):
        route_cfg = cfg.get("create", {})
        auth_required = route_cfg.get("auth_required", True)
        permission = route_cfg.get("permission", f"create:{entity_name}")
        decorators = route_cfg.get("decorators")

        def create_item(json_data):
            """Create a new item."""
            return service.create(json_data)

        view = unit_of_work(create_item)
        if decorators:
            for decorator in reversed(decorators):
                view = decorator(view)
        if permission:
            view = permission_required(permission)(view)
        if auth_required:
            view = jwt_required()(view)

        doc_params = {"summary": f"Create a new {entity_name}"}
        if auth_required:
            doc_params["security"] = "bearerAuth"

        bp.post("/")(
            bp.input(input_schema)(
                bp.output(main_schema, status_code=201)(bp.doc(**doc_params)(view))
            )
        )

    # --- Route: Update ---
    if cfg.get("update", {}).get("enabled", True):
        route_cfg = cfg.get("update", {})
        auth_required = route_cfg.get("auth_required", True)
        permission = route_cfg.get("permission", f"update:{entity_name}")
        decorators = route_cfg.get("decorators")

        def update_item(json_data, **kwargs):
            """Update a single item."""
            item_id = kwargs[id_field]
            return service.update(item_id, json_data, id_field=id_field)

        view = unit_of_work(update_item)
        if decorators:
            for decorator in reversed(decorators):
                view = decorator(view)
        if permission:
            view = permission_required(permission)(view)
        if auth_required:
            view = jwt_required()(view)

        doc_params = {"summary": f"Update an existing {entity_name}"}
        if auth_required:
            doc_params["security"] = "bearerAuth"

        bp.patch(f"/<{id_field}>")(
            bp.input(update_schema(partial=True))(bp.output(main_schema)(bp.doc(**doc_params)(view)))
        )

    # --- Route: Delete ---
    if cfg.get("delete", {}).get("enabled", True):
        route_cfg = cfg.get("delete", {})
        auth_required = route_cfg.get("auth_required", True)
        permission = route_cfg.get("permission", f"delete:{entity_name}")
        decorators = route_cfg.get("decorators")

        def delete_item(**kwargs):
            """Delete a single item."""
            item_id = kwargs[id_field]
            service.delete(entity_id=item_id, id_field=id_field)
            return {"message": f"{entity_name.capitalize()} deleted successfully."}

        view = unit_of_work(delete_item)
        if decorators:
            for decorator in reversed(decorators):
                view = decorator(view)
        if permission:
            view = permission_required(permission)(view)
        if auth_required:
            view = jwt_required()(view)

        doc_params = {"summary": f"Delete an {entity_name}"}
        if auth_required:
            doc_params["security"] = "bearerAuth"

        bp.delete(f"/<{id_field}>")(
            bp.output(MessageSchema, status_code=200)(bp.doc(**doc_params)(view))
        )

    # --- Route: Restore ---
    if cfg.get("restore", {}).get("enabled", False): # Disabled by default
        route_cfg = cfg.get("restore", {})
        auth_required = route_cfg.get("auth_required", True)
        permission = route_cfg.get("permission", f"restore:{entity_name}")

        def restore_item(**kwargs):
            """Restore a soft-deleted item."""
            item_id = kwargs[id_field]
            return service.restore(item_id, id_field=id_field)

        view = unit_of_work(restore_item)
        if permission:
            view = permission_required(permission)(view)
        if auth_required:
            view = jwt_required()(view)

        doc_params = {"summary": f"Restore a soft-deleted {entity_name}"}
        if auth_required:
            doc_params["security"] = "bearerAuth"

        bp.post(f"/<{id_field}>/restore")(
            bp.output(main_schema)(bp.doc(**doc_params)(view))
        )

    # --- Route: Force Delete ---
    if cfg.get("force_delete", {}).get("enabled", False): # Disabled by default
        route_cfg = cfg.get("force_delete", {})
        auth_required = route_cfg.get("auth_required", True)
        permission = route_cfg.get("permission", f"force_delete:{entity_name}")

        def force_delete_item(**kwargs):
            """Permanently delete an item."""
            item_id = kwargs[id_field]
            service.force_delete(entity_id=item_id, id_field=id_field)
            return {"message": f"{entity_name.capitalize()} permanently deleted."}

        view = unit_of_work(force_delete_item)
        if permission:
            view = permission_required(permission)(view)
        if auth_required:
            view = jwt_required()(view)

        doc_params = {"summary": f"Permanently delete an {entity_name}"}
        if auth_required:
            doc_params["security"] = "bearerAuth"

        bp.delete(f"/<{id_field}>/force")(
            bp.output(MessageSchema, status_code=200)(bp.doc(**doc_params)(view))
        )

def register_custom_route(
    bp: APIBlueprint,
    rule: str,
    view_func: Callable,
    methods: List[str],
    *,
    input_schema: Optional[Type] = None,
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

    This helper function simplifies creating custom endpoints by encapsulating
    the common pattern of applying authentication, permissions, schema validation,
    and transaction management decorators.

    Args:
        bp: The APIBlueprint to register the route on.
        rule: The URL rule string.
        view_func: The view function to decorate and register.
        methods: A list of HTTP methods (e.g., ["GET", "POST"]).
        input_schema: The Marshmallow schema for request validation.
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

    # Apply custom decorators first
    if decorators:
        for decorator in reversed(decorators):
            view = decorator(view)

    # Apply built-in decorators in reverse order of execution.
    # The last decorator applied is the first one to run.
    if apply_unit_of_work:
        view = unit_of_work(view)

    if permission:
        view = permission_required(permission)(view)

    if auth_required:
        view = jwt_required()(view)

    doc_params = doc or {}
    if auth_required and "security" not in doc_params:
        doc_params["security"] = "bearerAuth"

    # The apiflask decorators are applied last, so they run first.
    final_view = bp.doc(**doc_params)(view)
    if output_schema:
        final_view = bp.output(output_schema, status_code=status_code)(final_view)
    if input_schema:
        # The location argument might be needed here if we support query args
        final_view = bp.input(input_schema)(final_view)

    bp.route(rule, methods=methods)(final_view)