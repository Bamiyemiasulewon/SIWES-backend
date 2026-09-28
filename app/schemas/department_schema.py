from marshmallow import fields, validate

from app.extensions import ma
from app.models import Department


class DepartmentSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Department
        load_instance = True

    id = ma.auto_field()
    name = fields.String(required=True, validate=validate.Length(min=2, max=150))
    description = fields.String(required=False, allow_none=True, validate=validate.Length(max=500))
    created_at = ma.auto_field(dump_only=True)


class DepartmentCreateSchema(ma.Schema):
    name = fields.String(required=True, validate=validate.Length(min=2, max=150))
    description = fields.String(allow_none=True, validate=validate.Length(max=500))


class DepartmentUpdateSchema(ma.Schema):
    name = fields.String(validate=validate.Length(min=2, max=150))
    description = fields.String(allow_none=True, validate=validate.Length(max=500))
