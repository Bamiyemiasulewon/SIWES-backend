from collections import Counter
from datetime import datetime

from flask import jsonify, request
from flask_jwt_extended import current_user, jwt_required
from flask_smorest import Blueprint

from app.extensions import db
from app.models import Asset, Request, User
from app.utils.helpers import json_error


dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


def _request_visibility_scope(user, req):
    if user.role == "admin":
        return True
    if user.role in {"student", "staff"}:
        return req.created_by == user.id
    if user.role == "maintenance_officer":
        return req.type == "maintenance"
    if user.role == "complaint_officer":
        if user.officer_scope == "department":
            return req.type == "complaint" and req.category in {"results", "registration"} and req.department_id == user.department_id
        if user.officer_scope == "bursary":
            return req.type == "complaint" and req.category == "fees"
        if user.officer_scope == "general":
            return req.type == "complaint" and req.category in {"hostel", "other"}
    return False


@dashboard_bp.route("/student", methods=["GET"])
@jwt_required()
def student_dashboard():
    if current_user.role not in {"student", "staff"}:
        return json_error(403, "forbidden", "Student access required")

    requests = [req for req in Request.query.filter_by(created_by=current_user.id).all()]
    by_status = Counter(req.status for req in requests)
    return {
        "student_id": current_user.id,
        "total_requests": len(requests),
        "by_status": dict(by_status),
        "requests": [{
            "id": req.id,
            "title": req.title,
            "status": req.status,
            "priority": req.priority,
            "type": req.type,
            "created_at": req.created_at.isoformat() if req.created_at else None,
        } for req in requests],
    }


@dashboard_bp.route("/officer", methods=["GET"])
@jwt_required()
def officer_dashboard():
    if current_user.role not in {"maintenance_officer", "complaint_officer", "admin"}:
        return json_error(403, "forbidden", "Officer access required")

    query = Request.query
    if current_user.role == "maintenance_officer":
        query = query.filter_by(type="maintenance")
    elif current_user.role == "complaint_officer":
        if current_user.officer_scope == "department":
            query = query.filter(Request.type == "complaint", Request.category.in_(["results", "registration"]), Request.department_id == current_user.department_id)
        elif current_user.officer_scope == "bursary":
            query = query.filter(Request.type == "complaint", Request.category == "fees")
        elif current_user.officer_scope == "general":
            query = query.filter(Request.type == "complaint", Request.category.in_(["hostel", "other"]))
    requests = [req for req in query.all() if _request_visibility_scope(current_user, req)]

    by_status = Counter(req.status for req in requests)
    by_priority = Counter(req.priority for req in requests)
    my_assigned = [req for req in requests if req.assigned_to == current_user.id]
    unassigned = [req for req in requests if req.assigned_to is None]
    reopened = [req for req in requests if req.status == "reopened"]

    return {
        "officer_id": current_user.id,
        "total_requests": len(requests),
        "by_status": dict(by_status),
        "by_priority": dict(by_priority),
        "unassigned_count": len(unassigned),
        "my_assigned_count": len(my_assigned),
        "reopened_count": len(reopened),
        "requests": [{
            "id": req.id,
            "title": req.title,
            "status": req.status,
            "priority": req.priority,
            "type": req.type,
            "assigned_to": req.assigned_to,
        } for req in requests],
    }


@dashboard_bp.route("/admin", methods=["GET"])
@jwt_required()
def admin_dashboard():
    if current_user.role != "admin":
        return json_error(403, "forbidden", "Admin access required")

    requests = Request.query.all()
    status_counts = Counter(req.status for req in requests)
    type_counts = Counter(req.type for req in requests)
    category_counts = Counter(req.category for req in requests)
    priority_counts = Counter(req.priority for req in requests)
    dept_counts = Counter(req.department_id for req in requests)
    resolved = [req for req in requests if req.resolved_at and req.created_at]
    avg_hours = 0.0
    if resolved:
        diffs = [(req.resolved_at - req.created_at).total_seconds() / 3600 for req in resolved]
        avg_hours = round(sum(diffs) / len(diffs), 2)

    last_30 = []
    for req in requests:
        if req.created_at and (datetime.utcnow() - req.created_at).days <= 30:
            last_30.append(req.created_at.date().isoformat())
    last_30_counts = Counter(last_30)

    return {
        "total_requests": len(requests),
        "by_type": dict(type_counts),
        "by_status": dict(status_counts),
        "by_category": dict(category_counts),
        "by_department": dict(dept_counts),
        "by_priority": dict(priority_counts),
        "average_resolution_hours": avg_hours,
        "flagged_count": sum(1 for req in requests if req.is_flagged),
        "reopened_count": sum(1 for req in requests if req.reopen_count > 0),
        "top_buildings": dict(Counter(req.building for req in requests if req.building)),
        "requests_per_day_last_30_days": dict(last_30_counts),
    }


@dashboard_bp.route("/assets", methods=["GET"])
@jwt_required()
def asset_dashboard():
    if current_user.role not in {"admin", "maintenance_officer", "complaint_officer"}:
        return json_error(403, "forbidden", "Asset access requires an officer or admin role")

    assets = Asset.query.all()
    counts_by_status = Counter(asset.status for asset in assets)
    counts_by_type = Counter(asset.type for asset in assets)
    return {
        "total_assets": len(assets),
        "counts_by_status": dict(counts_by_status),
        "counts_by_type": dict(counts_by_type),
        "assets": [{
            "id": asset.id,
            "name": asset.name,
            "type": asset.type,
            "status": asset.status,
            "building": asset.building,
            "room": asset.room,
            "department_id": asset.department_id,
        } for asset in assets],
    }
