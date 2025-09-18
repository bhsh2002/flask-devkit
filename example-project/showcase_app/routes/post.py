from apiflask import APIBlueprint

from flask_devkit.database import db
from flask_devkit.helpers.routing import register_crud_routes
from showcase_app.models.post import Post
from showcase_app.schemas.post import post_schemas
from showcase_app.services.post import PostService

posts_bp = APIBlueprint("posts", __name__, url_prefix="/posts")

post_service = PostService(model=Post, db_session=db.session)

# Define custom permissions for posts
# These will be used by the permission_required decorator in register_crud_routes
post_routes_config = {
    "create": {"permission": "create:post"},
    "update": {"permission": "update:post"},
    "delete": {"permission": "delete:post"},
    "list": {"auth_required": False},  # Make posts list public
    "get": {"auth_required": False},  # Make single post public
}

register_crud_routes(
    bp=posts_bp,
    service=post_service,
    schemas=post_schemas,
    entity_name="post",
    id_field="uuid",
    routes_config=post_routes_config,
)
