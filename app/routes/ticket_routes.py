from datetime import datetime

from flask import request
from flask_jwt_extended import current_user, jwt_required
from flask_smorest import Blueprint
from marshmallow import ValidationError

from app.extensions import db
from app.models import Asset, Department, Ticket, TicketHistory, User
from app.schemas import (
    TicketAssignSchema,
    TicketCreateSchema,
    TicketHistorySchema,
    TicketSchema,
    TicketStatusSchema,
    TicketUpdateSchema,
)
from app.utils.helpers import json_error, paginate_query, require_roles


ticket_bp = Blueprint("tickets", __name__, url_prefix="/tickets")
ticket_schema = TicketSchema()


def record_ticket_history(ticket, field, old_value, new_value, changed_by):
    if old_value == new_value:
        return
    history = TicketHistory(
        ticket_id=ticket.id,
        changed_by=changed_by,
        field_changed=field,
        old_value=str(old_value) if old_value is not None else None,
        new_value=str(new_value) if new_value is not None else None,
    )
    db.session.add(history)


@ticket_bp.route("", methods=["GET"])
@jwt_required()
def list_tickets():
    query = Ticket.query

    if current_user.role == "employee":
        query = query.filter_by(created_by=current_user.id)
    elif current_user.role == "technician":
        query = query.filter((Ticket.assigned_to == current_user.id) | (Ticket.created_by == current_user.id))

    if request.args.get("status"):
        query = query.filter_by(status=request.args.get("status"))
    if request.args.get("priority"):
        query = query.filter_by(priority=request.args.get("priority"))
    if request.args.get("department_id"):
        query = query.filter_by(department_id=request.args.get("department_id", type=int))
    if request.args.get("assigned_to"):
        query = query.filter_by(assigned_to=request.args.get("assigned_to", type=int))
    if request.args.get("created_by"):
        query = query.filter_by(created_by=request.args.get("created_by", type=int))

    paginated = paginate_query(query)
    return {
        "items": [ticket_schema.dump(item) for item in paginated.items],
        "page": paginated.page,
        "pages": paginated.pages,
        "total": paginated.total,
    }


@ticket_bp.route("", methods=["POST"])
@jwt_required()
def create_ticket():
    data = request.get_json(silent=True) or {}
    try:
        payload = TicketCreateSchema().load(data)
    except ValidationError as exc:
        return json_error(400, "validation_error", "Validation failed", exc.messages)

    if payload.get("asset_id") and not db.session.get(Asset, payload["asset_id"]):
        return json_error(404, "not_found", "Asset not found")
    if payload.get("department_id") and not db.session.get(Department, payload["department_id"]):
        return json_error(404, "not_found", "Department not found")
    if payload.get("assigned_to") and not db.session.get(User, payload["assigned_to"]):
        return json_error(404, "not_found", "Assigned technician not found")
    if current_user.role == "employee" and payload.get("assigned_to"):
        return json_error(403, "forbidden", "Employees cannot assign tickets")

    ticket = Ticket(
        title=payload["title"].strip(),
        description=payload["description"].strip(),
        status=payload.get("status", "open"),
        priority=payload.get("priority", "medium"),
        created_by=current_user.id,
        assigned_to=payload.get("assigned_to"),
        asset_id=payload.get("asset_id"),
        department_id=payload.get("department_id") or current_user.department_id,
    )
    db.session.add(ticket)
    db.session.commit()
    return {"ticket": ticket_schema.dump(ticket)}, 201


@ticket_bp.route("/<int:ticket_id>", methods=["GET"])
@jwt_required()
def get_ticket(ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    if not ticket:
        return json_error(404, "not_found", "Ticket not found")
    if current_user.role == "employee" and ticket.created_by != current_user.id:
        return json_error(403, "forbidden", "Access denied")
    return {"ticket": ticket_schema.dump(ticket)}


@ticket_bp.route("/<int:ticket_id>", methods=["PUT", "PATCH"])
@jwt_required()
def update_ticket(ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    if not ticket:
        return json_error(404, "not_found", "Ticket not found")
    if current_user.role == "employee" and ticket.created_by != current_user.id:
        return json_error(403, "forbidden", "Access denied")

    data = request.get_json(silent=True) or {}
    try:
        payload = TicketUpdateSchema().load(data)
    except ValidationError as exc:
        return json_error(400, "validation_error", "Validation failed", exc.messages)

    for field in ["title", "description", "priority", "department_id"]:
        if field in payload:
            old_value = getattr(ticket, field)
            setattr(ticket, field, payload[field])
            record_ticket_history(ticket, field, old_value, payload[field], current_user.id)

    if "status" in payload:
        old_status = ticket.status
        ticket.status = payload["status"]
        if ticket.status == "resolved" and not ticket.resolved_at:
            ticket.resolved_at = datetime.utcnow()
        elif ticket.status != "resolved":
            ticket.resolved_at = None
        record_ticket_history(ticket, "status", old_status, ticket.status, current_user.id)

    if "assigned_to" in payload and current_user.role in {"admin", "technician"}:
        if payload["assigned_to"] and not db.session.get(User, payload["assigned_to"]):
            return json_error(404, "not_found", "Assigned technician not found")
        old_value = ticket.assigned_to
        ticket.assigned_to = payload["assigned_to"]
        record_ticket_history(ticket, "assigned_to", old_value, payload["assigned_to"], current_user.id)

    if "asset_id" in payload and current_user.role in {"admin", "technician"}:
        if payload["asset_id"] and not db.session.get(Asset, payload["asset_id"]):
            return json_error(404, "not_found", "Asset not found")
        ticket.asset_id = payload["asset_id"]

    ticket.updated_at = datetime.utcnow()
    db.session.commit()
    return {"ticket": ticket_schema.dump(ticket)}


@ticket_bp.route("/<int:ticket_id>", methods=["DELETE"])
@jwt_required()
@require_roles("admin", "technician")
def delete_ticket(ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    if not ticket:
        return json_error(404, "not_found", "Ticket not found")
    db.session.delete(ticket)
    db.session.commit()
    return {"message": "Ticket deleted"}


@ticket_bp.route("/<int:ticket_id>/status", methods=["PATCH"])
@jwt_required()
def change_ticket_status(ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    if not ticket:
        return json_error(404, "not_found", "Ticket not found")
    if current_user.role == "employee" and ticket.created_by != current_user.id:
        return json_error(403, "forbidden", "Access denied")

    data = request.get_json(silent=True) or {}
    try:
        payload = TicketStatusSchema().load(data)
    except ValidationError as exc:
        return json_error(400, "validation_error", "Validation failed", exc.messages)

    old_status = ticket.status
    ticket.status = payload["status"]
    if ticket.status == "resolved" and not ticket.resolved_at:
        ticket.resolved_at = datetime.utcnow()
    elif ticket.status != "resolved":
        ticket.resolved_at = None
    record_ticket_history(ticket, "status", old_status, ticket.status, current_user.id)
    ticket.updated_at = datetime.utcnow()
    db.session.commit()
    return {"ticket": ticket_schema.dump(ticket)}


@ticket_bp.route("/<int:ticket_id>/assign", methods=["PATCH"])
@jwt_required()
@require_roles("admin", "technician")
def assign_ticket(ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    if not ticket:
        return json_error(404, "not_found", "Ticket not found")

    data = request.get_json(silent=True) or {}
    try:
        payload = TicketAssignSchema().load(data)
    except ValidationError as exc:
        return json_error(400, "validation_error", "Validation failed", exc.messages)

    technician_id = payload["assigned_to"]
    tech = db.session.get(User, technician_id)
    if not tech or tech.role not in {"admin", "technician"}:
        return json_error(400, "validation_error", "Must be a valid technician", {"assigned_to": ["Must be a valid technician"]})

    old_assignment = ticket.assigned_to
    ticket.assigned_to = technician_id
    record_ticket_history(ticket, "assigned_to", old_assignment, technician_id, current_user.id)
    ticket.updated_at = datetime.utcnow()
    db.session.commit()
    return {"ticket": ticket_schema.dump(ticket)}


@ticket_bp.route("/<int:ticket_id>/history", methods=["GET"])
@jwt_required()
def ticket_history(ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    if not ticket:
        return json_error(404, "not_found", "Ticket not found")
    if current_user.role == "employee" and ticket.created_by != current_user.id:
        return json_error(403, "forbidden", "Access denied")

    history = TicketHistory.query.filter_by(ticket_id=ticket_id).order_by(TicketHistory.changed_at.desc())
    paginated = paginate_query(history)
    return {
        "items": [{
            "id": item.id,
            "field_changed": item.field_changed,
            "old_value": item.old_value,
            "new_value": item.new_value,
            "changed_by": item.changed_by,
            "changed_at": item.changed_at.isoformat() if item.changed_at else None,
        } for item in paginated.items],
        "page": paginated.page,
        "pages": paginated.pages,
        "total": paginated.total,
    }
