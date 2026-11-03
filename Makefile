# ==============================================================================
# ChessReview - Developer Automation Makefile
# ==============================================================================
# Self-documenting Makefile for local development, Docker orchestration,
# testing, linting, and quality assurance.
# ==============================================================================

SHELL := /bin/bash
COMPOSE_FILE := infra/docker-compose.yml
PYTHON := python3
PIP := pip

.DEFAULT_GOAL := help

# ------------------------------------------------------------------------------
# Help Target
# ------------------------------------------------------------------------------
.PHONY: help
help: ## Display this help screen with target descriptions
	@echo "========================================================================"
	@echo "                      ChessReview Command Center                        "
	@echo "========================================================================"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo "========================================================================"

# ------------------------------------------------------------------------------
# Docker Orchestration
# ------------------------------------------------------------------------------
.PHONY: build
build: ## Build all Docker container images
	@echo "==> Building Docker images via $(COMPOSE_FILE)..."
	docker compose -f $(COMPOSE_FILE) build

.PHONY: up
up: ## Start application containers in detached mode
	@echo "==> Launching ChessReview containers..."
	docker compose -f $(COMPOSE_FILE) up -d
	@echo "==> Application running:"
	@echo "    - Frontend: http://localhost:3000"
	@echo "    - Backend:  http://localhost:8000"
	@echo "    - API Docs: http://localhost:8000/docs"

.PHONY: down
down: ## Stop and remove active application containers
	@echo "==> Stopping ChessReview containers..."
	docker compose -f $(COMPOSE_FILE) down

.PHONY: restart
restart: ## Restart all Docker containers
	@echo "==> Restarting containers..."
	docker compose -f $(COMPOSE_FILE) restart

.PHONY: logs
logs: ## Stream live output logs from all running containers
	docker compose -f $(COMPOSE_FILE) logs -f

# ------------------------------------------------------------------------------
# Local Development (Without Docker)
# ------------------------------------------------------------------------------
.PHONY: backend
backend: ## Run FastAPI backend locally with hot-reloading
	@echo "==> Starting local FastAPI backend on port 8000..."
	cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

.PHONY: frontend
frontend: ## Run React/Vite frontend locally with hot-reloading
	@echo "==> Starting local Vite frontend development server..."
	cd frontend && npm run dev

.PHONY: install
install: ## Install both backend and frontend dependencies locally
	@echo "==> Installing Python dependencies..."
	$(PIP) install -r requirements-dev.txt
	@echo "==> Installing Node dependencies..."
	cd frontend && npm install

# ------------------------------------------------------------------------------
# Testing & Quality Assurance
# ------------------------------------------------------------------------------
.PHONY: test
test: ## Run unit and integration tests with pytest and coverage
	@echo "==> Executing automated test suite..."
	PYTHONPATH=backend pytest tests -v --tb=short

.PHONY: lint
lint: ## Run Ruff, Black, and Flake8 linters
	@echo "==> Running Ruff linter..."
	ruff check backend tests
	@echo "==> Checking Black formatting..."
	black --check backend tests
	@echo "==> Running Flake8..."
	flake8 backend tests

.PHONY: format
format: ## Automatically format Python codebase with Black and isort
	@echo "==> Formatting code with Black..."
	black backend tests
	@echo "==> Sorting imports with isort..."
	isort backend tests
	@echo "==> Applying Ruff auto-fixes..."
	ruff check --fix backend tests

# ------------------------------------------------------------------------------
# Cleanup
# ------------------------------------------------------------------------------
.PHONY: clean
clean: ## Remove temporary build files, bytecode, caches, and test artifacts
	@echo "==> Cleaning temporary artifacts..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ dist/ build/ *.egg-info
	@echo "==> Clean complete."

