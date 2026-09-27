# Smart IT Helpdesk Backend

This backend replaces the company’s Excel-based IT ticket workflow with a Flask API for employees, technicians, and administrators. It supports JWT login, role-based access control, asset tracking, ticket assignment, audit history, and Swagger documentation.

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

5. Seed sample data for manual Postman/Swagger testing:

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

JWT bearer tokens are required for protected routes. Passwords are hashed and never returned in API responses.

## Role model

- Employee: create tickets and manage only their own tickets
- Technician: view and update assigned tickets, change ticket status, and assign work
- Admin: full CRUD access across users, departments, assets, and tickets

## Main API routes

- Users: `/users`
- Departments: `/departments`
- Assets: `/assets`
- Tickets: `/tickets`
- Ticket status: `/tickets/<id>/status`
- Ticket assignment: `/tickets/<id>/assign`
- Ticket history: `/tickets/<id>/history`
- Dashboard: `/dashboard/technician`, `/dashboard/executive`, `/dashboard/assets`

## Filtering and pagination

List endpoints support filters such as:

- `?status=`
- `?priority=`
- `?department_id=`
- `?page=`
- `?per_page=`

## Swagger/OpenAPI docs

OpenAPI docs are available at:

- `/docs/swagger-ui`
- `/docs/redoc`
- `/docs/openapi.json`

Use the Swagger UI at `/docs/swagger-ui` for interactive testing with Postman-style request payloads.

## Testing

Run the security and validation test suite with:

```bash
pytest -q tests/test_auth.py
```

The tests cover unauthorized access, JWT expiry and tampering, role escalation prevention, and validation edge cases such as malformed or malicious payloads.

## Notes

- All write operations use Marshmallow validation.
- Ticket status and assignment changes are automatically recorded in `TicketHistory`.
- Error responses follow a consistent JSON format with `status_code`, `message`, and `error` fields.
