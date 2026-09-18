# Whoosh FastAPI Backend

Database foundation for the Whoosh Employee Seat Availability system. This phase contains the FastAPI app shell, environment configuration, SQLAlchemy/MySQL engine setup, Alembic, the ERD models, CORS, and a health endpoint.

## Requirements

- Python 3.11+
- MySQL 8+
- A virtual environment is recommended

Python 3.14 is also supported by the current dependency set.

## Local setup

From the `backend/` directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` with the real MySQL connection string and allowed frontend origins. The default database URL uses the PyMySQL SQLAlchemy driver:

```text
mysql+pymysql://USER:PASSWORD@HOST:3306/DATABASE
```

## Database initialization

Create the MySQL database before running the migration. For example, from the XAMPP MySQL client:

```powershell
C:\xampp\mysql\bin\mysql.exe -u root -e "CREATE DATABASE IF NOT EXISTS booking_seat CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

Then apply the initial schema from `backend/`:

```powershell
alembic upgrade head
```

Inspect the migration state with:

```powershell
alembic current
alembic history
```

The schema contains roles, users, departments, employees, trains, carriages, seats, manifests, manifest passengers, employee bookings, booking history, and system logs. Carriage seat letters are stored as JSON configuration, so the database is not limited to `A B C D F`.

## Run FastAPI

From `backend/` with the virtual environment active:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API documentation is available at:

- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/redoc

Health check:

```text
GET http://127.0.0.1:8000/api/v1/health
```

Example response:

```json
{
  "status": "ok",
  "service": "Whoosh Employee Seat Availability API",
  "version": "0.1.0",
  "database": {
    "configured": true,
    "driver": "mysql+pymysql",
    "connection_checked": false
  }
}
```

The health endpoint performs a lightweight `SELECT 1` connection check and reports `connected: true` or the database driver error class. FastAPI remains available when MySQL is offline.

## Scope boundary

## Authentication

Authentication uses OAuth2 password form login with JWT bearer access tokens. Passwords are hashed with Argon2 through `pwdlib`; plaintext passwords are never stored. Set these values in `.env` before starting authentication:

```text
JWT_SECRET_KEY=use-a-long-random-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Start the development role/admin seed after the database migration:

```powershell
$env:DATABASE_URL = "mysql+pymysql://root@127.0.0.1:3306/booking_seat"
$env:JWT_SECRET_KEY = "local-development-secret"
$env:SEED_ADMIN_EMAIL = "admin@example.com"
$env:SEED_ADMIN_PASSWORD = "use-a-local-password"
python -m scripts.seed_auth
```

The seed creates these roles: `Admin`, `Operator`, `Manager`, and `Employee`. It creates one Admin user using only environment values and never hardcodes a production password.

Login uses form fields `username` (email) and `password`:

```powershell
curl.exe -X POST http://127.0.0.1:8000/api/v1/auth/login -H "Content-Type: application/x-www-form-urlencoded" -d "username=admin@example.com&password=use-a-local-password"
```

Use the returned access token as:

```text
Authorization: Bearer <access_token>
```

Protected endpoints in this phase:

```text
GET /api/v1/auth/me
GET /api/v1/auth/admin-check
```

`admin-check` is a small authorization probe for testing role protection; it is not a CMS API. Roles are loaded from the database for every authenticated request. The backend never trusts a role or employee ID from the frontend.

Run auth tests from `backend/`:

```powershell
pytest -q
```

This phase intentionally does not include CMS screens, Excel import, employee APIs, or booking logic. Employee booking concurrency will use row locks and the `active_booking_key` structure in a later phase.

## Phase 4 master data APIs

The backend now exposes role-protected master-data endpoints. Admin and Operator can mutate data; Admin, Operator, and Manager can view it; Employee cannot access these CMS master-data endpoints.

```text
GET    /api/v1/trains
POST   /api/v1/trains
GET    /api/v1/trains/{id}
PUT    /api/v1/trains/{id}
PATCH  /api/v1/trains/{id}/status

GET    /api/v1/trains/{train_id}/carriages
POST   /api/v1/trains/{train_id}/carriages
GET    /api/v1/carriages/{id}
PUT    /api/v1/carriages/{id}
PATCH  /api/v1/carriages/{id}/status

GET    /api/v1/carriages/{carriage_id}/seats
POST   /api/v1/carriages/{carriage_id}/seats/generate
PATCH  /api/v1/seats/{seat_id}
```

Carriage seat generation uses the stored `total_rows` and JSON `seat_config`; the generator does not contain a fixed A/B/C/D/F list. For example:

```json
{
  "carriage_number": "08",
  "class_type": "Premium Economy",
  "total_rows": 8,
  "seat_config": ["A", "C", "D", "F"]
}
```

This generates 32 seats. A second generation attempt is rejected to prevent duplicate seats. Every train, carriage, status change, seat update, and generation action writes a `system_logs` record.

The Phase 4 migration is `20260917_0002_train_identity`, which adds a unique `(train_number, travel_date)` constraint. Excel import, CMS screens, employee APIs, and booking logic remain out of scope.
