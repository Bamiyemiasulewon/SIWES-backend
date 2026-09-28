from datetime import timedelta

import pytest
from flask_jwt_extended import create_access_token

from app import create_app
from app.extensions import db
from app.models import Department, User
from config import TestingConfig


@pytest.fixture
def client():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()

        dept = Department(name="Software Engineering", description="Support")
        db.session.add(dept)
        db.session.commit()

        admin = User(
            name="Admin",
            email="admin@test.com",
            role="admin",
            department_id=dept.id,
            matric_number="ADM001",
        )
        admin.password = "admin123"

        student = User(
            name="Student",
            email="student@test.com",
            role="student",
            department_id=dept.id,
            matric_number="SWE2023001",
            level=200,
        )
        student.password = "student123"

        db.session.add_all([admin, student])
        db.session.commit()

    with app.test_client() as client:
        yield client

    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_register_rejects_client_role_and_allows_login_by_matric(client):
    res = client.post(
        "/auth/register",
        json={
            "name": "Alice",
            "email": "alice@example.com",
            "matric_number": "SWE2023002",
            "department_id": 1,
            "level": 300,
            "password": "secret123",
            "role": "staff",
        },
    )
    assert res.status_code == 201
    payload = res.get_json()
    assert payload["user"]["role"] == "student"

    login = client.post(
        "/auth/login",
        json={
            "identifier": "SWE2023002",
            "password": "secret123",
        },
    )
    assert login.status_code == 200
    assert "token" in login.get_json()


def test_admin_can_create_staff_user(client):
    login = client.post(
        "/auth/login",
        json={
            "identifier": "admin@test.com",
            "password": "admin123",
        },
    )
    token = login.get_json()["token"]

    res = client.post(
        "/users",
        json={
            "name": "Staff One",
            "email": "staff1@example.com",
            "role": "staff",
            "department_id": 1,
            "password": "staff123",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    data = res.get_json()["user"]
    assert data["role"] == "staff"


def test_unauthenticated_requests_are_rejected(client):
    res = client.get("/auth/me")
    assert res.status_code == 401
    payload = res.get_json()
    assert payload["error"] in {"unauthorized", "token_expired"}


def test_expired_jwt_is_rejected(client):
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        user = User(
            name="Expired User",
            email="expired@test.com",
            role="student",
            department_id=1,
            matric_number="EXP001",
        )
        user.password = "expired123"
        db.session.add(user)
        db.session.commit()
        expired = create_access_token(identity=str(user.id), expires_delta=timedelta(seconds=-10))

    res = client.get("/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert res.status_code == 401
    assert res.get_json()["error"] == "token_expired"


def test_tampered_jwt_is_rejected(client):
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIn0.bad-signature"
    res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401
    assert res.get_json()["error"] in {"unauthorized", "invalid_token"}


def test_student_cannot_escalate_role(client):
    login = client.post(
        "/auth/login",
        json={
            "identifier": "student@test.com",
            "password": "student123",
        },
    )
    token = login.get_json()["token"]

    res = client.post(
        "/users",
        json={
            "name": "Hacker",
            "email": "hacker@example.com",
            "password": "pw123",
            "role": "admin",
            "department_id": 1,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403


def test_sql_injection_like_input_is_rejected(client):
    res = client.post(
        "/auth/register",
        json={
            "name": "admin' OR '1'='1",
            "email": "admin@example.com'; DROP TABLE users; --",
            "matric_number": "ATTACK01",
            "department_id": 1,
            "level": 100,
            "password": "secret123",
        },
    )
    assert res.status_code in {400, 409}
