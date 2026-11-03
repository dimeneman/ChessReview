# Contributing to ChessReview

Thank you for your interest in contributing to **ChessReview**! Whether you are fixing a bug, adding new chess engine heuristics, optimizing Docker containers, or improving documentation, your contributions are warmly welcomed.

---

## Code of Conduct

All contributors and participants are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md). Please treat everyone with respect, kindness, and constructive feedback.

---

## Development Workflow

### 1. Prerequisites
Ensure you have the following installed on your machine:
* **Python 3.12+**
* **Node.js 20+** and **npm**
* **Stockfish 16+** ([Download Stockfish](https://stockfishchess.org/download/))
* **Docker & Docker Compose** (optional, recommended for full-stack preview)
* **Make**

### 2. Fork and Clone
```bash
git clone https://github.com/YOUR_USERNAME/ChessReview.git
cd ChessReview
```

### 3. Setup Local Environment
```bash
# Create and populate environment variables
cp .env.example .env

# Install backend and frontend dependencies
make install

# Configure pre-commit hooks
pre-commit install
```

### 4. Running Locally
Run the backend and frontend in separate terminals:

```bash
# Terminal 1: Backend (http://localhost:8000)
make backend

# Terminal 2: Frontend (http://localhost:5173)
make frontend
```

Or run everything inside Docker:
```bash
make up
make logs
```

---

## Branching & Commit Conventions

### Branch Naming
* `feat/short-description`: New feature or engine improvement
* `fix/short-description`: Bug fix or patch
* `docs/short-description`: Documentation updates
* `refactor/short-description`: Code restructuring without behavioral change
* `ci/short-description`: GitHub Actions or infrastructure changes

### Conventional Commits
Please structure your commit messages following the [Conventional Commits](https://www.conventionalcommits.org/) specification:
```
<type>(<scope>): <subject>

# Examples:
feat(engine): add multi-pv candidate line evaluation
fix(api): correct centipawn loss sign handling for black moves
docs(readme): add docker compose quick start instructions
test(accuracy): add edge cases for mate-in-1 accuracy curves
```

---

## Quality Standards

Before submitting a Pull Request, ensure that all linting, formatting, and automated tests pass:

```bash
# Run automated test suite
make test

# Check code formatting and style
make lint

# Auto-format files
make format
```

---

## Submitting a Pull Request

1. Push your branch to your GitHub fork:
   ```bash
   git push origin feat/your-feature-name
   ```
2. Open a Pull Request against the `main` branch of the upstream repository.
3. Complete the [Pull Request Template](.github/PULL_REQUEST_TEMPLATE.md) checklist.
4. Ensure all CI workflow checks pass (Linting, Tests, Frontend build, Docker Compose validation).
5. A maintainer will review your code and provide feedback.

