from flask import request
from flask_jwt_extended import create_access_token, current_user, jwt_required
from flask_smorest import Blueprint
from marshmallow import ValidationError

from app.extensions import db
from app.models import User
from app.schemas import UserLoginSchema, UserRegisterSchema
from app.utils.helpers import json_error


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    try:
        payload = UserRegisterSchema().load(data)
    except ValidationError as exc:
        return json_error(400, "validation_error", "Validation failed", exc.messages)

    email = payload["email"].strip().lower()
    existing = User.query.filter_by(email=email).first()
    if existing:
        return json_error(409, "conflict", "User with this email already exists")

    user = User(
        name=payload["name"].strip(),
        email=email,
        role=payload.get("role", "employee"),
        department_id=payload.get("department_id"),
    )
    user.password = payload["password"]
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return {"token": token, "user": user.to_public_dict()}, 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    try:
        payload = UserLoginSchema().load(data)
    except ValidationError as exc:
        return json_error(400, "validation_error", "Validation failed", exc.messages)

    email = payload["email"].strip().lower()
    password = payload["password"]
    user = User.query.filter_by(email=email).first()
    if not user or not user.verify_password(password):
        return json_error(401, "unauthorized", "Invalid credentials")

    token = create_access_token(identity=str(user.id))
    return {"token": token, "user": user.to_public_dict()}


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    return {"user": current_user.to_public_dict()}
