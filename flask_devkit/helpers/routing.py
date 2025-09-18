# flask_devkit/helpers/routing.py
"""
Provides a powerful factory function to auto-generate CRUD REST endpoints.
"""

from typing import Any, Callable, Dict, List, Type

from apiflask import APIBlueprint
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
        return error.to_dict(), 404

    @bp.errorhandler(AppBaseException)
    def handle_app_exception(error):
        return error.to_dict(), error.status_code

    if NoAuthorizationError is not None:

        @bp.errorhandler(NoAuthorizationError)
        def handle_no_auth_error(error):
            return {
                "message": "Missing authorization",
                "error_code": "AUTH_REQUIRED",
            }, 401

    if CSRFError is not None:

        @bp.errorhandler(CSRFError)
        def handle_csrf_error(error):
            return {
                "message": "CSRF validation failed",
                "error_code": "CSRF_FAILED",
            }, 401

    @bp.errorhandler(ValidationError)
    def handle_validation_error(error):
        return {"message": "Validation failed", "errors": error.messages}, 422


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

        def list_items(query_data):
            """Retrieve a paginated list of items."""
            filters = query_data.copy()
            page = filters.pop("page", 1)
            per_page = filters.pop("per_page", 10)
            sort_by_str = filters.pop("sort_by", None)
            order_by = (
                [s.strip() for s in sort_by_str.split(",") if s.strip()]
                if sort_by_str
                else None
            )
            include_soft_deleted = filters.pop("include_soft_deleted", False)
            return service.paginate(
                page=page,
                per_page=per_page,
                filters=filters,
                order_by=order_by,
                include_soft_deleted=include_soft_deleted,
            ), 200

        view = list_items
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

    # --- Route: Get ---
    if cfg.get("get", {}).get("enabled", True):
        route_cfg = cfg.get("get", {})
        auth_required = route_cfg.get("auth_required", True)
        permission = route_cfg.get("permission")

        def get_item(**kwargs):
            """Retrieve a single item by its ID or UUID."""
            item_id = kwargs[id_field]
            method_to_call = getattr(service, f"get_by_{id_field}")
            item = method_to_call(item_id)
            if item is None:
                raise NotFoundError(entity_name, item_id)
            return item

        view = get_item
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

        def create_item(json_data):
            """Create a new item."""
            return service.create(json_data)

        view = unit_of_work(create_item)
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

        def update_item(json_data, **kwargs):
            """Update a single item."""
            item_id = kwargs[id_field]
            return service.update(item_id, json_data, id_field=id_field)

        view = unit_of_work(update_item)
        if permission:
            view = permission_required(permission)(view)
        if auth_required:
            view = jwt_required()(view)

        doc_params = {"summary": f"Update an existing {entity_name}"}
        if auth_required:
            doc_params["security"] = "bearerAuth"

        bp.patch(f"/<{id_field}>")(
            bp.input(update_schema)(bp.output(main_schema)(bp.doc(**doc_params)(view)))
        )

    # --- Route: Delete ---
    if cfg.get("delete", {}).get("enabled", True):
        route_cfg = cfg.get("delete", {})
        auth_required = route_cfg.get("auth_required", True)
        permission = route_cfg.get("permission", f"delete:{entity_name}")

        def delete_item(**kwargs):
            """Delete a single item."""
            item_id = kwargs[id_field]
            service.delete(entity_id=item_id, id_field=id_field)
            return {"message": f"{entity_name.capitalize()} deleted successfully."}

        view = unit_of_work(delete_item)
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
