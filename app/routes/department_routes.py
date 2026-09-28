from flask import request
from flask_jwt_extended import current_user, jwt_required
from flask_smorest import Blueprint
from marshmallow import ValidationError

from app.extensions import db
from app.models import Department, Request, User
from app.schemas import DepartmentCreateSchema, DepartmentSchema, DepartmentUpdateSchema
from app.utils.helpers import json_error, paginate_query


department_bp = Blueprint("departments", __name__, url_prefix="/departments")
department_schema = DepartmentSchema()


@department_bp.route("", methods=["GET"])
def list_departments_public():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    paginated = Department.query.paginate(page=page, per_page=per_page, error_out=False)
    return {
        "items": [{"id": dept.id, "name": dept.name} for dept in paginated.items],
        "page": paginated.page,
        "pages": paginated.pages,
        "total": paginated.total,
    }


@department_bp.route("", methods=["POST"])
@jwt_required()
def create_department():
    if current_user.role != "admin":
        return json_error(403, "forbidden", "Admin access required")

    data = request.get_json(silent=True) or {}
    try:
        payload = DepartmentCreateSchema().load(data)
    except ValidationError as exc:
        return json_error(400, "validation_error", "Validation failed", exc.messages)

    name = payload["name"].strip()
    if Department.query.filter_by(name=name).first():
        return json_error(409, "conflict", "Department already exists")

    dept = Department(name=name, description=payload.get("description"))
    db.session.add(dept)
    db.session.commit()
    return {"department": department_schema.dump(dept)}, 201


@department_bp.route("/<int:department_id>", methods=["GET"])
@jwt_required()
def get_department(department_id):
    dept = db.session.get(Department, department_id)
    if not dept:
        return json_error(404, "not_found", "Department not found")
    return {"department": department_schema.dump(dept)}


@department_bp.route("/<int:department_id>", methods=["PUT", "PATCH"])
@jwt_required()
def update_department(department_id):
    if current_user.role != "admin":
        return json_error(403, "forbidden", "Admin access required")

    dept = db.session.get(Department, department_id)
    if not dept:
        return json_error(404, "not_found", "Department not found")

    data = request.get_json(silent=True) or {}
    try:
        payload = DepartmentUpdateSchema().load(data)
    except ValidationError as exc:
        return json_error(400, "validation_error", "Validation failed", exc.messages)

    if "name" in payload:
        dept.name = payload["name"].strip()
    if "description" in payload:
        dept.description = payload["description"]
    db.session.commit()
    return {"department": department_schema.dump(dept)}


@department_bp.route("/<int:department_id>", methods=["DELETE"])
@jwt_required()
def delete_department(department_id):
    if current_user.role != "admin":
        return json_error(403, "forbidden", "Admin access required")

    dept = db.session.get(Department, department_id)
    if not dept:
        return json_error(404, "not_found", "Department not found")
    if User.query.filter_by(department_id=dept.id).first() or Request.query.filter_by(department_id=dept.id).first():
        return json_error(409, "conflict", "Department cannot be deleted because it has users or requests")
    db.session.delete(dept)
    db.session.commit()
    return {"message": "Department deleted"}
