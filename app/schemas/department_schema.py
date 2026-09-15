from marshmallow import fields

from app.extensions import ma
from app.models import Department


class DepartmentSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Department
        load_instance = True

    id = ma.auto_field()
    name = ma.auto_field(required=True)
    description = fields.String(required=False, allow_none=True)
    created_at = ma.auto_field(dump_only=True)
