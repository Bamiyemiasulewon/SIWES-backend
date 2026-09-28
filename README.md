# Smart Campus Service Desk Backend

This backend supports the School of Computing service desk workflow for students and staff. It handles maintenance requests, complaints, department-based complaint routing, anonymous complaint submission, identity reveal logging, officer assignment, and dashboard analytics. The project retains the original Flask structure while adapting the legacy ticketing logic to the new campus service domain.

## Stack

- Python 3.11+
- Flask 3.0
- Flask-SQLAlchemy
- Flask-Migrate
- Flask-JWT-Extended
- Flask-Marshmallow
- flask-smorest
- PostgreSQL
- Pytest

## Project structure

- app/
  - models/
  - routes/
  - schemas/
  - services/
  - utils/
- config.py
- requirements.txt
- run.py
- seed.py
- tests/

## Setup

1. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:

   ```bash
   cp .env.example .env
   ```

   Update the PostgreSQL connection string and JWT secrets if needed.

4. Initialize the database and migrations:

   ```bash
   flask --app run.py db init
   flask --app run.py db migrate -m "Initial migration"
   flask --app run.py db upgrade
   ```

5. Seed sample data for manual testing:

   ```bash
   python seed.py
   ```

6. Run the application:

   ```bash
   python run.py
   ```

   or:

   ```bash
   flask --app run.py run
   ```

## Authentication

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`

Students can register with their matriculation number, level, and department. Roles are enforced server-side and cannot be escalated by the client.

## Role model

- Student: create and monitor their own requests
- Staff: create and monitor their own requests, with restrictions on maintenance submissions
- Maintenance officer: view and resolve maintenance requests assigned to them
- Complaint officer: manage complaint requests by scope (department, bursary, or general)
- Admin: full system access to users, departments, assets, complaints, and audits

## Main API routes

- Users: `/users`
- Departments: `/departments`
- Assets: `/assets`
- Requests: `/requests`
- Legacy compatibility: `/tickets`
- Request status: `/requests/<id>/status`
- Request assignment: `/requests/<id>/assign`
- Request history: `/requests/<id>/history`
- Flagging: `/requests/<id>/flag`, `/requests/<id>/unflag`
- Identity reveal logs: `/requests/<id>/reveal-identity`, `/requests/identity-reveals`
- Dashboard: `/dashboard/student`, `/dashboard/officer`, `/dashboard/admin`, `/dashboard/assets`

## Business rules

- Maintenance requests require a building and room.
- Electrical maintenance requests require high or critical priority.
- Students and staff can only edit requests still in the `submitted` state.
- Requests move through a strict lifecycle: `submitted -> assigned -> in_progress -> resolved -> reopened -> in_progress -> resolved -> closed`.
- Anonymous complaints hide the creator from non-admin viewers.
- Admin approval is required to reveal an anonymous complaint’s identity.
- Officer scopes control complaint visibility and routing.

## Filtering and pagination

List endpoints support filters such as:

- `?status=`
- `?priority=`
- `?department_id=`
- `?assigned_to=`
- `?is_flagged=`
- `?page=`
- `?per_page=`

## Swagger/OpenAPI docs

OpenAPI docs are available at:

- `/docs/swagger-ui`
- `/docs/redoc`
- `/docs/openapi.json`

## Testing

Run the test suite with:

```bash
pytest -q
```

The current suite covers authentication, authorization, JWT validation, role escape prevention, and malicious input handling.

## Notes

- All write operations use Marshmallow validation.
- Request lifecycle changes are recorded in `RequestHistory`.
- Flagging and identity reveal actions are audited for admin review.
- Error responses follow a consistent JSON format with `status_code`, `message`, and `error` fields.
