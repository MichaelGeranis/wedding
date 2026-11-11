.PHONY: help install install-backend install-frontend build-backend build-frontend \
		dev-backend dev-frontend lint-backend lint-frontend \
		docker-compose-up docker-compose-down db-create db-init db-downgrade clean test e2e-test test-clean restart-frontend

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'


# Install
install: install-backend install-frontend ## Install all dependencies

install-backend: ## Install backend dependencies with UV
	cd backend && uv sync --all-extras

install-frontend: ## Install frontend dependencies
	cd frontend && npm install


# Build
build-backend: ## Build backend (prepare for production)
	cd backend && uv sync --frozen --no-dev

build-frontend: ## Build frontend for production
	cd frontend && npm run build

restart-frontend: ## Restore frontend dependencies
	cd frontend && docker-compose build frontend && docker-compose up -d --no-deps frontend

# Run
dev-backend: ## Run backend development server
	cd backend && uv run uvicorn wedding_api.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Run frontend development server
	cd frontend && npm run dev


# Lint and format
lint-backend: ## Lint backend code
	cd backend && uv run ruff check --select I --fix src tests scripts
	cd backend && uv run ruff check src tests --fix
	cd backend && uv run ruff format src tests
	cd backend && uv run mypy src

lint-frontend: ## Lint frontend code
	cd frontend && npm run lint


# Docker
docker-compose-up: ## Start all services with docker-compose
	docker-compose up -d --build

docker-compose-down: ## Stop all docker-compose services
	docker-compose down

db-create: ## Create the database
	cd backend && uv run alembic revision --autogenerate -m "Create initial database schema"
	cd backend && uv run alembic upgrade head

db-init: ## Apply all pending migrations to the database
	cd backend && uv run alembic upgrade head

db-downgrade: ## Downgrade the database by one migration
	cd backend && uv run alembic downgrade -1


# Clean cache
clean: ## Clean build artifacts and caches
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/.coverage
	rm -rf backend/htmlcov
	rm -rf frontend/dist
	rm -rf frontend/node_modules/.cache

# Tests
test: ## Run all tests
	cd backend && uv run pytest tests

e2e-test: ## Run end-to-end tests
	cd frontend && VITE_API_BASE_URL=http://localhost:8000 npm run test:e2e && VITE_API_BASE_URL=http://localhost:8000 npm run test:e2e:rsvp
	&& make test-clean

test-clean: ## Clean test data created during end-to-end tests
	cd frontend && VITE_API_BASE_URL=http://localhost:8000 E2E_ADMIN_PASSWORD='demo-admin' node test/e2e/cleanup_e2e.js
