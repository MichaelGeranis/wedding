# Development guide

Details that the [README](../README.md) leaves out: tests, migrations, configuration and troubleshooting.

## Testing

### Backend Testing

The backend uses **pytest** with async support. Tests are organized into unit and integration tests.

**Run all tests:**
```bash
cd backend
uv run pytest tests/
```

**Run specific test types:**
```bash
# Unit tests only (fast, use in-memory SQLite)
uv run pytest tests/unit/

# Integration tests only (slower, use test database)
uv run pytest tests/integration/

# Tests with verbose output
uv run pytest tests/ -v

# Tests with coverage report
uv run pytest tests/ --cov=wedding_api --cov-report=html
```

**Run specific test files or functions:**
```bash
# Single test file
uv run pytest tests/unit/test_services/test_rsvp_service.py -v

# Single test function
uv run pytest tests/integration/test_api/test_rsvp_routes.py::test_submit_rsvp_success -v

# Tests matching a pattern
uv run pytest tests/ -k "rsvp" -v
```

**Test Configuration:**
- Unit tests use in-memory SQLite (`aiosqlite`) for speed
- Integration tests can use a test PostgreSQL database
- Fixtures provide database sessions and test data
- See `tests/conftest.py` for shared fixtures

### Frontend checks

CI lints the frontend, runs its unit tests and builds it:

```bash
cd frontend
npm run lint
npm test          # Vitest, e.g. src/lib/validationSchemas.test.js
npm run build
```

Unit tests sit next to the code they test as `*.test.js` files.

End-to-end scripts that drive a running stack are in
[`frontend/test/e2e/`](../frontend/test/e2e/README.md).

### Linting and Code Quality

**Backend:**
```bash
make lint-backend
```

This runs:
- `ruff check --select I --fix` - Import sorting
- `ruff check --fix` - Linting with auto-fix
- `ruff format` - Code formatting
- `mypy` - Type checking (CI runs it too)

**Frontend:**
```bash
make lint-frontend
```

This runs ESLint (flat config in `frontend/eslint.config.js`) on the frontend code.

## Database Migrations

### Understanding Migrations

This project uses **Alembic** for database schema versioning. Migrations are stored in `backend/alembic/versions/`.

### Common Migration Commands

**Apply pending migrations:**
```bash
cd backend
uv run alembic upgrade head
```

**Create a new migration (after model changes):**
```bash
cd backend
uv run alembic revision --autogenerate -m "description of changes"
```

**Review the migration:**
- Check the generated file in `alembic/versions/`
- Verify the `upgrade()` and `downgrade()` functions
- Test the migration on a development database

**Rollback one migration:**
```bash
uv run alembic downgrade -1
```

**Check current migration version:**
```bash
uv run alembic current
```

**View migration history:**
```bash
uv run alembic history
```

### Migration Workflow

1. **Modify models** in `backend/src/wedding_api/models/database.py`
2. **Generate migration:**
   ```bash
   uv run alembic revision --autogenerate -m "add user avatar field"
   ```
3. **Review generated migration** in `alembic/versions/`
4. **Test migration:**
   ```bash
   uv run alembic upgrade head
   ```
5. **Verify database state:**
   ```bash
   uv run alembic current
   ```
6. **Run tests:**
   ```bash
   uv run pytest tests/
   ```

### Migration Best Practices

⚠️ **Important:** When adding NOT NULL constraints to existing columns:

```python
# BAD - Will fail if existing rows have NULL values
op.alter_column('table', 'column', nullable=False)

# GOOD - Update NULL values first
op.execute("UPDATE table SET column = 'default' WHERE column IS NULL")
op.alter_column('table', 'column', nullable=False)
```

For more details, see `backend/alembic/README_MIGRATIONS.md`.

### Architecture Overview

The backend follows a **3-layer architecture**:

```
Routes (API Layer)
    ↓ Depends(get_db) → provides AsyncSession
Services (Business Logic)
    ↓ receives db session, creates repositories
Repositories (Data Access)
    ↓ receives db session, executes queries
Database (PostgreSQL)
```

**Key Principles:**
- Routes handle HTTP concerns (status codes, request/response)
- Services implement business logic and coordinate operations
- Repositories handle database queries
- `get_db()` dependency manages transaction lifecycle
- Repositories use `flush()`, NOT `commit()` or `rollback()`

## Troubleshooting

### Common Issues

#### Database Connection Errors

**Problem:** `connection refused` or `could not connect to server`

**Solution:**
```bash
# Check if PostgreSQL is running
docker-compose ps

# Start PostgreSQL if it's not running
docker-compose up -d postgres

# Check logs
docker-compose logs postgres
```

#### Migration Errors

**Problem:** `Target database is not up to date`

**Solution:**
```bash
cd backend
uv run alembic upgrade head
```

**Problem:** `Can't locate revision identified by 'xxxxx'`

**Solution:**
```bash
# Check current revision
uv run alembic current

# View migration history
uv run alembic history

# If database is out of sync, you may need to stamp it
uv run alembic stamp head
```

#### Port Already in Use

**Problem:** `Address already in use` when starting servers

**Solution:**
```bash
# Find process using the port
lsof -i :8000  # Backend
lsof -i :5173  # Frontend

# Kill the process
kill -9 <PID>

# Or use different ports
# Backend: Edit .env and set API_PORT=8001
# Frontend: npm run dev -- --port 5174
```

#### Import Errors

**Problem:** `ModuleNotFoundError` or import errors

**Solution:**
```bash
# Reinstall backend dependencies
cd backend
uv sync

# Reinstall frontend dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install
```

#### Authentication Issues

**Problem:** Cannot login to admin panel

**Solution:**
```bash
# Generate a new hash
cd backend
uv run python scripts/generate_secrets.py
```

The `admin` user is created from `ADMIN_PASSWORD_HASH` only when the database
has no users. To change the password later, update the stored hash:

```sql
UPDATE users
SET password_hash = '<new hash>'
WHERE username = 'admin';
```

#### CORS Errors

**Problem:** Browser shows CORS errors when accessing API

**Solution:**
```bash
# Check .env file has correct CORS_ORIGINS
# Example for development:
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Restart backend after changing .env
```

#### QR Code Generation Fails

**Problem:** QR code download returns 500 error

**Solution:**
```bash
# Ensure FRONTEND_URL is set correctly in .env
FRONTEND_URL=http://localhost:5173

# Check backend logs for specific error
docker-compose logs backend
```

### Clean Installation

If all else fails, try a clean installation:

```bash
# Stop all services
docker-compose down -v

# Clean backend
cd backend
rm -rf .venv __pycache__ .pytest_cache
uv sync

# Clean frontend
cd ../frontend
rm -rf node_modules .vite package-lock.json
npm install

# Start fresh
cd ..
docker-compose up -d postgres
cd backend
uv run alembic upgrade head
cd ..
make dev-backend  # Terminal 1
make dev-frontend # Terminal 2
```

## Environment Variables Reference

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `ENVIRONMENT` | Deployment environment | `development`, `staging`, `production` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://user:pass@localhost:5432/wedding` |
| `FRONTEND_URL` | Frontend URL for QR codes | `http://localhost:5173` |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | `http://localhost:5173,http://localhost:3000` |
| `JWT_SECRET_KEY` | Secret key for JWT tokens (min 32 chars) | Generated by `generate_secrets.py` |
| `ADMIN_PASSWORD_HASH` | Bcrypt hash of admin password | Generated by `generate_secrets.py` |
| `RATE_LIMIT_RSVP` | Rate limit for RSVP submissions | `10/day` |
| `RATE_LIMIT_ADMIN_LOGIN` | Rate limit for admin login | `5/minute` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_PORT` | Backend API port | `8000` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `JWT_EXPIRATION_MINUTES` | JWT token expiration | `60` |
| `EMAIL_ENABLED` | Enable email notifications | `false` |
| `REQUIRE_INVITED_GUEST_VALIDATION` | Validate phone numbers against invited guest list | `false` |

