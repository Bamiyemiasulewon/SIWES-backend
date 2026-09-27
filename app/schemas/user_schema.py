from marshmallow import fields, validate

from app.extensions import ma
from app.models import User


class UserSchema(ma.SQLAlchemySchema):
    class Meta:
        model = User
        load_instance = True

    id = ma.auto_field()
    name = fields.String(required=True, validate=validate.Length(min=2, max=120))
    email = fields.Email(required=True, validate=validate.Length(max=120))
    role = fields.String(validate=validate.OneOf(["admin", "technician", "employee"]))
    department_id = fields.Integer(allow_none=True)
    created_at = ma.auto_field(dump_only=True)
    password = fields.String(load_only=True, required=False, validate=validate.Length(min=8, max=128))


class UserRegisterSchema(ma.Schema):
    name = fields.String(required=True, validate=validate.Length(min=2, max=120))
    email = fields.Email(required=True, validate=validate.Length(max=120))
    password = fields.String(required=True, load_only=True, validate=validate.Length(min=8, max=128))
    role = fields.String(load_default="employee", validate=validate.OneOf(["admin", "technician", "employee"]))
    department_id = fields.Integer(load_default=None, allow_none=True)


class UserLoginSchema(ma.Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True)


class UserUpdateSchema(ma.Schema):
    name = fields.String(validate=validate.Length(min=2, max=120))
    email = fields.Email(validate=validate.Length(max=120))
    password = fields.String(load_only=True, validate=validate.Length(min=8, max=128))
    role = fields.String(validate=validate.OneOf(["admin", "technician", "employee"]))
    department_id = fields.Integer(allow_none=True)
