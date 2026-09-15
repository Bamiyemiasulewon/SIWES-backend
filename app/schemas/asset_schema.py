from marshmallow import fields

from app.extensions import ma
from app.models import Asset


class AssetSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Asset
        load_instance = True

    id = ma.auto_field()
    name = ma.auto_field(required=True)
    type = ma.auto_field(required=True)
    serial_number = ma.auto_field(required=True)
    status = ma.auto_field(required=True)
    assigned_to = fields.Integer(required=False, allow_none=True)
    department_id = fields.Integer(required=False, allow_none=True)
    created_at = ma.auto_field(dump_only=True)
