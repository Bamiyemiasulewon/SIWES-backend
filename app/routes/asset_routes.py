from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user

from app.extensions import db
from app.models import Asset, Department, User
from app.schemas import AssetSchema
from app.utils.helpers import paginate_query


asset_bp = Blueprint("assets", __name__, url_prefix="/assets")
asset_schema = AssetSchema()


@asset_bp.route("", methods=["GET"])
@jwt_required()
def list_assets():
    if current_user.role not in {"admin", "technician", "employee"}:
        return jsonify({"error": "forbidden", "message": "Access denied"}), 403

    query = Asset.query
    if request.args.get("status"):
        query = query.filter_by(status=request.args.get("status"))
    if request.args.get("department_id"):
        query = query.filter_by(department_id=request.args.get("department_id", type=int))
    if request.args.get("assigned_to"):
        query = query.filter_by(assigned_to=request.args.get("assigned_to", type=int))

    paginated = paginate_query(query)
    return jsonify({
        "items": [asset_schema.dump(item) for item in paginated.items],
        "page": paginated.page,
        "pages": paginated.pages,
        "total": paginated.total,
    })


@asset_bp.route("", methods=["POST"])
@jwt_required()
def create_asset():
    if current_user.role not in {"admin", "technician"}:
        return jsonify({"error": "forbidden", "message": "Admin or technician access required"}), 403

    data = request.get_json(silent=True) or {}
    if not data.get("name") or not data.get("type") or not data.get("serial_number"):
        return jsonify({"error": "validation_error", "messages": {"name": ["Required"], "type": ["Required"], "serial_number": ["Required"]}}), 400

    if Asset.query.filter_by(serial_number=data["serial_number"].strip()).first():
        return jsonify({"error": "conflict", "message": "Asset serial number already exists"}), 409

    if data.get("assigned_to") and not db.session.get(User, data["assigned_to"]):
        return jsonify({"error": "not_found", "message": "Assigned user not found"}), 404
    if data.get("department_id") and not db.session.get(Department, data["department_id"]):
        return jsonify({"error": "not_found", "message": "Department not found"}), 404

    asset = Asset(
        name=data["name"].strip(),
        type=data["type"],
        serial_number=data["serial_number"].strip(),
        status=data.get("status", "active"),
        assigned_to=data.get("assigned_to"),
        department_id=data.get("department_id"),
    )
    db.session.add(asset)
    db.session.commit()
    return jsonify({"asset": asset_schema.dump(asset)}), 201


@asset_bp.route("/<int:asset_id>", methods=["GET"])
@jwt_required()
def get_asset(asset_id):
    asset = db.session.get(Asset, asset_id)
    if not asset:
        return jsonify({"error": "not_found", "message": "Asset not found"}), 404
    return jsonify({"asset": asset_schema.dump(asset)})


@asset_bp.route("/<int:asset_id>", methods=["PUT", "PATCH"])
@jwt_required()
def update_asset(asset_id):
    if current_user.role not in {"admin", "technician"}:
        return jsonify({"error": "forbidden", "message": "Admin or technician access required"}), 403

    asset = db.session.get(Asset, asset_id)
    if not asset:
        return jsonify({"error": "not_found", "message": "Asset not found"}), 404

    data = request.get_json(silent=True) or {}
    for field in ["name", "type", "status"]:
        if field in data:
            setattr(asset, field, data[field])
    if "serial_number" in data:
        if Asset.query.filter(Asset.serial_number == data["serial_number"].strip(), Asset.id != asset.id).first():
            return jsonify({"error": "conflict", "message": "Asset serial number already exists"}), 409
        asset.serial_number = data["serial_number"].strip()
    if "assigned_to" in data:
        if data["assigned_to"] and not db.session.get(User, data["assigned_to"]):
            return jsonify({"error": "not_found", "message": "Assigned user not found"}), 404
        asset.assigned_to = data["assigned_to"]
    if "department_id" in data:
        if data["department_id"] and not db.session.get(Department, data["department_id"]):
            return jsonify({"error": "not_found", "message": "Department not found"}), 404
        asset.department_id = data["department_id"]
    db.session.commit()
    return jsonify({"asset": asset_schema.dump(asset)})


@asset_bp.route("/<int:asset_id>", methods=["DELETE"])
@jwt_required()
def delete_asset(asset_id):
    if current_user.role not in {"admin", "technician"}:
        return jsonify({"error": "forbidden", "message": "Admin or technician access required"}), 403

    asset = db.session.get(Asset, asset_id)
    if not asset:
        return jsonify({"error": "not_found", "message": "Asset not found"}), 404
    db.session.delete(asset)
    db.session.commit()
    return jsonify({"message": "Asset deleted"})
