from datetime import timedelta

import pytest
from flask_jwt_extended import create_access_token

from app import create_app
from app.extensions import db
from app.models import User, Department
from config import TestingConfig


@pytest.fixture
def client():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        dept = Department(name="IT", description="Support")
        db.session.add(dept)
        db.session.commit()

        admin = User(name="Admin", email="admin@test.com", role="admin", department_id=dept.id)
        admin.password = "admin123"
        employee = User(name="Employee", email="employee@test.com", role="employee", department_id=dept.id)
        employee.password = "emp123"
        db.session.add_all([admin, employee])
        db.session.commit()

    with app.test_client() as client:
        yield client

    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_register_and_login(client):
    res = client.post('/auth/register', json={
        'name': 'Alice',
        'email': 'alice@example.com',
        'password': 'secret123'
    })
    assert res.status_code == 201
    payload = res.get_json()
    assert 'token' in payload and 'user' in payload

    login = client.post('/auth/login', json={
        'email': 'alice@example.com',
        'password': 'secret123'
    })
    assert login.status_code == 200
    assert 'token' in login.get_json()


def test_employee_cannot_access_admin_users(client):
    login = client.post('/auth/login', json={
        'email': 'employee@test.com',
        'password': 'emp123'
    })
    token = login.get_json()['token']

    res = client.get('/users', headers={'Authorization': f'Bearer {token}'})
    assert res.status_code == 403


def test_invalid_ticket_payload_returns_400(client):
    login = client.post('/auth/login', json={
        'email': 'employee@test.com',
        'password': 'emp123'
    })
    token = login.get_json()['token']

    res = client.post('/tickets', json={'description': 'Missing title'}, headers={'Authorization': f'Bearer {token}'})
    assert res.status_code == 400


def test_ticket_history_is_recorded_on_status_change(client):
    login = client.post('/auth/login', json={
        'email': 'employee@test.com',
        'password': 'emp123'
    })
    token = login.get_json()['token']

    ticket_res = client.post('/tickets', json={
        'title': 'Printer issue',
        'description': 'Printer not responding',
        'priority': 'medium'
    }, headers={'Authorization': f'Bearer {token}'})
    ticket_id = ticket_res.get_json()['ticket']['id']

    change = client.patch(f'/tickets/{ticket_id}/status', json={'status': 'in_progress'}, headers={'Authorization': f'Bearer {token}'})
    assert change.status_code == 200

    history = client.get(f'/tickets/{ticket_id}/history', headers={'Authorization': f'Bearer {token}'})
    assert history.status_code == 200
    assert len(history.get_json()['items']) >= 1


def test_unauthenticated_requests_are_rejected(client):
    res = client.get('/auth/me')
    assert res.status_code == 401
    payload = res.get_json()
    assert payload['error'] in {'unauthorized', 'token_expired'}


def test_expired_jwt_is_rejected(client):
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        user = User(name='Expired User', email='expired@test.com', role='employee', department_id=1)
        user.password = 'expired123'
        db.session.add(user)
        db.session.commit()
        expired = create_access_token(identity=str(user.id), expires_delta=timedelta(seconds=-10))

    res = client.get('/auth/me', headers={'Authorization': f'Bearer {expired}'})
    assert res.status_code == 401
    assert res.get_json()['error'] == 'token_expired'


def test_tampered_jwt_is_rejected(client):
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIn0.bad-signature'
    res = client.get('/auth/me', headers={'Authorization': f'Bearer {token}'})
    assert res.status_code == 401
    assert res.get_json()['error'] in {'unauthorized', 'invalid_token'}


def test_employee_cannot_escalate_role(client):
    login = client.post('/auth/login', json={
        'email': 'employee@test.com',
        'password': 'emp123'
    })
    token = login.get_json()['token']

    res = client.post('/users', json={
        'name': 'Hacker',
        'email': 'hacker@example.com',
        'password': 'pw123',
        'role': 'admin'
    }, headers={'Authorization': f'Bearer {token}'})
    assert res.status_code == 403


def test_sql_injection_like_input_is_rejected(client):
    res = client.post('/auth/register', json={
        'name': "admin' OR '1'='1",
        'email': "admin@example.com'; DROP TABLE users; --",
        'password': 'secret123'
    })
    assert res.status_code == 400
