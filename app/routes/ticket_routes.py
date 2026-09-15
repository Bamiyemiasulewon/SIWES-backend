from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user

from app.extensions import db
from app.models import Ticket, Asset, Department, User
from app.schemas import TicketSchema
from app.utils.helpers import paginate_query


ticket_bp = Blueprint("tickets", __name__, url_prefix="/tickets")
ticket_schema = TicketSchema()


@ticket_bp.route("", methods=["GET"])
@jwt_required()
def list_tickets():
    query = Ticket.query

    if current_user.role == "employee" and request.args.get("created_by") is None:
        query = query.filter_by(created_by=current_user.id)
    elif current_user.role == "technician":
        query = query.filter((Ticket.created_by == current_user.id) | (Ticket.assigned_to == current_user.id))

    if request.args.get("status"):
        query = query.filter_by(status=request.args.get("status"))
    if request.args.get("priority"):
        query = query.filter_by(priority=request.args.get("priority"))
    if request.args.get("department_id"):
        query = query.filter_by(department_id=request.args.get("department_id", type=int))
    if request.args.get("assigned_to"):
        query = query.filter_by(assigned_to=request.args.get("assigned_to", type=int))

    paginated = paginate_query(query)
    return jsonify({
        "items": [ticket_schema.dump(item) for item in paginated.items],
        "page": paginated.page,
        "pages": paginated.pages,
        "total": paginated.total,
    })


@ticket_bp.route("", methods=["POST"])
@jwt_required()
def create_ticket():
    data = request.get_json(silent=True) or {}
    if not data.get("title") or not data.get("description"):
        return jsonify({"error": "validation_error", "messages": {"title": ["Required"], "description": ["Required"]}}), 400

    if data.get("asset_id") and not db.session.get(Asset, data["asset_id"]):
        return jsonify({"error": "not_found", "message": "Asset not found"}), 404
    if data.get("department_id") and not db.session.get(Department, data["department_id"]):
        return jsonify({"error": "not_found", "message": "Department not found"}), 404
    if data.get("assigned_to") and not db.session.get(User, data["assigned_to"]):
        return jsonify({"error": "not_found", "message": "Assigned technician not found"}), 404

    if current_user.role == "employee" and data.get("assigned_to"):
        return jsonify({"error": "forbidden", "message": "Employees cannot assign tickets"}), 403

    ticket = Ticket(
        title=data["title"].strip(),
        description=data["description"].strip(),
        status=data.get("status", "open"),
        priority=data.get("priority", "medium"),
        created_by=current_user.id,
        assigned_to=data.get("assigned_to"),
        asset_id=data.get("asset_id"),
        department_id=data.get("department_id") or current_user.department_id,
    )
    db.session.add(ticket)
    db.session.commit()
    return jsonify({"ticket": ticket_schema.dump(ticket)}), 201


@ticket_bp.route("/<int:ticket_id>", methods=["GET"])
@jwt_required()
def get_ticket(ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    if not ticket:
        return jsonify({"error": "not_found", "message": "Ticket not found"}), 404
    if current_user.role == "employee" and ticket.created_by != current_user.id:
        return jsonify({"error": "forbidden", "message": "Access denied"}), 403
    return jsonify({"ticket": ticket_schema.dump(ticket)})


@ticket_bp.route("/<int:ticket_id>", methods=["PUT", "PATCH"])
@jwt_required()
def update_ticket(ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    if not ticket:
        return jsonify({"error": "not_found", "message": "Ticket not found"}), 404
    if current_user.role == "employee" and ticket.created_by != current_user.id:
        return jsonify({"error": "forbidden", "message": "Access denied"}), 403

    data = request.get_json(silent=True) or {}
    for field in ["title", "description", "priority", "department_id"]:
        if field in data:
            setattr(ticket, field, data[field])
    if "status" in data:
        ticket.status = data["status"]
        if data["status"] == "resolved" and not ticket.resolved_at:
            ticket.resolved_at = datetime.utcnow()
        elif data["status"] != "resolved":
            ticket.resolved_at = None
    if "assigned_to" in data and current_user.role in {"admin", "technician"}:
        if data["assigned_to"] and not db.session.get(User, data["assigned_to"]):
            return jsonify({"error": "not_found", "message": "Assigned technician not found"}), 404
        ticket.assigned_to = data["assigned_to"]
    if "asset_id" in data and current_user.role in {"admin", "technician"}:
        if data["asset_id"] and not db.session.get(Asset, data["asset_id"]):
            return jsonify({"error": "not_found", "message": "Asset not found"}), 404
        ticket.asset_id = data["asset_id"]

    ticket.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"ticket": ticket_schema.dump(ticket)})


@ticket_bp.route("/<int:ticket_id>", methods=["DELETE"])
@jwt_required()
def delete_ticket(ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    if not ticket:
        return jsonify({"error": "not_found", "message": "Ticket not found"}), 404
    if current_user.role not in {"admin", "technician"} and ticket.created_by != current_user.id:
        return jsonify({"error": "forbidden", "message": "Access denied"}), 403
    db.session.delete(ticket)
    db.session.commit()
    return jsonify({"message": "Ticket deleted"})


@ticket_bp.route("/<int:ticket_id>/status", methods=["PATCH"])
@jwt_required()
def change_ticket_status(ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    if not ticket:
        return jsonify({"error": "not_found", "message": "Ticket not found"}), 404
    if current_user.role == "employee" and ticket.created_by != current_user.id:
        return jsonify({"error": "forbidden", "message": "Access denied"}), 403

    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if not status:
        return jsonify({"error": "validation_error", "messages": {"status": ["Required"]}}), 400

    ticket.status = status
    if status == "resolved" and not ticket.resolved_at:
        ticket.resolved_at = datetime.utcnow()
    elif status != "resolved":
        ticket.resolved_at = None
    ticket.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"ticket": ticket_schema.dump(ticket)})


@ticket_bp.route("/<int:ticket_id>/assign", methods=["PATCH"])
@jwt_required()
def assign_ticket(ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    if not ticket:
        return jsonify({"error": "not_found", "message": "Ticket not found"}), 404
    if current_user.role not in {"admin", "technician"}:
        return jsonify({"error": "forbidden", "message": "Only admin or technician can assign tickets"}), 403

    data = request.get_json(silent=True) or {}
    technician_id = data.get("assigned_to")
    if technician_id is None:
        return jsonify({"error": "validation_error", "messages": {"assigned_to": ["Required"]}}), 400
    tech = db.session.get(User, technician_id)
    if not tech or tech.role not in {"admin", "technician"}:
        return jsonify({"error": "validation_error", "messages": {"assigned_to": ["Must be a valid technician"]}}), 400

    ticket.assigned_to = technician_id
    ticket.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"ticket": ticket_schema.dump(ticket)})
