from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user

from app.extensions import db
from app.models import Department
from app.schemas import DepartmentSchema
from app.utils.helpers import paginate_query


department_bp = Blueprint("departments", __name__, url_prefix="/departments")
department_schema = DepartmentSchema()


@department_bp.route("", methods=["GET"])
@jwt_required()
def list_departments():
    if current_user.role not in {"admin", "technician", "employee"}:
        return jsonify({"error": "forbidden", "message": "Access denied"}), 403
    paginated = paginate_query(Department.query)
    return jsonify({
        "items": [department_schema.dump(item) for item in paginated.items],
        "page": paginated.page,
        "pages": paginated.pages,
        "total": paginated.total,
    })


@department_bp.route("", methods=["POST"])
@jwt_required()
def create_department():
    if current_user.role != "admin":
        return jsonify({"error": "forbidden", "message": "Admin access required"}), 403

    data = request.get_json(silent=True) or {}
    if not data.get("name"):
        return jsonify({"error": "validation_error", "messages": {"name": ["Required"]}}), 400

    dept = Department(name=data["name"].strip(), description=data.get("description"))
    db.session.add(dept)
    db.session.commit()
    return jsonify({"department": department_schema.dump(dept)}), 201


@department_bp.route("/<int:department_id>", methods=["GET"])
@jwt_required()
def get_department(department_id):
    dept = db.session.get(Department, department_id)
    if not dept:
        return jsonify({"error": "not_found", "message": "Department not found"}), 404
    return jsonify({"department": department_schema.dump(dept)})


@department_bp.route("/<int:department_id>", methods=["PUT", "PATCH"])
@jwt_required()
def update_department(department_id):
    if current_user.role != "admin":
        return jsonify({"error": "forbidden", "message": "Admin access required"}), 403

    dept = db.session.get(Department, department_id)
    if not dept:
        return jsonify({"error": "not_found", "message": "Department not found"}), 404

    data = request.get_json(silent=True) or {}
    if "name" in data:
        dept.name = data["name"].strip()
    if "description" in data:
        dept.description = data["description"]
    db.session.commit()
    return jsonify({"department": department_schema.dump(dept)})


@department_bp.route("/<int:department_id>", methods=["DELETE"])
@jwt_required()
def delete_department(department_id):
    if current_user.role != "admin":
        return jsonify({"error": "forbidden", "message": "Admin access required"}), 403

    dept = db.session.get(Department, department_id)
    if not dept:
        return jsonify({"error": "not_found", "message": "Department not found"}), 404
    db.session.delete(dept)
    db.session.commit()
    return jsonify({"message": "Department deleted"})
