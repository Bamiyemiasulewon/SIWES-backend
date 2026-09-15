from marshmallow import fields

from app.extensions import ma
from app.models import Ticket


class TicketSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Ticket
        load_instance = True

    id = ma.auto_field()
    title = ma.auto_field(required=True)
    description = ma.auto_field(required=True)
    status = ma.auto_field(required=True)
    priority = ma.auto_field(required=True)
    created_by = ma.auto_field(dump_only=True)
    assigned_to = fields.Integer(required=False, allow_none=True)
    asset_id = fields.Integer(required=False, allow_none=True)
    department_id = fields.Integer(required=False, allow_none=True)
    created_at = ma.auto_field(dump_only=True)
    updated_at = ma.auto_field(dump_only=True)
    resolved_at = ma.auto_field(dump_only=True, allow_none=True)
