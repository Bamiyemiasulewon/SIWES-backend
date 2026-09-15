from marshmallow import fields

from app.extensions import ma
from app.models import User


class UserSchema(ma.SQLAlchemySchema):
    class Meta:
        model = User
        load_instance = True

    id = ma.auto_field()
    name = ma.auto_field(required=True)
    email = ma.auto_field(required=True)
    role = ma.auto_field()
    department_id = ma.auto_field()
    created_at = ma.auto_field(dump_only=True)

    password = fields.String(load_only=True, required=False)
