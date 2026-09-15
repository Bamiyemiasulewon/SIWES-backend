from collections import Counter

from app.models import Ticket, Asset


def get_technician_summary(technician_id):
    tickets = Ticket.query.filter_by(assigned_to=technician_id).all()
    return {
        "technician_id": technician_id,
        "total_tickets": len(tickets),
        "by_status": dict(Counter(ticket.status for ticket in tickets)),
        "by_priority": dict(Counter(ticket.priority for ticket in tickets)),
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
    }


def get_executive_summary():
    tickets = Ticket.query.all()
    total_by_status = Counter(ticket.status for ticket in tickets)
    resolved_tickets = [ticket for ticket in tickets if ticket.resolved_at and ticket.created_at]
    avg_resolution_hours = 0
    if resolved_tickets:
        diffs = [
            (ticket.resolved_at - ticket.created_at).total_seconds() / 3600
            for ticket in resolved_tickets
        ]
        avg_resolution_hours = round(sum(diffs) / len(diffs), 2)

    return {
        "total_tickets": len(tickets),
        "total_by_status": dict(total_by_status),
        "average_resolution_hours": avg_resolution_hours,
        "tickets_per_department": dict(Counter(ticket.department_id for ticket in tickets)),
        "top_ticket_categories": dict(Counter(ticket.priority for ticket in tickets)),
        "resolved_tickets": len(resolved_tickets),
    }


def get_asset_summary():
    assets = Asset.query.all()
    return {
        "total_assets": len(assets),
        "counts_by_status": dict(Counter(asset.status for asset in assets)),
        "counts_by_type": dict(Counter(asset.type for asset in assets)),
        "assets_nearing_end_of_life": [
            {
                "id": asset.id,
                "name": asset.name,
                "status": asset.status,
                "serial_number": asset.serial_number,
            }
            for asset in assets
            if asset.type in {"laptop", "desktop", "monitor"}
        ],
        "frequently_repaired": [
            {
                "name": asset.name,
                "serial_number": asset.serial_number,
                "status": asset.status,
            }
            for asset in assets
            if asset.status == "in_repair"
        ],
    }
