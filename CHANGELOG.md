# Changelog

All notable changes to the **ChessReview** platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-11-03

### Added
* **Docker Infrastructure:**
  * Multi-stage `backend/Dockerfile` with Debian slim runtime, non-root `appuser`, and native Stockfish package.
  * Multi-stage `frontend/Dockerfile` featuring Alpine Node build stage and Alpine Nginx production server.
  * `infra/docker-compose.yml` orchestrating isolated bridge networking, health check dependencies, and port mapping.
  * Production Nginx server configuration (`frontend/nginx.conf`) with SPA routing, gzip compression, and security headers.
* **Observability & Monitoring:**
  * Added `GET /health` endpoint reporting uptime, API version, environment, engine binary status, and UTC timestamp.
  * Integrated structured Python logging with timestamping, log levels, and request execution time middleware.
* **Developer Experience & Tooling:**
  * Developer `Makefile` featuring `build`, `up`, `down`, `logs`, `backend`, `frontend`, `lint`, `format`, `test`, and `clean`.
  * Multi-linter configuration (`pyproject.toml`, `.flake8`) for Ruff, Black, and isort.
  * Git pre-commit hooks (`.pre-commit-config.yaml`) and cross-editor consistency config (`.editorconfig`).
* **CI/CD Pipeline:**
  * GitHub Actions workflow (`.github/workflows/ci.yml`) covering code quality, pytest unit/integration test coverage, frontend builds, and Docker Compose validation.
* **Automated Testing:**
  * Complete pytest suite (`tests/test_api.py`, `tests/test_review_engine.py`) covering centipawn loss accuracy formulas, move classification thresholds, coach comments, and API error contracts.
* **Open Source Governance:**
  * Added `LICENSE` (MIT), `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, Issue Forms, and Pull Request templates.
* **Comprehensive Documentation:**
  * High-level architectural diagrams, sequence diagrams, deployment topology, and complete REST API documentation.

### Changed
* Refactored `backend/config.py` into a centralized, environment-driven settings module.
* Updated `frontend/src/api.js` to read `VITE_API_URL` dynamically with zero breaking changes to existing deployments.
* Overhauled root `.gitignore` and added `.dockerignore` to eliminate repository bloat.

### Fixed
* Removed committed vendor files (`node_modules`) and Python bytecode (`__pycache__`).
* Fixed permissive CORS policies by binding to configurable origins.

