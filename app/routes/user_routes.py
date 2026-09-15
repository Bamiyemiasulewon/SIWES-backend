from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user

from app.extensions import db
from app.models import User, Department
from app.schemas import UserSchema
from app.utils.helpers import paginate_query


user_bp = Blueprint("users", __name__, url_prefix="/users")
user_schema = UserSchema()


def require_admin():
    if current_user.role != "admin":
        return False
    return True


@user_bp.route("", methods=["GET"])
@jwt_required()
def list_users():
    if current_user.role not in {"admin", "technician"}:
        return jsonify({"error": "forbidden", "message": "Access denied"}), 403

    query = User.query
    if request.args.get("department_id"):
        query = query.filter_by(department_id=request.args.get("department_id", type=int))
    if request.args.get("role"):
        query = query.filter_by(role=request.args.get("role"))

    paginated = paginate_query(query)
    return jsonify({
        "items": [u.to_public_dict() for u in paginated.items],
        "page": paginated.page,
        "pages": paginated.pages,
        "total": paginated.total,
    })


@user_bp.route("/<int:user_id>", methods=["GET"])
@jwt_required()
def get_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "not_found", "message": "User not found"}), 404
    if current_user.role != "admin" and current_user.id != user.id:
        return jsonify({"error": "forbidden", "message": "Access denied"}), 403
    return jsonify({"user": user.to_public_dict()})


@user_bp.route("", methods=["POST"])
@jwt_required()
def create_user():
    if not require_admin():
        return jsonify({"error": "forbidden", "message": "Admin access required"}), 403

    data = request.get_json(silent=True) or {}
    if not data.get("name") or not data.get("email"):
        return jsonify({"error": "validation_error", "messages": {"name": ["Required"], "email": ["Required"]}}), 400

    if User.query.filter_by(email=data["email"].strip().lower()).first():
        return jsonify({"error": "conflict", "message": "User already exists"}), 409

    if data.get("department_id") and not db.session.get(Department, data["department_id"]):
        return jsonify({"error": "not_found", "message": "Department not found"}), 404

    user = User(
        name=data["name"].strip(),
        email=data["email"].strip().lower(),
        role=data.get("role", "employee"),
        department_id=data.get("department_id"),
    )
    user.password = data.get("password", "changeme")
    db.session.add(user)
    db.session.commit()
    return jsonify({"user": user.to_public_dict()}), 201


@user_bp.route("/<int:user_id>", methods=["PUT", "PATCH"])
@jwt_required()
def update_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "not_found", "message": "User not found"}), 404
    if current_user.role != "admin" and current_user.id != user.id:
        return jsonify({"error": "forbidden", "message": "Access denied"}), 403

    data = request.get_json(silent=True) or {}
    if "name" in data:
        user.name = data["name"].strip()
    if "email" in data:
        email = data["email"].strip().lower()
        if User.query.filter(User.email == email, User.id != user.id).first():
            return jsonify({"error": "conflict", "message": "Email already in use"}), 409
        user.email = email
    if "role" in data and current_user.role == "admin":
        user.role = data["role"]
    if "department_id" in data and current_user.role == "admin":
        if data["department_id"] and not db.session.get(Department, data["department_id"]):
            return jsonify({"error": "not_found", "message": "Department not found"}), 404
        user.department_id = data["department_id"]
    if "password" in data and data["password"]:
        user.password = data["password"]

    db.session.commit()
    return jsonify({"user": user.to_public_dict()})


@user_bp.route("/<int:user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id):
    if not require_admin():
        return jsonify({"error": "forbidden", "message": "Admin access required"}), 403

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "not_found", "message": "User not found"}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted successfully"})
