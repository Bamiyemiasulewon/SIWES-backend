import pytest

from app import create_app
from app.extensions import db
from app.models import Department, User
from config import TestingConfig


@pytest.fixture
def client():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()

        dept_one = Department(name="Software Engineering", description="Department one")
        dept_two = Department(name="Computer Science", description="Department two")
        db.session.add_all([dept_one, dept_two])
        db.session.commit()

        admin = User(
            name="Admin User",
            email="adminsvc@test.com",
            role="admin",
            department_id=dept_one.id,
            matric_number="ADM987",
            level=500,
        )
        admin.password = "admin123"

        student_one = User(
            name="Student One",
            email="student1@test.com",
            role="student",
            department_id=dept_one.id,
            matric_number="SWE1001",
            level=200,
        )
        student_one.password = "student123"

        student_two = User(
            name="Student Two",
            email="student2@test.com",
            role="student",
            department_id=dept_two.id,
            matric_number="SWE1002",
            level=300,
        )
        student_two.password = "student123"

        staff = User(
            name="Staff User",
            email="staff@test.com",
            role="staff",
            department_id=dept_one.id,
            matric_number="STF1001",
            level=300,
        )
        staff.password = "staff123"

        complaint_officer = User(
            name="Complaint Officer",
            email="compofficer@test.com",
            role="complaint_officer",
            department_id=dept_one.id,
            matric_number="CMP1001",
            level=300,
            officer_scope="department",
        )
        complaint_officer.password = "officer123"

        db.session.add_all([admin, student_one, student_two, staff, complaint_officer])
        db.session.commit()

    with app.test_client() as client:
        yield client

    with app.app_context():
        db.session.remove()
        db.drop_all()


def _login(client, email, password):
    res = client.post(
        "/auth/login",
        json={"identifier": email, "password": password},
    )
    assert res.status_code == 200
    return res.get_json()["token"]


def test_anonymous_complaint_can_be_flagged_and_identity_revealed(client):
    student_token = _login(client, "student1@test.com", "student123")
    create = client.post(
        "/requests",
        json={
            "type": "complaint",
            "category": "results",
            "title": "My grades are wrong",
            "description": "The platform shows grades that are not mine.",
            "priority": "high",
            "is_anonymous": True,
            "department_id": 1,
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert create.status_code == 201
    request_id = create.get_json()["request"]["id"]

    admin_token = _login(client, "adminsvc@test.com", "admin123")
    flag = client.post(
        f"/requests/{request_id}/flag",
        json={
            "flag_type": "false_report",
            "reason": "This complaint contains misleading information and requires review.",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert flag.status_code == 201

    reveal = client.post(
        f"/requests/{request_id}/reveal-identity",
        json={"reason": "The anonymous report was found to be false and requires admin review."},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert reveal.status_code == 200
    payload = reveal.get_json()
    assert payload["revealed_creator"]["email"] == "student1@test.com"


def test_department_officer_cannot_view_other_department_complaints(client):
    student_token = _login(client, "student2@test.com", "student123")
    create = client.post(
        "/requests",
        json={
            "type": "complaint",
            "category": "results",
            "title": "Wrong department complaint",
            "description": "This complaint belongs to another department and should not be visible.",
            "priority": "medium",
            "is_anonymous": False,
            "department_id": 2,
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert create.status_code == 201
    request_id = create.get_json()["request"]["id"]

    officer_token = _login(client, "compofficer@test.com", "officer123")
    res = client.get(
        f"/requests/{request_id}",
        headers={"Authorization": f"Bearer {officer_token}"},
    )
    assert res.status_code == 403


def test_staff_cannot_create_maintenance_request(client):
    staff_token = _login(client, "staff@test.com", "staff123")
    res = client.post(
        "/requests",
        json={
            "type": "maintenance",
            "category": "electrical",
            "title": "Power issue",
            "description": "The wall socket stopped working.",
            "priority": "high",
            "building": "Science Block",
            "room": "SB-103",
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert res.status_code == 403
