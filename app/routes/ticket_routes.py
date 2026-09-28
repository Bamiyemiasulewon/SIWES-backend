from datetime import datetime

from flask import request
from flask_jwt_extended import current_user, jwt_required
from flask_smorest import Blueprint
from marshmallow import ValidationError

from app.extensions import db
from app.models import Asset, Department, IdentityRevealLog, Request, RequestHistory, User
from app.schemas import TicketAssignSchema, TicketCreateSchema, TicketHistorySchema, TicketSchema, TicketStatusSchema, TicketUpdateSchema
from app.utils.helpers import json_error, paginate_query

request_bp = Blueprint("requests", __name__, url_prefix="/requests")
ticket_bp = Blueprint("tickets", __name__, url_prefix="/tickets")
ticket_schema = TicketSchema()


def _serialize_request(req, viewer):
    if viewer is None:
        viewer = current_user
    if req.is_anonymous and viewer.id != req.created_by and viewer.role != "admin":
        data = ticket_schema.dump(req)
        data["created_by"] = None
        data["created_by_name"] = "Anonymous"
        data["creator_email"] = None
        data["creator_matric_number"] = None
        data["creator_level"] = None
        return data
    return ticket_schema.dump(req)


def record_request_history(request_obj, field, old_value, new_value, changed_by, note=None):
    if old_value == new_value:
        return
    history = RequestHistory(
        request_id=request_obj.id,
        changed_by=changed_by,
        field_changed=field,
        old_value=str(old_value) if old_value is not None else None,
        new_value=str(new_value) if new_value is not None else None,
        note=note,
    )
    db.session.add(history)


@request_bp.route("", methods=["GET"])
@jwt_required()
def list_requests():
    query = Request.query
    if current_user.role == "student":
        query = query.filter_by(created_by=current_user.id)
    elif current_user.role == "staff":
        query = query.filter_by(created_by=current_user.id)
    elif current_user.role == "maintenance_officer":
        query = query.filter((Request.type == "maintenance") | (Request.assigned_to == current_user.id))
    elif current_user.role == "complaint_officer":
        if current_user.officer_scope == "department":
            query = query.filter(Request.type == "complaint", Request.category.in_(["results", "registration"]))
            query = query.filter(Request.department_id == current_user.department_id)
        elif current_user.officer_scope == "bursary":
            query = query.filter(Request.type == "complaint", Request.category == "fees")
        elif current_user.officer_scope == "general":
            query = query.filter(Request.type == "complaint", Request.category.in_(["hostel", "other"]))
    elif current_user.role != "admin":
        return json_error(403, "forbidden", "Access denied")

    if request.args.get("type"):
        query = query.filter_by(type=request.args.get("type"))
    if request.args.get("category"):
        query = query.filter_by(category=request.args.get("category"))
    if request.args.get("status"):
        query = query.filter_by(status=request.args.get("status"))
    if request.args.get("priority"):
        query = query.filter_by(priority=request.args.get("priority"))
    if request.args.get("department_id"):
        query = query.filter_by(department_id=request.args.get("department_id", type=int))
    if request.args.get("assigned_to"):
        if current_user.role in {"admin", "maintenance_officer", "complaint_officer"} or int(request.args.get("assigned_to")) == current_user.id:
            query = query.filter_by(assigned_to=request.args.get("assigned_to", type=int))
    if request.args.get("building"):
        query = query.filter_by(building=request.args.get("building"))
    if request.args.get("is_flagged"):
        query = query.filter_by(is_flagged=request.args.get("is_flagged", type=int))
    if request.args.get("q"):
        query = query.filter(Request.title.ilike(f"%{request.args.get('q')}%"))
    if request.args.get("created_by") and (current_user.role == "admin" or int(request.args.get("created_by")) == current_user.id):
        query = query.filter_by(created_by=request.args.get("created_by", type=int))

    paginated = paginate_query(query)
    return {
        "items": [_serialize_request(item, current_user) for item in paginated.items],
        "page": paginated.page,
        "pages": paginated.pages,
        "total": paginated.total,
    }


@request_bp.route("", methods=["POST"])
@jwt_required()
def create_request():
    data = request.get_json(silent=True) or {}
    try:
        payload = TicketCreateSchema().load(data)
    except ValidationError as exc:
        return json_error(400, "validation_error", "Validation failed", exc.messages)

    if payload["type"] == "maintenance" and current_user.role == "staff":
        return json_error(403, "forbidden", "Staff cannot create maintenance requests")
    if payload["type"] == "maintenance" and payload.get("building") is None:
        return json_error(400, "validation_error", "Building is required for maintenance requests", {"building": ["Required"]})
    if payload["type"] == "maintenance" and payload.get("room") is None:
        return json_error(400, "validation_error", "Room is required for maintenance requests", {"room": ["Required"]})
    if payload["type"] == "maintenance" and payload.get("category") == "electrical" and payload.get("priority") not in {"high", "critical"}:
        return json_error(400, "validation_error", "Electrical maintenance requests must be at least high priority")

    if payload.get("asset_id") and not db.session.get(Asset, payload["asset_id"]):
        return json_error(404, "not_found", "Asset not found")
    if payload.get("department_id") and not db.session.get(Department, payload["department_id"]):
        return json_error(404, "not_found", "Department not found")

    req = Request(
        type=payload["type"],
        category=payload["category"],
        title=payload["title"].strip(),
        description=payload["description"].strip(),
        priority=payload.get("priority", "medium"),
        status="submitted",
        is_anonymous=bool(payload.get("is_anonymous", False)),
        created_by=current_user.id,
        department_id=payload.get("department_id") or current_user.department_id,
        building=payload.get("building"),
        room=payload.get("room"),
        course_code=payload.get("course_code"),
        asset_id=payload.get("asset_id"),
        assigned_to=payload.get("assigned_to"),
    )
    db.session.add(req)
    db.session.commit()
    record_request_history(req, "created", None, "request_created", current_user.id, note="Request created")
    db.session.commit()
    return {"request": ticket_schema.dump(req)}, 201


@request_bp.route("/<int:request_id>", methods=["GET"])
@jwt_required()
def get_request(request_id):
    req = db.session.get(Request, request_id)
    if not req:
        return json_error(404, "not_found", "Request not found")
    if current_user.role == "student" and req.created_by != current_user.id:
        return json_error(403, "forbidden", "Access denied")
    if current_user.role == "staff" and req.created_by != current_user.id:
        return json_error(403, "forbidden", "Access denied")
    if current_user.role == "maintenance_officer" and req.type != "maintenance":
        return json_error(403, "forbidden", "Access denied")
    if current_user.role == "complaint_officer":
        if current_user.officer_scope == "department" and not (
            req.type == "complaint" and req.category in ["results", "registration"] and req.department_id == current_user.department_id
        ):
            return json_error(403, "forbidden", "Access denied")
        if current_user.officer_scope == "bursary" and not (req.type == "complaint" and req.category == "fees"):
            return json_error(403, "forbidden", "Access denied")
        if current_user.officer_scope == "general" and not (req.type == "complaint" and req.category in ["hostel", "other"]):
            return json_error(403, "forbidden", "Access denied")
    return {"request": _serialize_request(req, current_user)}


@request_bp.route("/<int:request_id>", methods=["PATCH"])
@jwt_required()
def update_request(request_id):
    req = db.session.get(Request, request_id)
    if not req:
        return json_error(404, "not_found", "Request not found")
    if current_user.role not in {"admin"} and req.created_by != current_user.id:
        return json_error(403, "forbidden", "Access denied")
    if current_user.role != "admin" and req.status != "submitted":
        return json_error(400, "bad_request", "Only submitted requests can be edited by the owner")

    data = request.get_json(silent=True) or {}
    try:
        payload = TicketUpdateSchema().load(data)
    except ValidationError as exc:
        return json_error(400, "validation_error", "Validation failed", exc.messages)

    for field in ["title", "description", "priority", "is_anonymous", "building", "room", "course_code", "asset_id", "department_id"]:
        if field in payload:
            if field == "asset_id" and payload[field] and not db.session.get(Asset, payload[field]):
                return json_error(404, "not_found", "Asset not found")
            if field == "department_id" and payload[field] and not db.session.get(Department, payload[field]):
                return json_error(404, "not_found", "Department not found")
            old_value = getattr(req, field)
            setattr(req, field, payload[field])
            record_request_history(req, field, old_value, payload[field], current_user.id)

    req.updated_at = datetime.utcnow()
    db.session.commit()
    return {"request": ticket_schema.dump(req)}


@request_bp.route("/<int:request_id>", methods=["DELETE"])
@jwt_required()
def delete_request(request_id):
    if current_user.role != "admin":
        return json_error(403, "forbidden", "Admin access required")
    req = db.session.get(Request, request_id)
    if not req:
        return json_error(404, "not_found", "Request not found")
    db.session.delete(req)
    db.session.commit()
    return {"message": "Request deleted"}


@request_bp.route("/<int:request_id>/assign", methods=["PATCH"])
@jwt_required()
def assign_request(request_id):
    req = db.session.get(Request, request_id)
    if not req:
        return json_error(404, "not_found", "Request not found")
    if current_user.role not in {"admin", "maintenance_officer", "complaint_officer"}:
        return json_error(403, "forbidden", "Access denied")

    data = request.get_json(silent=True) or {}
    try:
        payload = TicketAssignSchema().load(data)
    except ValidationError as exc:
        return json_error(400, "validation_error", "Validation failed", exc.messages)

    user = db.session.get(User, payload["assigned_to"])
    if not user:
        return json_error(404, "not_found", "User not found")
    if user.role not in {"maintenance_officer", "complaint_officer", "admin"}:
        return json_error(400, "validation_error", "Assigned user must be an officer or admin")

    old_value = req.assigned_to
    req.assigned_to = user.id
    req.status = "assigned"
    record_request_history(req, "assigned_to", old_value, user.id, current_user.id)
    record_request_history(req, "status", old_value if False else req.status, "assigned", current_user.id)
    req.updated_at = datetime.utcnow()
    db.session.commit()
    return {"request": ticket_schema.dump(req)}


@request_bp.route("/<int:request_id>/status", methods=["PATCH"])
@jwt_required()
def change_request_status(request_id):
    req = db.session.get(Request, request_id)
    if not req:
        return json_error(404, "not_found", "Request not found")

    data = request.get_json(silent=True) or {}
    try:
        payload = TicketStatusSchema().load(data)
    except ValidationError as exc:
        return json_error(400, "validation_error", "Validation failed", exc.messages)

    new_status = payload["status"]
    if current_user.role == "student" and req.created_by != current_user.id:
        return json_error(403, "forbidden", "Access denied")
    if current_user.role != "admin" and req.assigned_to not in {current_user.id, None} and req.created_by != current_user.id:
        return json_error(403, "forbidden", "Access denied")

    if req.status == "submitted" and new_status != "assigned":
        return json_error(400, "bad_request", "Submitted requests can only move to assigned")
    if req.status == "assigned" and new_status not in {"in_progress"}:
        return json_error(400, "bad_request", "Assigned requests can only move to in_progress")
    if req.status == "in_progress" and new_status not in {"resolved"}:
        return json_error(400, "bad_request", "In progress requests can only move to resolved")
    if req.status == "resolved" and new_status not in {"reopened", "closed"}:
        return json_error(400, "bad_request", "Resolved requests can only move to reopened or closed")
    if req.status == "reopened" and new_status != "in_progress":
        return json_error(400, "bad_request", "Reopened requests can only move to in_progress")
    if req.status == "closed":
        return json_error(400, "bad_request", "Closed requests cannot change")

    old_status = req.status
    req.status = new_status
    if new_status == "resolved":
        req.resolved_at = datetime.utcnow()
        if not payload.get("resolution_notes"):
            return json_error(400, "validation_error", "Resolution notes are required", {"resolution_notes": ["Required"]})
        req.resolution_notes = payload.get("resolution_notes")
    if new_status == "closed":
        req.closed_at = datetime.utcnow()
    if new_status == "reopened":
        if req.created_by != current_user.id:
            return json_error(403, "forbidden", "Only the creator can reopen a request")
        if not payload.get("reason"):
            return json_error(400, "validation_error", "Reason is required for reopening", {"reason": ["Required"]})
        req.reopen_count += 1
    record_request_history(req, "status", old_status, new_status, current_user.id, note=payload.get("reason") or payload.get("resolution_notes"))
    req.updated_at = datetime.utcnow()
    db.session.commit()
    return {"request": _serialize_request(req, current_user)}


@request_bp.route("/<int:request_id>/flag", methods=["POST"])
@jwt_required()
def flag_request(request_id):
    req = db.session.get(Request, request_id)
    if not req:
        return json_error(404, "not_found", "Request not found")
    if current_user.role not in {"admin", "maintenance_officer", "complaint_officer"}:
        return json_error(403, "forbidden", "Only officers and admins can flag requests")
    data = request.get_json(silent=True) or {}
    flag_type = data.get("flag_type")
    reason = data.get("reason")
    if flag_type not in {"abuse", "threat", "false_report"}:
        return json_error(400, "validation_error", "flag_type must be abuse, threat or false_report", {"flag_type": ["Invalid value"]})
    if not reason or len(str(reason).strip()) < 10:
        return json_error(400, "validation_error", "Reason is required and must be at least 10 characters", {"reason": ["Minimum 10 characters required"]})
    req.is_flagged = True
    req.flag_type = flag_type
    req.flag_reason = reason
    req.flagged_by = current_user.id
    req.flagged_at = datetime.utcnow()
    record_request_history(req, "flagged", None, flag_type, current_user.id, note=reason)
    db.session.commit()
    return {"request": _serialize_request(req, current_user), "message": "Request flagged"}, 201


@request_bp.route("/<int:request_id>/unflag", methods=["POST"])
@jwt_required()
def unflag_request(request_id):
    if current_user.role != "admin":
        return json_error(403, "forbidden", "Only admins can unflag requests")
    req = db.session.get(Request, request_id)
    if not req:
        return json_error(404, "not_found", "Request not found")
    data = request.get_json(silent=True) or {}
    reason = data.get("reason")
    if not reason or len(str(reason).strip()) < 10:
        return json_error(400, "validation_error", "Reason is required and must be at least 10 characters", {"reason": ["Minimum 10 characters required"]})
    req.is_flagged = False
    req.flag_type = None
    req.flag_reason = None
    req.flagged_by = None
    req.flagged_at = None
    record_request_history(req, "unflagged", True, False, current_user.id, note=reason)
    db.session.commit()
    return {"request": _serialize_request(req, current_user), "message": "Request unflagged"}


@request_bp.route("/<int:request_id>/reveal-identity", methods=["POST"])
@jwt_required()
def reveal_identity(request_id):
    if current_user.role != "admin":
        return json_error(403, "forbidden", "Admin access required")
    req = db.session.get(Request, request_id)
    if not req:
        return json_error(404, "not_found", "Request not found")
    if not req.is_anonymous or not req.is_flagged:
        return json_error(403, "forbidden", "Only anonymous flagged requests can be revealed")
    data = request.get_json(silent=True) or {}
    reason = data.get("reason")
    if not reason or len(str(reason).strip()) < 10:
        return json_error(400, "validation_error", "Reason is required and must be at least 10 characters", {"reason": ["Minimum 10 characters required"]})
    creator = db.session.get(User, req.created_by)
    if creator is None:
        return json_error(404, "not_found", "Request creator not found")
    req.identity_revealed = True
    record_request_history(req, "identity_revealed", False, True, current_user.id, note=reason)
    db.session.add(IdentityRevealLog(request_id=req.id, admin_id=current_user.id, reason=reason))
    db.session.commit()
    return {
        "request_id": req.id,
        "revealed_creator": {
            "name": creator.name,
            "email": creator.email,
            "matric_number": creator.matric_number,
            "level": creator.level,
            "department_id": creator.department_id,
        },
        "message": "Identity revealed",
    }


@request_bp.route("/identity-reveals", methods=["GET"])
@jwt_required()
def identity_reveals():
    if current_user.role != "admin":
        return json_error(403, "forbidden", "Admin access required")
    query = IdentityRevealLog.query.order_by(IdentityRevealLog.revealed_at.desc())
    paginated = paginate_query(query)
    return {
        "items": [{
            "id": item.id,
            "request_id": item.request_id,
            "admin_id": item.admin_id,
            "reason": item.reason,
            "revealed_at": item.revealed_at.isoformat() if item.revealed_at else None,
        } for item in paginated.items],
        "page": paginated.page,
        "pages": paginated.pages,
        "total": paginated.total,
    }


@request_bp.route("/<int:request_id>/reopen", methods=["POST"])
@jwt_required()
def reopen_request(request_id):
    req = db.session.get(Request, request_id)
    if not req:
        return json_error(404, "not_found", "Request not found")
    if req.created_by != current_user.id:
        return json_error(403, "forbidden", "Only the creator can reopen the request")
    if req.status != "resolved":
        return json_error(400, "bad_request", "Only resolved requests can be reopened")
    data = request.get_json(silent=True) or {}
    if not data.get("reason") or len(str(data.get("reason")).strip()) < 10:
        return json_error(400, "validation_error", "Reason must be at least 10 characters", {"reason": ["Minimum 10 characters required"]})
    req.status = "reopened"
    req.reopen_count += 1
    record_request_history(req, "status", "resolved", "reopened", current_user.id, note=data["reason"])
    req.updated_at = datetime.utcnow()
    db.session.commit()
    return {"request": ticket_schema.dump(req)}


@request_bp.route("/<int:request_id>/history", methods=["GET"])
@jwt_required()
def request_history(request_id):
    req = db.session.get(Request, request_id)
    if not req:
        return json_error(404, "not_found", "Request not found")
    if current_user.role == "student" and req.created_by != current_user.id:
        return json_error(403, "forbidden", "Access denied")
    if current_user.role == "staff" and req.created_by != current_user.id:
        return json_error(403, "forbidden", "Access denied")
    if current_user.role == "maintenance_officer" and req.type != "maintenance":
        return json_error(403, "forbidden", "Access denied")
    if current_user.role == "complaint_officer":
        if current_user.officer_scope == "department" and not (
            req.type == "complaint" and req.category in ["results", "registration"] and req.department_id == current_user.department_id
        ):
            return json_error(403, "forbidden", "Access denied")
        if current_user.officer_scope == "bursary" and not (req.type == "complaint" and req.category == "fees"):
            return json_error(403, "forbidden", "Access denied")
        if current_user.officer_scope == "general" and not (req.type == "complaint" and req.category in ["hostel", "other"]):
            return json_error(403, "forbidden", "Access denied")

    history = RequestHistory.query.filter_by(request_id=request_id).order_by(RequestHistory.changed_at.desc())
    paginated = paginate_query(history)
    return {
        "items": [{
            "id": item.id,
            "field_changed": item.field_changed,
            "old_value": item.old_value,
            "new_value": item.new_value,
            "note": item.note,
            "changed_by": item.changed_by,
            "changed_at": item.changed_at.isoformat() if item.changed_at else None,
        } for item in paginated.items],
        "page": paginated.page,
        "pages": paginated.pages,
        "total": paginated.total,
    }


@ticket_bp.route("", methods=["GET"])
@jwt_required()
def list_tickets_legacy():
    return list_requests()


@ticket_bp.route("", methods=["POST"])
@jwt_required()
def create_ticket_legacy():
    return create_request()


@ticket_bp.route("/<int:ticket_id>", methods=["GET"])
@jwt_required()
def get_ticket_legacy(ticket_id):
    return get_request(ticket_id)


@ticket_bp.route("/<int:ticket_id>", methods=["PUT", "PATCH"])
@jwt_required()
def update_ticket_legacy(ticket_id):
    return update_request(ticket_id)


@ticket_bp.route("/<int:ticket_id>", methods=["DELETE"])
@jwt_required()
def delete_ticket_legacy(ticket_id):
    return delete_request(ticket_id)


@ticket_bp.route("/<int:ticket_id>/status", methods=["PATCH"])
@jwt_required()
def change_ticket_status_legacy(ticket_id):
    return change_request_status(ticket_id)


@ticket_bp.route("/<int:ticket_id>/assign", methods=["PATCH"])
@jwt_required()
def assign_ticket_legacy(ticket_id):
    return assign_request(ticket_id)


@ticket_bp.route("/<int:ticket_id>/history", methods=["GET"])
@jwt_required()
def ticket_history_legacy(ticket_id):
    return request_history(ticket_id)
