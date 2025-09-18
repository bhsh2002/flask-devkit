from marshmallow import fields

from flask_devkit.helpers.schemas import BaseSchema, create_crud_schemas
from flask_devkit.users.schemas import user_schemas
from showcase_app.models.post import Post


class PostAuthorSchema(user_schemas["main"]):
    class Meta(user_schemas["main"].Meta):
        fields = ("uuid", "username")


class PostSchema(BaseSchema):
    author = fields.Nested(PostAuthorSchema, dump_only=True)

    class Meta(BaseSchema.Meta):
        model = Post
        fields = ("uuid", "title", "content", "author", "created_at", "updated_at")


post_schemas = create_crud_schemas(
    model_class=Post,
    main_schema=PostSchema,
    # author_id will be set automatically
    # from the logged-in user, so we exclude it from input
    excluded_input_fields=["author_id", "author"],
    # Only title and content can be updated
    allowed_update_fields=["title", "content"],
)
