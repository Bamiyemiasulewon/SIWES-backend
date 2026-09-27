from marshmallow import fields, validate

from app.extensions import ma
from app.models import Ticket


class TicketSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Ticket
        load_instance = True

    id = ma.auto_field()
    title = fields.String(required=True, validate=validate.Length(min=3, max=200))
    description = fields.String(required=True, validate=validate.Length(min=5, max=2000))
    status = fields.String(required=True, validate=validate.OneOf(["open", "in_progress", "resolved", "closed"]))
    priority = fields.String(required=True, validate=validate.OneOf(["low", "medium", "high", "critical"]))
    created_by = ma.auto_field(dump_only=True)
    assigned_to = fields.Integer(required=False, allow_none=True)
    asset_id = fields.Integer(required=False, allow_none=True)
    department_id = fields.Integer(required=False, allow_none=True)
    created_at = ma.auto_field(dump_only=True)
    updated_at = ma.auto_field(dump_only=True)
    resolved_at = ma.auto_field(dump_only=True, allow_none=True)


class TicketCreateSchema(ma.Schema):
    title = fields.String(required=True, validate=validate.Length(min=3, max=200))
    description = fields.String(required=True, validate=validate.Length(min=5, max=2000))
    priority = fields.String(load_default="medium", validate=validate.OneOf(["low", "medium", "high", "critical"]))
    status = fields.String(load_default="open", validate=validate.OneOf(["open", "in_progress", "resolved", "closed"]))
    assigned_to = fields.Integer(allow_none=True)
    asset_id = fields.Integer(allow_none=True)
    department_id = fields.Integer(allow_none=True)


class TicketUpdateSchema(ma.Schema):
    title = fields.String(validate=validate.Length(min=3, max=200))
    description = fields.String(validate=validate.Length(min=5, max=2000))
    priority = fields.String(validate=validate.OneOf(["low", "medium", "high", "critical"]))
    status = fields.String(validate=validate.OneOf(["open", "in_progress", "resolved", "closed"]))
    assigned_to = fields.Integer(allow_none=True)
    asset_id = fields.Integer(allow_none=True)
    department_id = fields.Integer(allow_none=True)


class TicketStatusSchema(ma.Schema):
    status = fields.String(required=True, validate=validate.OneOf(["open", "in_progress", "resolved", "closed"]))


class TicketAssignSchema(ma.Schema):
    assigned_to = fields.Integer(required=True)


class TicketHistorySchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    ticket_id = fields.Integer(dump_only=True)
    changed_by = fields.Integer(dump_only=True)
    field_changed = fields.String(dump_only=True)
    old_value = fields.String(allow_none=True, dump_only=True)
    new_value = fields.String(allow_none=True, dump_only=True)
    changed_at = fields.DateTime(dump_only=True)
