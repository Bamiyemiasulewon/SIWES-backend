from app import create_app
from app.extensions import db
from app.models import Asset, Department, IdentityRevealLog, Request, RequestHistory, User


app = create_app()


def seed_data():
    with app.app_context():
        db.drop_all()
        db.create_all()

        department_names = [
            "Software Engineering",
            "Computer Science",
            "Information Systems",
            "Information Technology",
            "Cyber Security",
            "Data Science",
        ]
        departments = {name: Department(name=name, description=f"{name} department") for name in department_names}
        db.session.add_all(departments.values())
        db.session.commit()

        dept_by_name = {d.name: d for d in departments.values()}
        admin = User(name="Ada Admin", email="admin@school.com", role="admin", department_id=dept_by_name["Software Engineering"].id, matric_number="ADM001", level=500)
        admin.password = "admin123"

        maintenance_staff = [
            User(name="Megan Boiler", email="maint1@school.com", role="maintenance_officer", department_id=dept_by_name["Software Engineering"].id, matric_number="MNT001", level=400, officer_scope="department"),
            User(name="David Pipe", email="maint2@school.com", role="maintenance_officer", department_id=dept_by_name["Information Technology"].id, matric_number="MNT002", level=400, officer_scope="department"),
        ]
        for user in maintenance_staff:
            user.password = "maint123"

        staff = User(name="Jane Staff", email="staff@school.com", role="staff", department_id=dept_by_name["Computer Science"].id, matric_number="STF001", level=300)
        staff.password = "staff123"

        complaint_officers = []
        for idx, dept_name in enumerate(department_names, start=1):
            user = User(
                name=f"Officer {idx}",
                email=f"complaint{idx}@school.com",
                role="complaint_officer",
                department_id=dept_by_name[dept_name].id,
                matric_number=f"CMP{idx:03d}",
                level=300,
                officer_scope="department",
            )
            user.password = "officer123"
            complaint_officers.append(user)

        bursary_officer = User(name="Bursary Officer", email="bursary@school.com", role="complaint_officer", department_id=dept_by_name["Information Systems"].id, matric_number="BRS001", level=300, officer_scope="bursary")
        bursary_officer.password = "officer123"

        general_officer = User(name="General Officer", email="general@school.com", role="complaint_officer", department_id=dept_by_name["Data Science"].id, matric_number="GEN001", level=300, officer_scope="general")
        general_officer.password = "officer123"

        students = []
        for idx, dept_name in enumerate(department_names, start=1):
            student = User(
                name=f"Student {idx}",
                email=f"student{idx}@school.com",
                role="student",
                department_id=dept_by_name[dept_name].id,
                matric_number=f"SWE{idx:04d}",
                level=(100 + (idx % 5) * 100),
            )
            student.password = "student123"
            students.append(student)

        db.session.add_all([admin, staff, bursary_officer, general_officer] + maintenance_staff + complaint_officers + students)
        db.session.commit()

        assets = [
            Asset(name="Projector 01", type="projector", serial_number="PRJ-001", status="active", building="Science Block", room="SB-101", department_id=dept_by_name["Computer Science"].id),
            Asset(name="Laptop Lab 02", type="lab_equipment", serial_number="LAB-002", status="active", building="Engineering Hub", room="EH-204", department_id=dept_by_name["Software Engineering"].id),
            Asset(name="HVAC Unit 01", type="hvac", serial_number="HVAC-001", status="active", building="ICT Hall", room="ICT-8", department_id=dept_by_name["Information Technology"].id),
            Asset(name="Generator 01", type="generator", serial_number="GEN-001", status="active", building="Central Plant", room="CP-02", department_id=dept_by_name["Cyber Security"].id),
            Asset(name="Lecture Desk", type="furniture", serial_number="FUR-001", status="active", building="Data Center", room="DC-12", department_id=dept_by_name["Data Science"].id),
        ]
        db.session.add_all(assets)
        db.session.commit()

        request_data = [
            {
                "type": "complaint",
                "category": "results",
                "title": "Results portal shows wrong marks",
                "description": "The results portal is showing duplicate grade entries for my course.",
                "priority": "high",
                "status": "submitted",
                "created_by": students[0].id,
                "department_id": dept_by_name["Software Engineering"].id,
                "building": "Academic Block",
                "room": "AB-203",
                "is_anonymous": True,
            },
            {
                "type": "maintenance",
                "category": "electrical",
                "title": "Power failure in lab",
                "description": "A complete power outage in the lab has stopped work and created a risk.",
                "priority": "critical",
                "status": "assigned",
                "created_by": students[1].id,
                "department_id": dept_by_name["Computer Science"].id,
                "building": "Engineering Hub",
                "room": "EH-201",
                "assigned_to": maintenance_staff[0].id,
            },
            {
                "type": "complaint",
                "category": "fees",
                "title": "Tuition payment mismatch",
                "description": "The payment portal is showing a duplicate charge for my school fees.",
                "priority": "medium",
                "status": "in_progress",
                "created_by": students[2].id,
                "department_id": dept_by_name["Information Systems"].id,
                "building": "Finance Block",
                "room": "FB-02",
                "assigned_to": bursary_officer.id,
            },
            {
                "type": "maintenance",
                "category": "hostel",
                "title": "Water leakage in hostel room",
                "description": "Water collects near the room door after rainfall causing a safety issue.",
                "priority": "high",
                "status": "resolved",
                "created_by": students[3].id,
                "department_id": dept_by_name["Information Technology"].id,
                "building": "Hostel A",
                "room": "A-12",
                "assigned_to": maintenance_staff[1].id,
                "resolution_notes": "Plumber fixed the pipe and cleaned the area.",
                "resolved_at": "2026-09-10T10:00:00",
            },
            {
                "type": "complaint",
                "category": "lecturer_conduct",
                "title": "Late lecturer attendance",
                "description": "The lecturer continues to cancel classes and does not provide clear timelines.",
                "priority": "medium",
                "status": "submitted",
                "created_by": students[4].id,
                "department_id": dept_by_name["Cyber Security"].id,
                "building": "Faculty Tower",
                "room": "FT-104",
            },
        ]
        created_requests = []
        for item in request_data:
            req = Request(
                type=item["type"],
                category=item["category"],
                title=item["title"],
                description=item["description"],
                priority=item["priority"],
                status=item["status"],
                is_anonymous=item.get("is_anonymous", False),
                created_by=item["created_by"],
                department_id=item["department_id"],
                building=item.get("building"),
                room=item.get("room"),
                assigned_to=item.get("assigned_to"),
                resolution_notes=item.get("resolution_notes"),
                resolved_at=item.get("resolved_at"),
            )
            if isinstance(item.get("resolved_at"), str):
                from datetime import datetime
                req.resolved_at = datetime.fromisoformat(item["resolved_at"])
            created_requests.append(req)
        db.session.add_all(created_requests)
        db.session.commit()

        for req in Request.query.all():
            if req.status == "submitted":
                req.history.append(RequestHistory(request_id=req.id, changed_by=req.created_by, field_changed="status", old_value=None, new_value=req.status, note="Request submitted"))
            if req.status == "assigned":
                req.history.append(RequestHistory(request_id=req.id, changed_by=req.assigned_to, field_changed="status", old_value="submitted", new_value="assigned", note="Request assigned"))
            if req.status == "in_progress":
                req.history.append(RequestHistory(request_id=req.id, changed_by=req.assigned_to, field_changed="status", old_value="assigned", new_value="in_progress", note="Now in progress"))
            if req.status == "resolved":
                req.history.append(RequestHistory(request_id=req.id, changed_by=req.assigned_to, field_changed="status", old_value="in_progress", new_value="resolved", note="Request resolved"))
        db.session.commit()

        print("Demo credentials:")
        print("admin@example.com / admin123")
        print("maint1@school.com / maint123")
        print("student1@school.com / student123")


if __name__ == "__main__":
    seed_data()
