from marshmallow import fields, validate

from app.extensions import ma
from app.models import User


VALID_ROLES = ["student", "staff", "maintenance_officer", "complaint_officer", "admin"]
VALID_OFFICER_SCOPES = ["department", "bursary", "general"]


class UserSchema(ma.SQLAlchemySchema):
    class Meta:
        model = User
        load_instance = True

    id = ma.auto_field()
    name = fields.String(required=True, validate=validate.Length(min=2, max=120))
    email = fields.Email(required=True, validate=validate.Length(max=120))
    role = fields.String(validate=validate.OneOf(VALID_ROLES))
    department_id = fields.Integer(allow_none=True)
    matric_number = fields.String(allow_none=True)
    level = fields.Integer(allow_none=True, validate=validate.Range(min=100, max=600))
    officer_scope = fields.String(allow_none=True, validate=validate.OneOf(VALID_OFFICER_SCOPES))
    created_at = ma.auto_field(dump_only=True)
    password = fields.String(load_only=True, required=False, validate=validate.Length(min=8, max=128))


class UserRegisterSchema(ma.Schema):
    name = fields.String(required=True, validate=validate.Length(min=2, max=120))
    email = fields.Email(required=True, validate=validate.Length(max=120))
    matric_number = fields.String(required=False, allow_none=True, validate=validate.Length(min=4, max=50))
    department_id = fields.Integer(required=True)
    level = fields.Integer(required=False, allow_none=True, validate=validate.Range(min=100, max=600))
    password = fields.String(required=True, load_only=True, validate=validate.Length(min=8, max=128))
    role = fields.String(load_default="student", validate=validate.OneOf(VALID_ROLES), required=False, allow_none=True)


class UserLoginSchema(ma.Schema):
    identifier = fields.String(required=True)
    password = fields.String(required=True, load_only=True)


class UserUpdateSchema(ma.Schema):
    name = fields.String(validate=validate.Length(min=2, max=120))
    email = fields.Email(validate=validate.Length(max=120))
    password = fields.String(load_only=True, validate=validate.Length(min=8, max=128))
    role = fields.String(validate=validate.OneOf(VALID_ROLES))
    department_id = fields.Integer(allow_none=True)
    matric_number = fields.String(allow_none=True)
    level = fields.Integer(allow_none=True, validate=validate.Range(min=100, max=600))
    officer_scope = fields.String(allow_none=True, validate=validate.OneOf(VALID_OFFICER_SCOPES))
