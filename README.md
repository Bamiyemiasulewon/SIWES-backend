# Smart IT Helpdesk Backend

A Flask-based backend API for a Smart IT Helpdesk system using PostgreSQL, SQLAlchemy, JWT authentication, and role-based access control.

## Stack

- Python 3.11+
- Flask
- SQLAlchemy ORM
- Flask-Migrate
- PostgreSQL
- Flask-JWT-Extended
- Marshmallow
- python-dotenv

## Project structure

- app/
  - models/
  - routes/
  - schemas/
  - services/
  - utils/
- config.py
- .env.example
- requirements.txt
- run.py
- seed.py
- migrations/

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

   Update the PostgreSQL connection string if needed.

4. Initialize the database and migrations:

   ```bash
   flask --app run.py db init
   flask --app run.py db migrate -m "Initial migration"
   flask --app run.py db upgrade
   ```

5. Seed sample data:

   ```bash
   python seed.py
   ```

6. Run the application:

   ```bash
   flask --app run.py run
   ```

   Or:

   ```bash
   python run.py
   ```

## Authentication

The API uses JWT bearer tokens.

### Register

```http
POST /auth/register
```

### Login

```http
POST /auth/login
```

### Profile

```http
GET /auth/me
```

## Role-based access

- Admin: full access
- Technician: manage assigned tickets and assets
- Employee: create and view their own tickets

## Core endpoints

- Auth: `/auth/register`, `/auth/login`, `/auth/me`
- Users: `/users`
- Departments: `/departments`
- Assets: `/assets`
- Tickets: `/tickets`
- Dashboard: `/dashboard/technician`, `/dashboard/executive`, `/dashboard/assets`

## Notes

- Pagination is supported on list endpoints using `page` and `per_page` query params.
- Error responses follow a consistent JSON format.
- Input validation is enforced on write requests.

## Production notes

- Change the JWT secret and database credentials in `.env` before deployment.
- Use a managed PostgreSQL host for production.
- Consider enabling HTTPS and secure secret storage in deployment.
