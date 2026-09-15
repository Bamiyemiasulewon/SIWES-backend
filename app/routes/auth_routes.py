from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, current_user

from app.extensions import db
from app.models import User
from app.schemas import UserSchema


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
user_schema = UserSchema()


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    if not data.get("name") or not data.get("email") or not data.get("password"):
        return jsonify({"error": "validation_error", "messages": {"name": ["Required"], "email": ["Required"], "password": ["Required"]}}), 400

    existing = User.query.filter_by(email=data["email"].strip().lower()).first()
    if existing:
        return jsonify({"error": "conflict", "message": "User with this email already exists"}), 409

    user = User(
        name=data["name"].strip(),
        email=data["email"].strip().lower(),
        role=data.get("role", "employee"),
        department_id=data.get("department_id"),
    )
    user.password = data["password"]
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_public_dict()}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "validation_error", "messages": {"email": ["Required"], "password": ["Required"]}}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.verify_password(password):
        return jsonify({"error": "unauthorized", "message": "Invalid credentials"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_public_dict()})


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    return jsonify({"user": current_user.to_public_dict()})
