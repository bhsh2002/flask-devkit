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
except Exception:
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
    """
    register_error_handlers(bp)

    main_schema = schemas["main"]
    input_schema = schemas["input"]
    update_schema = schemas["update"]
    query_schema = schemas["query"]
    pagination_out_schema = schemas["pagination_out"]
    tags = [entity_name.capitalize()]

    if id_field not in {"id", "uuid"}:
        raise ValueError("id_field must be either 'id' or 'uuid'")

    cfg: Dict[str, Dict[str, Any]] = routes_config or {}

    def get_route_decorators(
        route_name: str, default_require_auth: bool, default_permission: str | None
    ) -> List[Callable]:
        route_cfg = cfg.get(route_name, {})
        decorators: List[Callable] = []

        require_auth = route_cfg.get("auth_required", default_require_auth)
        if require_auth:
            decorators.append(jwt_required())

        permission = route_cfg.get("permission", default_permission)
        if permission:
            decorators.append(permission_required(permission))

        # Add unit_of_work for state-changing methods
        if route_name in {"create", "update", "delete"}:
            decorators.append(unit_of_work)

        return decorators

    def _apply_decorators(func, decorators: List[Callable]):
        for dec in reversed(decorators):
            func = dec(func)
        return func

    def list_items(query_data):
        """Retrieve a paginated list of items."""
        filters = query_data.copy()
        page = filters.pop("page", 1)
        per_page = filters.pop("per_page", 10)
        sort_by_str = filters.pop("sort_by", None)
        order_by = None
        if sort_by_str:
            order_by = [s.strip() for s in sort_by_str.split(",") if s.strip()]
        include_soft_deleted = filters.pop("include_soft_deleted", False)

        return service.paginate(
            page=page,
            per_page=per_page,
            filters=filters,
            order_by=order_by,
            include_soft_deleted=include_soft_deleted,
        ), 200

    def get_item(**kwargs):
        """Retrieve a single item by its ID or UUID."""
        item_id = kwargs[id_field]
        method_to_call = getattr(service, f"get_by_{id_field}")
        item = method_to_call(item_id)
        if item is None:
            raise NotFoundError(entity_name, item_id)
        return item

    def create_item(json_data):
        """Create a new item."""
        new = service.create(json_data)
        return new

    def update_item(json_data, **kwargs):
        """Update a single item."""
        item_id = kwargs[id_field]
        updated = service.update(item_id, json_data, id_field=id_field)
        return updated

    def delete_item(**kwargs):
        """Delete a single item."""
        item_id = kwargs[id_field]
        service.delete(entity_id=item_id, id_field=id_field)
        return {"message": f"{entity_name.capitalize()} deleted successfully."}

    if cfg.get("list", {}).get("enabled", True):
        list_doc_params = {"summary": f"List all {entity_name}s", "tags": tags}
        if cfg.get("list", {}).get("auth_required", True):
            list_doc_params["security"] = "bearerAuth"

        list_decorators: List[Callable] = [
            bp.get("/"),
            bp.input(query_schema, location="query"),
            bp.output(pagination_out_schema),
            bp.doc(**list_doc_params),
        ] + get_route_decorators(
            "list", default_require_auth=True, default_permission=None
        )
        list_items = _apply_decorators(list_items, list_decorators)

    if cfg.get("get", {}).get("enabled", True):
        get_doc_params = {"summary": f"Get a single {entity_name}", "tags": tags}
        if cfg.get("get", {}).get("auth_required", True):
            get_doc_params["security"] = "bearerAuth"

        get_decorators: List[Callable] = [
            bp.get(f"/<{id_field}>"),
            bp.output(main_schema),
            bp.doc(**get_doc_params),
        ] + get_route_decorators(
            "get", default_require_auth=True, default_permission=None
        )
        get_item = _apply_decorators(get_item, get_decorators)

    if cfg.get("create", {}).get("enabled", True):
        create_doc_params = {"summary": f"Create a new {entity_name}", "tags": tags}
        if cfg.get("create", {}).get("auth_required", True):
            create_doc_params["security"] = "bearerAuth"

        create_decorators: List[Callable] = [
            bp.post("/"),
            bp.input(input_schema),
            bp.output(main_schema, status_code=201),
            bp.doc(**create_doc_params),
        ] + get_route_decorators(
            "create",
            default_require_auth=True,
            default_permission=f"create:{entity_name}",
        )
        create_item = _apply_decorators(create_item, create_decorators)

    if cfg.get("update", {}).get("enabled", True):
        update_doc_params = {
            "summary": f"Update an existing {entity_name}",
            "tags": tags,
        }
        if cfg.get("update", {}).get("auth_required", True):
            update_doc_params["security"] = "bearerAuth"

        update_decorators: List[Callable] = [
            bp.patch(f"/<{id_field}>"),
            bp.input(update_schema),
            bp.output(main_schema),
            bp.doc(**update_doc_params),
        ] + get_route_decorators(
            "update",
            default_require_auth=True,
            default_permission=f"update:{entity_name}",
        )
        update_item = _apply_decorators(update_item, update_decorators)

    if cfg.get("delete", {}).get("enabled", True):
        delete_doc_params = {"summary": f"Delete an {entity_name}", "tags": tags}
        if cfg.get("delete", {}).get("auth_required", True):
            delete_doc_params["security"] = "bearerAuth"

        delete_decorators: List[Callable] = [
            bp.delete(f"/<{id_field}>"),
            bp.output(MessageSchema, status_code=200),
            bp.doc(**delete_doc_params),
        ] + get_route_decorators(
            "delete",
            default_require_auth=True,
            default_permission=f"delete:{entity_name}",
        )
        delete_item = _apply_decorators(delete_item, delete_decorators)
