# Contributing

Thanks for your interest. This guide covers setup, the rules the codebase
follows, and how to get a change merged.

By participating you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
To report a security problem, follow [SECURITY.md](SECURITY.md) instead of
opening a public issue.

## Before you start

- **Bugs and small fixes:** open a pull request directly, or an issue first if
  you are unsure it is a bug.
- **Features and larger changes:** open an issue to discuss the approach first.

## Development setup

Follow [Development in the README](README.md#development). The backend tests use
in-memory SQLite and need no database or email server. More detail on tests,
migrations and configuration is in [docs/development.md](docs/development.md).

## Rules the codebase follows

- **Layers:** routes handle HTTP, services hold the business rules, repositories
  do data access.
- **Transactions:** `get_db()` commits or rolls back each request.
  Repositories call `flush()`, never `commit()` or `rollback()`, and let
  exceptions propagate.
- **Async everywhere**, type hints on every function, line length 160.
- **Model changes need a migration:** `uv run alembic revision --autogenerate -m "..."`,
  then review the generated file.
- **Every user-facing string** goes in both `frontend/src/i18n/locales/en.json`
  and `el.json`.

## Making a change

1. Fork the repository and create a branch from `main`
   (`feat/short-description`, `fix/short-description`, `docs/topic`).
2. Make the change, with tests for backend behaviour (success and error cases).
3. Run the checks:
   ```bash
   make test
   make lint-backend
   make lint-frontend
   cd frontend && npm test && npm run build
   ```
4. Commit using [Conventional Commits](https://www.conventionalcommits.org/)
   (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).
5. Add a line under `Unreleased` in [CHANGELOG.md](CHANGELOG.md) for any
   user-visible change.
6. Open a pull request against `main` and fill in the template.

Pull requests are squash-merged to keep `main` linear.

## Licence

By contributing, you agree that your contributions are licensed under the
[Apache License 2.0](LICENSE).
