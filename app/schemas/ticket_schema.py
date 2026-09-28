from marshmallow import fields, validate

from app.extensions import ma
from app.models import Request


MAINTENANCE_CATEGORIES = ["electrical", "plumbing", "lab_equipment", "hostel", "furniture", "other"]
COMPLAINT_CATEGORIES = ["results", "registration", "fees", "hostel", "lecturer_conduct", "other"]
VALID_TYPES = ["maintenance", "complaint"]
VALID_PRIORITIES = ["low", "medium", "high", "critical"]
VALID_STATUSES = ["submitted", "assigned", "in_progress", "resolved", "reopened", "closed"]


class TicketSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Request
        load_instance = True

    id = ma.auto_field()
    type = fields.String(required=True, validate=validate.OneOf(VALID_TYPES))
    category = fields.String(required=True)
    title = fields.String(required=True, validate=validate.Length(min=3, max=200))
    description = fields.String(required=True, validate=validate.Length(min=5, max=2000))
    priority = fields.String(required=True, validate=validate.OneOf(VALID_PRIORITIES))
    status = fields.String(required=True, validate=validate.OneOf(VALID_STATUSES))
    is_anonymous = fields.Boolean(required=False, dump_default=False)
    created_by = ma.auto_field(dump_only=True)
    department_id = fields.Integer(required=False, allow_none=True)
    building = fields.String(allow_none=True)
    room = fields.String(allow_none=True)
    course_code = fields.String(allow_none=True)
    asset_id = fields.Integer(required=False, allow_none=True)
    assigned_to = fields.Integer(required=False, allow_none=True)
    resolution_notes = fields.String(allow_none=True)
    reopen_count = fields.Integer(dump_default=0)
    is_flagged = fields.Boolean(dump_default=False)
    flag_type = fields.String(allow_none=True)
    flag_reason = fields.String(allow_none=True)
    flagged_by = fields.Integer(allow_none=True)
    flagged_at = fields.DateTime(allow_none=True)
    created_at = ma.auto_field(dump_only=True)
    updated_at = ma.auto_field(dump_only=True)
    resolved_at = ma.auto_field(dump_only=True, allow_none=True)
    closed_at = ma.auto_field(dump_only=True, allow_none=True)


class TicketCreateSchema(ma.Schema):
    type = fields.String(required=True, validate=validate.OneOf(VALID_TYPES))
    category = fields.String(required=True)
    title = fields.String(required=True, validate=validate.Length(min=3, max=200))
    description = fields.String(required=True, validate=validate.Length(min=5, max=2000))
    priority = fields.String(load_default="medium", validate=validate.OneOf(VALID_PRIORITIES))
    is_anonymous = fields.Boolean(load_default=False)
    building = fields.String(allow_none=True)
    room = fields.String(allow_none=True)
    course_code = fields.String(allow_none=True)
    asset_id = fields.Integer(allow_none=True)
    assigned_to = fields.Integer(allow_none=True)
    department_id = fields.Integer(allow_none=True)


class TicketUpdateSchema(ma.Schema):
    title = fields.String(validate=validate.Length(min=3, max=200))
    description = fields.String(validate=validate.Length(min=5, max=2000))
    priority = fields.String(validate=validate.OneOf(VALID_PRIORITIES))
    is_anonymous = fields.Boolean(allow_none=True)
    building = fields.String(allow_none=True)
    room = fields.String(allow_none=True)
    course_code = fields.String(allow_none=True)
    asset_id = fields.Integer(allow_none=True)
    department_id = fields.Integer(allow_none=True)


class TicketStatusSchema(ma.Schema):
    status = fields.String(required=True, validate=validate.OneOf(VALID_STATUSES))
    reason = fields.String(allow_none=True, validate=validate.Length(min=10, max=1000))
    resolution_notes = fields.String(allow_none=True, validate=validate.Length(min=5, max=1000))


class TicketAssignSchema(ma.Schema):
    assigned_to = fields.Integer(required=True)


class TicketHistorySchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    request_id = fields.Integer(dump_only=True)
    changed_by = fields.Integer(dump_only=True, allow_none=True)
    field_changed = fields.String(dump_only=True)
    old_value = fields.String(allow_none=True, dump_only=True)
    new_value = fields.String(allow_none=True, dump_only=True)
    note = fields.String(allow_none=True, dump_only=True)
    changed_at = fields.DateTime(dump_only=True)
