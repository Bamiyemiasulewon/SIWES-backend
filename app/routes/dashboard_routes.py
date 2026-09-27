from collections import Counter
from datetime import datetime

from flask import jsonify
from flask_jwt_extended import jwt_required, current_user
from flask_smorest import Blueprint

from app.models import Ticket, Asset, User


dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/technician", methods=["GET"])
@jwt_required()
def technician_dashboard():
    if current_user.role not in {"admin", "technician"}:
        return jsonify({"error": "forbidden", "message": "Technician access required"}), 403

    tickets = Ticket.query.filter_by(assigned_to=current_user.id).all()
    by_status = Counter(ticket.status for ticket in tickets)
    by_priority = Counter(ticket.priority for ticket in tickets)

    return jsonify({
        "technician_id": current_user.id,
        "total_tickets": len(tickets),
        "by_status": dict(by_status),
        "by_priority": dict(by_priority),
        "tickets": [
            {
                "id": ticket.id,
                "title": ticket.title,
                "status": ticket.status,
                "priority": ticket.priority,
                "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
            }
            for ticket in tickets
        ],
    })


@dashboard_bp.route("/executive", methods=["GET"])
@jwt_required()
def executive_dashboard():
    if current_user.role != "admin":
        return jsonify({"error": "forbidden", "message": "Admin access required"}), 403

    tickets = Ticket.query.all()
    total_by_status = Counter(ticket.status for ticket in tickets)
    resolved_tickets = [ticket for ticket in tickets if ticket.resolved_at and ticket.created_at]
    average_resolution = 0
    if resolved_tickets:
        diffs = [
            (ticket.resolved_at - ticket.created_at).total_seconds() / 3600
            for ticket in resolved_tickets
        ]
        average_resolution = round(sum(diffs) / len(diffs), 2)

    by_department = Counter(ticket.department_id for ticket in tickets)
    top_categories = Counter(ticket.priority for ticket in tickets)

    return jsonify({
        "total_tickets": len(tickets),
        "total_by_status": dict(total_by_status),
        "average_resolution_hours": average_resolution,
        "tickets_per_department": dict(by_department),
        "top_ticket_categories": dict(top_categories),
        "resolved_tickets": len(resolved_tickets),
    })


@dashboard_bp.route("/assets", methods=["GET"])
@jwt_required()
def asset_dashboard():
    if current_user.role not in {"admin", "technician"}:
        return jsonify({"error": "forbidden", "message": "Admin or technician access required"}), 403

    assets = Asset.query.all()
    counts_by_status = Counter(asset.status for asset in assets)
    counts_by_type = Counter(asset.type for asset in assets)

    nearing_end_of_life = []
    for asset in assets:
        if asset.type in {"laptop", "desktop", "monitor"}:
            nearing_end_of_life.append({
                "id": asset.id,
                "name": asset.name,
                "status": asset.status,
                "serial_number": asset.serial_number,
            })

    return jsonify({
        "total_assets": len(assets),
        "counts_by_status": dict(counts_by_status),
        "counts_by_type": dict(counts_by_type),
        "assets_nearing_end_of_life": nearing_end_of_life,
        "frequently_repaired": [
            {
                "name": asset.name,
                "serial_number": asset.serial_number,
                "status": asset.status,
            }
            for asset in assets
            if asset.status == "in_repair"
        ],
    })
