from flask import request
from flask_jwt_extended import current_user, jwt_required
from flask_smorest import Blueprint
from marshmallow import ValidationError

from app.extensions import db
from app.models import Department, User
from app.schemas import UserRegisterSchema, UserSchema, UserUpdateSchema
from app.utils.helpers import json_error, paginate_query


user_bp = Blueprint("users", __name__, url_prefix="/users")


def require_admin():
    if current_user.role != "admin":
        return False
    return True


@user_bp.route("", methods=["GET"])
@jwt_required()
def list_users():
    if current_user.role not in {"admin", "technician"}:
        return json_error(403, "forbidden", "Access denied")

    query = User.query
    if request.args.get("department_id"):
        query = query.filter_by(department_id=request.args.get("department_id", type=int))
    if request.args.get("role"):
        query = query.filter_by(role=request.args.get("role"))

    paginated = paginate_query(query)
    return {
        "items": [u.to_public_dict() for u in paginated.items],
        "page": paginated.page,
        "pages": paginated.pages,
        "total": paginated.total,
    }


@user_bp.route("/<int:user_id>", methods=["GET"])
@jwt_required()
def get_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return json_error(404, "not_found", "User not found")
    if current_user.role != "admin" and current_user.id != user.id:
        return json_error(403, "forbidden", "Access denied")
    return {"user": user.to_public_dict()}


@user_bp.route("", methods=["POST"])
@jwt_required()
def create_user():
    if not require_admin():
        return json_error(403, "forbidden", "Admin access required")

    data = request.get_json(silent=True) or {}
    try:
        payload = UserRegisterSchema().load(data)
    except ValidationError as exc:
        return json_error(400, "validation_error", "Validation failed", exc.messages)

    email = payload["email"].strip().lower()
    if User.query.filter_by(email=email).first():
        return json_error(409, "conflict", "User already exists")
    if payload.get("department_id") and not db.session.get(Department, payload["department_id"]):
        return json_error(404, "not_found", "Department not found")

    user = User(
        name=payload["name"].strip(),
        email=email,
        role=payload.get("role", "employee"),
        department_id=payload.get("department_id"),
    )
    user.password = payload.get("password")
    db.session.add(user)
    db.session.commit()
    return {"user": user.to_public_dict()}, 201


@user_bp.route("/<int:user_id>", methods=["PUT", "PATCH"])
@jwt_required()
def update_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return json_error(404, "not_found", "User not found")
    if current_user.role != "admin" and current_user.id != user.id:
        return json_error(403, "forbidden", "Access denied")

    data = request.get_json(silent=True) or {}
    try:
        payload = UserUpdateSchema().load(data)
    except ValidationError as exc:
        return json_error(400, "validation_error", "Validation failed", exc.messages)

    if "name" in payload:
        user.name = payload["name"].strip()
    if "email" in payload:
        email = payload["email"].strip().lower()
        if User.query.filter(User.email == email, User.id != user.id).first():
            return json_error(409, "conflict", "Email already in use")
        user.email = email
    if "role" in payload:
        if current_user.role != "admin":
            return json_error(403, "forbidden", "Only admins can change roles")
        user.role = payload["role"]
    if "department_id" in payload:
        if current_user.role != "admin":
            return json_error(403, "forbidden", "Only admins can change department assignments")
        if payload["department_id"] and not db.session.get(Department, payload["department_id"]):
            return json_error(404, "not_found", "Department not found")
        user.department_id = payload["department_id"]
    if "password" in payload:
        user.password = payload["password"]

    db.session.commit()
    return {"user": user.to_public_dict()}


@user_bp.route("/<int:user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id):
    if not require_admin():
        return json_error(403, "forbidden", "Admin access required")

    user = db.session.get(User, user_id)
    if not user:
        return json_error(404, "not_found", "User not found")
    db.session.delete(user)
    db.session.commit()
    return {"message": "User deleted successfully"}
