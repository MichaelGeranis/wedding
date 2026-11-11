# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Wedding Planner application with FastAPI backend, React frontend, and PostgreSQL database. The application handles wedding invitations, RSVP submissions, and guest management with admin authentication.

## Development Commands

### Setup & Installation
```bash
make install              # Install all dependencies (backend + frontend)
make install-backend      # Install backend only (uses UV)
make install-frontend     # Install frontend only (uses npm)

# Generate secrets for .env
cd backend
uv run python scripts/generate_secrets.py  # Interactive - prompts for admin password
```

### Running Services
```bash
# Everything, with public demo settings (docker/demo.env; backend/.env overrides it)
docker compose up --build   # admin / demo-admin at http://localhost:3000/admin

# Start PostgreSQL database
docker-compose up -d postgres

# Run backend (development mode with auto-reload)
make dev-backend          # Runs on http://localhost:8000

# Run frontend (separate terminal)
make dev-frontend         # Runs on http://localhost:5173
```

### Testing
```bash
# Backend tests (from backend/ directory)
uv run pytest tests/                              # All tests
uv run pytest tests/unit/                         # Unit tests only
uv run pytest tests/integration/                  # Integration tests only
uv run pytest tests/unit/test_services/ -v        # Specific directory with verbose
uv run pytest tests/integration/test_api/test_rsvp_routes.py::test_submit_rsvp_success -v  # Single test
```

### Linting & Formatting
```bash
make lint-backend         # Runs ruff import sorting, ruff check --fix, ruff format, mypy
make lint-frontend        # Runs npm lint
```

### Database Migrations
```bash
# From backend/ directory
uv run alembic upgrade head                       # Apply all pending migrations
uv run alembic revision --autogenerate -m "msg"   # Create new migration after model changes
uv run alembic downgrade -1                       # Rollback one migration
uv run alembic current                            # Show current revision
uv run alembic history                            # Show migration history
```

See `backend/alembic/README_MIGRATIONS.md` for detailed migration workflow.

## Architecture

### Backend Structure (3-Layer Architecture)

```
Routes (API Layer)
    ↓ Depends(get_db) → provides AsyncSession
Services (Business Logic)
    ↓ receives db session, creates repositories
Repositories (Data Access)
    ↓ receives db session, executes queries
Database (PostgreSQL)
```

**CRITICAL: Transaction Management**
- `get_db()` dependency handles ALL transaction lifecycle (commit/rollback)
- Repositories MUST NOT call `session.commit()` or `session.rollback()`
- Repositories should use `session.flush()` to persist changes within the transaction
- Repositories should just `raise` exceptions without catching them
- Services coordinate multiple repository operations within a single transaction

### Key Components

**Database Session (`utils/database.py`)**
- `get_db()` is a FastAPI dependency that provides AsyncSession
- Automatically commits on success, rolls back on exceptions
- Used via `Depends(get_db)` in route handlers

**Models**
- `models/database.py` - SQLAlchemy ORM models (Invitation, RSVP)
- `models/*.py` - Pydantic models for request/response validation

**Repositories (`repositories/*_pg.py`)**
- Accept `AsyncSession` in `__init__`
- Use async SQLAlchemy with `select()`, `execute()`, `scalars()`
- MUST use `flush()` instead of `commit()`
- Let exceptions propagate (no rollback calls)

**Services (`services/*.py`)**
- Accept database session from routes
- Create repository instances
- Implement business logic
- Coordinate multi-repository operations

**Routes (`api/routes/*.py`)**
- Use `Depends(get_db)` to get database session
- Create service instances with the session
- Handle HTTP-specific concerns (status codes, exceptions)
- Apply rate limiting with `@limiter.limit()`

### Rate Limiting
- Applied at route level using `slowapi`
- Configured via environment variables (RATE_LIMIT_RSVP, RATE_LIMIT_ADMIN_LOGIN)
- Pattern: `@limiter.limit(settings.rate_limit_rsvp)` on route function

### Authentication
- JWT tokens for admin authentication
- Password hashing with bcrypt
- `utils/security.py` contains create_access_token, verify_password, etc.
- Admin routes require Bearer token authentication

### QR Code System for Invited Guests

**Overview:**
Each invited guest receives a unique secure token that can be encoded in a QR code. When scanned, the QR code opens the RSVP form with the guest's information pre-filled.

**Backend Components:**
- `models/database.py` - `InvitedGuest.token` field (64-char unique string)
- `utils/qr_code.py` - `generate_guest_qr_code()` function using `qrcode` library
- `repositories/invited_guest_repository_pg.py` - Auto-generates tokens using `secrets.token_urlsafe(32)`
- API Endpoints:
  - `GET /api/admin/invited-guests/{id}/qr-code` - Downloads QR code PNG (admin only)
  - `GET /api/rsvp/guest-info?token={token}` - Validates token and returns guest info (public)

**Frontend Components:**
- `InvitedGuestsTable.jsx` - QR code download button for each guest
- `RSVPForm.jsx` - Detects `?token=xxx` URL parameter and pre-fills name/phone
- `services/api.js` - `downloadQRCode()` and `getGuestInfoByToken()` functions

**Workflow:**
1. Admin clicks QR code button → Downloads `qr_code_Guest_Name.png`
2. Guest scans QR code → Opens `{frontend_url}/rsvp?token={token}`
3. Form automatically validates token and pre-fills guest information
4. Guest completes and submits RSVP

**Security:**
- Tokens are generated with 256 bits of entropy using `secrets.token_urlsafe()`
- Tokens are unique per guest and indexed in the database
- Token validation is rate-limited via the RSVP endpoint rate limit

### Invited Guest Statistics

**Overview:**
The system calculates total invited guests by counting base guests plus children and plus-ones mentioned in the notes field.

**Formula:** `total_invited = base_guests + children + plus_ones`

**Tag System:**
- `#child` - Marks a child in the notes field (case-insensitive)
- `#plusone` - Marks a plus-one in the notes field (case-insensitive)
- Uses word boundary matching (`\b`) to avoid partial matches (e.g., "childhood" won't match)

**Example:**
- Guest: "John Doe" with notes "Bringing wife and #child #child"
- Counts as: 1 base guest + 2 children = 3 total invited for this entry

**API Endpoint:**
- `GET /api/admin/invited-guests/stats` - Returns statistics breakdown

**Response:**
```json
{
  "total_invited_base": 50,
  "total_children": 12,
  "total_plus_ones": 8,
  "total_invited": 70
}
```

## Database Schema

**Tables:**
- `invitations` - Wedding invitation configuration (single row with id=1)
- `invited_guests` - Pre-approved guest list with unique tokens for QR codes
- `rsvps` - Guest RSVP responses with confirmation numbers
- `users` - Admin users for authentication

**Models are in:** `backend/src/wedding_api/models/database.py`

After model changes:
1. Edit `models/database.py`
2. Generate migration: `uv run alembic revision --autogenerate -m "description"`
3. Review generated migration in `alembic/versions/`
4. **IMPORTANT**: Check for NULL constraint issues - if making existing columns NOT NULL, update NULL values first
5. Apply: `uv run alembic upgrade head`

### Migration Best Practices

When adding NOT NULL constraints to existing columns:
```python
# Update NULL values first
op.execute("UPDATE table_name SET column_name = default_value WHERE column_name IS NULL")
# Then make column NOT NULL
op.alter_column('table_name', 'column_name', nullable=False)
```

When adding boolean columns with defaults:
```python
# Use 'false' not 'false()' for PostgreSQL
op.add_column('table', sa.Column('field', sa.Boolean(), server_default=sa.text('false'), nullable=False))
```

## Environment Configuration

The application uses **pydantic-settings** for configuration management. All settings are loaded from environment variables and the `.env` file.

### Configuration Priority (highest to lowest):
1. Environment variables (e.g., `export FRONTEND_URL=...`)
2. `.env` file variables
3. Default values in code (if any)

### Required Settings

**MUST be set explicitly** (no defaults):
- `ENVIRONMENT` - development/staging/production
- `DATABASE_URL` - PostgreSQL connection string
- `FRONTEND_URL` - Frontend URL for QR codes (e.g., http://localhost:3000)
- `CORS_ORIGINS` - Comma-separated list of allowed origins
- `JWT_SECRET_KEY` - Secret for JWT token generation (min 32 chars)
- `ADMIN_PASSWORD_HASH` - Bcrypt hash of admin password
- `RATE_LIMIT_RSVP` - Rate limit for RSVP endpoint (e.g., "10/day")
- `RATE_LIMIT_ADMIN_LOGIN` - Rate limit for admin login (e.g., "5/minute")

### Optional Settings (with sensible defaults):
- `API_PORT` - API server port (default: 8000)
- `LOG_LEVEL` - Logging level (default: INFO)
- `JWT_ALGORITHM` - JWT algorithm (default: HS256)
- `JWT_EXPIRATION_MINUTES` - Token expiration (default: 60)
- `EMAIL_ENABLED` - Enable email notifications (default: false)
- `REQUIRE_INVITED_GUEST_VALIDATION` - Validate phone numbers (default: false)

### Setup Instructions

**1. Copy the example file:**
```bash
cd backend
cp .env.example .env
```

**2. Generate secrets:**
```bash
cd backend
uv run python scripts/generate_secrets.py
```

This will prompt for admin password and generate:
- `JWT_SECRET_KEY` (64-char hex string)
- `ADMIN_PASSWORD_HASH` (bcrypt hash)

**3. Edit `.env` with your values:**
```bash
# Required settings
ENVIRONMENT=development
DATABASE_URL=postgresql+asyncpg://wedding:wedding@localhost:5432/wedding
FRONTEND_URL=http://localhost:3000
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
JWT_SECRET_KEY=<paste-from-generate_secrets>
ADMIN_PASSWORD_HASH=<paste-from-generate_secrets>
RATE_LIMIT_RSVP=10/day
RATE_LIMIT_ADMIN_LOGIN=5/minute

# Optional features
REQUIRE_INVITED_GUEST_VALIDATION=false
```

**4. Verify configuration:**
```bash
# Via Python
cd backend
uv run python -c "from wedding_api.config import settings; print(f'Environment: {settings.environment}'); print(f'Frontend URL: {settings.frontend_url}')"

# Via API (after starting backend)
curl http://localhost:8000/api/config/public
```

### Configuration by Environment

**Development (Vite):**
```bash
ENVIRONMENT=development
FRONTEND_URL=http://localhost:5173
CORS_ORIGINS=http://localhost:5173
```

**Development (Docker):**
```bash
ENVIRONMENT=development
FRONTEND_URL=http://localhost:3000
CORS_ORIGINS=http://localhost:3000
```

**Production:**
```bash
ENVIRONMENT=production
FRONTEND_URL=https://wedding.yourdomain.com
CORS_ORIGINS=https://wedding.yourdomain.com
RATE_LIMIT_RSVP=5/day
EMAIL_ENABLED=true
```

## Common Patterns

### Adding a New Endpoint

1. **Define Pydantic models** in `models/` for request/response
2. **Add repository method** in `repositories/` (if new data access needed)
3. **Add service method** in `services/` for business logic
4. **Add route** in `api/routes/` that uses `Depends(get_db)`
5. **Write tests** in `tests/unit/` and `tests/integration/`

### Testing Pattern
- Unit tests use in-memory SQLite (`aiosqlite`)
- Integration tests use the actual test database
- Fixtures provide database sessions and test data
- Always test both success and error cases

## Important Notes

- **Python 3.13** is used - avoid deprecated `datetime.utcnow()`, use `datetime.now(timezone.utc)`
- **Async/await everywhere** - all database operations are async
- **UV for package management** - faster than pip, use `uv run` to execute commands
- **Type hints required** - mypy is configured with `disallow_untyped_defs = true`
- **Line length: 160** - configured in ruff
- **Server-side defaults** - Use `server_default=func.now()` for timestamps in models

## Docker

Full stack can be run with:
```bash
docker-compose up -d  # Starts postgres, backend, frontend
```

Services:
- `postgres` - PostgreSQL 16 on port 5432
- `backend` - FastAPI on port 8000
- `frontend` - React app on port 3000
- `init-db` - Runs Alembic migrations on startup

## Frontend

React 18 with Vite, located in `frontend/`:
- Uses Axios for API calls
- AuthContext for authentication state
- React Router for routing
- Pages: Invitation, RSVP Form, Admin Panel

Frontend development server runs on port 5173, connects to backend on port 8000.
