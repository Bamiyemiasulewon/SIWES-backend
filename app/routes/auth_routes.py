from collections import defaultdict, deque
from datetime import datetime

from flask import current_app, request
from flask_jwt_extended import create_access_token, current_user, jwt_required
from flask_smorest import Blueprint
from marshmallow import ValidationError

from app.extensions import db
from app.models import Department, User
from app.schemas import UserLoginSchema, UserRegisterSchema
from app.utils.helpers import json_error


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _login_attempts_store():
    if not hasattr(current_app, "_login_attempts"):
        current_app._login_attempts = defaultdict(deque)
    return current_app._login_attempts


def _is_login_limited(ip):
    attempts = _login_attempts_store().get(ip, deque())
    now = datetime.utcnow()
    while attempts and (now - attempts[0]).total_seconds() > 60:
        attempts.popleft()
    return len(attempts) >= 5


def _record_login_attempt(ip):
    attempts = _login_attempts_store().get(ip, deque())
    attempts.append(datetime.utcnow())
    _login_attempts_store()[ip] = attempts


def _clear_login_attempts(ip):
    _login_attempts_store().pop(ip, None)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    try:
        payload = UserRegisterSchema().load(data)
    except ValidationError as exc:
        return json_error(400, "validation_error", "Validation failed", exc.messages)

    email = payload["email"].strip().lower()
    if User.query.filter_by(email=email).first():
        return json_error(409, "conflict", "User with this email already exists")

    if "matric_number" not in payload or not payload["matric_number"]:
        return json_error(400, "validation_error", "Matric number is required for student registration", {"matric_number": ["Required"]})
    if "level" not in payload or payload["level"] is None:
        return json_error(400, "validation_error", "Level is required for student registration", {"level": ["Required"]})

    matric_number = payload["matric_number"].strip().upper()
    if User.query.filter_by(matric_number=matric_number).first():
        return json_error(409, "conflict", "This matriculation number is already registered")

    department = db.session.get(Department, payload["department_id"])
    if not department:
        return json_error(404, "not_found", "Department not found")

    user = User(
        name=payload["name"].strip(),
        email=email,
        matric_number=matric_number,
        department_id=department.id,
        level=payload["level"],
        role="student",
    )
    user.password = payload["password"]
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return {"token": token, "user": user.to_public_dict()}, 201


@auth_bp.route("/login", methods=["POST"])
def login():
    ip = request.remote_addr or "unknown"
    if _is_login_limited(ip):
        return json_error(429, "rate_limited", "Too many login attempts. Please try again later.")

    data = request.get_json(silent=True) or {}
    try:
        payload = UserLoginSchema().load(data)
    except ValidationError as exc:
        _record_login_attempt(ip)
        return json_error(400, "validation_error", "Validation failed", exc.messages)

    identifier = payload["identifier"].strip()
    password = payload["password"]
    user = User.query.filter(
        (User.email == identifier.lower()) | (User.matric_number == identifier.upper())
    ).first()

    if not user or not user.verify_password(password):
        _record_login_attempt(ip)
        return json_error(401, "unauthorized", "Invalid credentials")

    _clear_login_attempts(ip)
    token = create_access_token(identity=str(user.id))
    return {"token": token, "user": user.to_public_dict()}


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    return {"user": current_user.to_public_dict()}
