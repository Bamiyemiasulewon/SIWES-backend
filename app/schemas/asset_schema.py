from marshmallow import fields, validate

from app.extensions import ma
from app.models import Asset


VALID_ASSET_TYPES = ["projector", "lab_equipment", "hvac", "generator", "furniture", "other"]


class AssetSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Asset
        load_instance = True

    id = ma.auto_field()
    name = fields.String(required=True, validate=validate.Length(min=2, max=120))
    type = fields.String(required=True, validate=validate.OneOf(VALID_ASSET_TYPES))
    serial_number = fields.String(required=True, validate=validate.Length(min=2, max=120))
    status = fields.String(required=True, validate=validate.OneOf(["active", "in_repair", "retired"]))
    building = fields.String(allow_none=True, validate=validate.Length(max=120))
    room = fields.String(allow_none=True, validate=validate.Length(max=60))
    assigned_to = fields.Integer(required=False, allow_none=True)
    department_id = fields.Integer(required=False, allow_none=True)
    created_at = ma.auto_field(dump_only=True)


class AssetCreateSchema(ma.Schema):
    name = fields.String(required=True, validate=validate.Length(min=2, max=120))
    type = fields.String(required=True, validate=validate.OneOf(VALID_ASSET_TYPES))
    serial_number = fields.String(required=True, validate=validate.Length(min=2, max=120))
    status = fields.String(load_default="active", validate=validate.OneOf(["active", "in_repair", "retired"]))
    building = fields.String(allow_none=True, validate=validate.Length(max=120))
    room = fields.String(allow_none=True, validate=validate.Length(max=60))
    assigned_to = fields.Integer(allow_none=True)
    department_id = fields.Integer(allow_none=True)


class AssetUpdateSchema(ma.Schema):
    name = fields.String(validate=validate.Length(min=2, max=120))
    type = fields.String(validate=validate.OneOf(VALID_ASSET_TYPES))
    serial_number = fields.String(validate=validate.Length(min=2, max=120))
    status = fields.String(validate=validate.OneOf(["active", "in_repair", "retired"]))
    building = fields.String(allow_none=True, validate=validate.Length(max=120))
    room = fields.String(allow_none=True, validate=validate.Length(max=60))
    assigned_to = fields.Integer(allow_none=True)
    department_id = fields.Integer(allow_none=True)
