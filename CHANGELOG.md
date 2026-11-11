# Changelog

All notable changes are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- `docker compose up --build` works with no setup, using the public demo
  values in `docker/demo.env` and a sample couple. `backend/.env` overrides them.
- The admin user is created from `ADMIN_PASSWORD_HASH` on first start.
- The API refuses to start outside development with the demo JWT secret.
- Apache 2.0 licence, contributing guide, security policy, code of conduct,
  issue and pull request templates, CI and Dependabot.

### Changed

- Sample invitation data replaces real names, dates and venues.
- Confirmation emails are signed "The happy couple"; the page footer shows the
  couple's names.
- Ports are bound to `127.0.0.1` in `docker-compose.yml`.

### Fixed

- The frontend builds from a fresh clone: `frontend/src/lib/` was ignored by a
  `lib/` rule in `.gitignore` and had never been committed.
- `backend/.env.example` is back; the README told you to copy it.
- `npm run lint` has an ESLint configuration.
- Five backend tests that no longer matched the code.

### Removed

- `backend/scripts/seed_admin.py`, which created an `admin` / `admin123` user.
