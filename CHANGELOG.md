# Changelog

All notable changes are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Upgrade notes

- The demo database moves from PostgreSQL 16 to 18, which cannot read the old
  data volume (and keeps its data at a new path inside the volume). Recreate it
  with `docker compose down -v` before `docker compose up --build`; this
  deletes the demo data.

### Added

- Vitest unit tests for the RSVP validation schema, run in CI (`npm test`).
- CI type-checks the backend with mypy.
- `docker compose up --build` works with no setup, using the public demo
  values in `docker/demo.env` and a sample couple. `backend/.env` overrides them.
- The admin user is created from `ADMIN_PASSWORD_HASH` on first start.
- The API refuses to start outside development with the demo JWT secret.
- Apache 2.0 licence, contributing guide, security policy, code of conduct,
  issue and pull request templates, CI and Dependabot.

### Changed

- Python 3.14 (from 3.13; 3.15 waits for PyYAML wheels) and the latest version
  of every backend dependency.
- Node 26 LTS, React 19, Vite 8, Tailwind CSS 4, React Router 8, zod 4,
  ESLint 9 (flat config) and the latest version of every other frontend
  dependency.
- PostgreSQL 18 in Docker Compose.
- The backend image installs its dependencies from `pyproject.toml` instead of
  a separate list in the Dockerfile.
- Dependabot groups its updates into one pull request per ecosystem per week,
  and now also watches `docker-compose.yml`.
- Sample invitation data replaces real names, dates and venues.
- Confirmation emails are signed "The happy couple"; the page footer shows the
  couple's names.
- Ports are bound to `127.0.0.1` in `docker-compose.yml`.

### Fixed

- The admin pages no longer set state synchronously inside effects, and ignore
  responses that arrive after the page or filter has changed.
- mypy reports no errors.
- The frontend builds from a fresh clone: `frontend/src/lib/` was ignored by a
  `lib/` rule in `.gitignore` and had never been committed.
- `backend/.env.example` is back; the README told you to copy it.
- `npm run lint` has an ESLint configuration.
- Five backend tests that no longer matched the code.

### Removed

- The unused `passlib` dependency; the backend calls `bcrypt` directly.
- `backend/scripts/seed_admin.py`, which created an `admin` / `admin123` user.
