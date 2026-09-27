from flask import request
from flask_jwt_extended import current_user, jwt_required
from flask_smorest import Blueprint
from marshmallow import ValidationError

from app.extensions import db
from app.models import Asset, Department, User
from app.schemas import AssetCreateSchema, AssetSchema, AssetUpdateSchema
from app.utils.helpers import json_error, paginate_query


asset_bp = Blueprint("assets", __name__, url_prefix="/assets")
asset_schema = AssetSchema()


@asset_bp.route("", methods=["GET"])
@jwt_required()
def list_assets():
    if current_user.role not in {"admin", "technician", "employee"}:
        return json_error(403, "forbidden", "Access denied")

    query = Asset.query
    if request.args.get("status"):
        query = query.filter_by(status=request.args.get("status"))
    if request.args.get("department_id"):
        query = query.filter_by(department_id=request.args.get("department_id", type=int))
    if request.args.get("assigned_to"):
        query = query.filter_by(assigned_to=request.args.get("assigned_to", type=int))

    paginated = paginate_query(query)
    return {
        "items": [asset_schema.dump(item) for item in paginated.items],
        "page": paginated.page,
        "pages": paginated.pages,
        "total": paginated.total,
    }


@asset_bp.route("", methods=["POST"])
@jwt_required()
def create_asset():
    if current_user.role not in {"admin", "technician"}:
        return json_error(403, "forbidden", "Admin or technician access required")

    data = request.get_json(silent=True) or {}
    try:
        payload = AssetCreateSchema().load(data)
    except ValidationError as exc:
        return json_error(400, "validation_error", "Validation failed", exc.messages)

    if Asset.query.filter_by(serial_number=payload["serial_number"].strip()).first():
        return json_error(409, "conflict", "Asset serial number already exists")
    if payload.get("assigned_to") and not db.session.get(User, payload["assigned_to"]):
        return json_error(404, "not_found", "Assigned user not found")
    if payload.get("department_id") and not db.session.get(Department, payload["department_id"]):
        return json_error(404, "not_found", "Department not found")

    asset = Asset(
        name=payload["name"].strip(),
        type=payload["type"],
        serial_number=payload["serial_number"].strip(),
        status=payload.get("status", "active"),
        assigned_to=payload.get("assigned_to"),
        department_id=payload.get("department_id"),
    )
    db.session.add(asset)
    db.session.commit()
    return {"asset": asset_schema.dump(asset)}, 201


@asset_bp.route("/<int:asset_id>", methods=["GET"])
@jwt_required()
def get_asset(asset_id):
    asset = db.session.get(Asset, asset_id)
    if not asset:
        return json_error(404, "not_found", "Asset not found")
    return {"asset": asset_schema.dump(asset)}


@asset_bp.route("/<int:asset_id>", methods=["PUT", "PATCH"])
@jwt_required()
def update_asset(asset_id):
    if current_user.role not in {"admin", "technician"}:
        return json_error(403, "forbidden", "Admin or technician access required")

    asset = db.session.get(Asset, asset_id)
    if not asset:
        return json_error(404, "not_found", "Asset not found")

    data = request.get_json(silent=True) or {}
    try:
        payload = AssetUpdateSchema().load(data)
    except ValidationError as exc:
        return json_error(400, "validation_error", "Validation failed", exc.messages)

    if "name" in payload:
        asset.name = payload["name"].strip()
    if "type" in payload:
        asset.type = payload["type"]
    if "status" in payload:
        asset.status = payload["status"]
    if "serial_number" in payload:
        serial_number = payload["serial_number"].strip()
        if Asset.query.filter(Asset.serial_number == serial_number, Asset.id != asset.id).first():
            return json_error(409, "conflict", "Asset serial number already exists")
        asset.serial_number = serial_number
    if "assigned_to" in payload:
        if payload["assigned_to"] and not db.session.get(User, payload["assigned_to"]):
            return json_error(404, "not_found", "Assigned user not found")
        asset.assigned_to = payload["assigned_to"]
    if "department_id" in payload:
        if payload["department_id"] and not db.session.get(Department, payload["department_id"]):
            return json_error(404, "not_found", "Department not found")
        asset.department_id = payload["department_id"]
    db.session.commit()
    return {"asset": asset_schema.dump(asset)}


@asset_bp.route("/<int:asset_id>", methods=["DELETE"])
@jwt_required()
def delete_asset(asset_id):
    if current_user.role not in {"admin", "technician"}:
        return json_error(403, "forbidden", "Admin or technician access required")

    asset = db.session.get(Asset, asset_id)
    if not asset:
        return json_error(404, "not_found", "Asset not found")
    db.session.delete(asset)
    db.session.commit()
    return {"message": "Asset deleted"}
