# ChessReview Architecture & System Design

This document details the system design, communication protocols, container topology, and execution flows of the **ChessReview** platform.

---

## 1. High-Level System Architecture

The following diagram illustrates the unidirectional data flow from the client browser through the containerized frontend, the FastAPI gateway, the analysis orchestrator, and the native Stockfish UCI process.

```mermaid
flowchart LR
    User(["User (Browser)"]) -->|HTTP / NDJSON| React["React / Vite Frontend\n(Nginx Port 80)"]
    React -->|REST API Calls| FastAPI["FastAPI Gateway\n(Uvicorn Port 8000)"]
    FastAPI -->|Orchestrates| Analyzer["Chess Analyzer\n(review_engine.py)"]
    Analyzer -->|UCI Protocol| Stockfish["Stockfish 16 Engine\n(C++ Subprocess)"]
    Stockfish -->|Centipawns & Lines| Analyzer
    Analyzer -->|Aggregates Accuracy & Graph| FastAPI
    FastAPI -->|Streamed JSON / Payload| React
    React -->|Interactive Board & Graphs| User
```

---

## 2. Sequence Diagram (Game Review Lifecycle)

This sequence diagram depicts the end-to-end lifecycle of an asynchronous streaming game review request.

```mermaid
sequenceDiagram
    autonumber
    actor User as User
    participant Frontend as React (Client)
    participant API as FastAPI Backend
    participant Engine as Review Engine
    participant Stockfish as Stockfish (UCI)

    User->>Frontend: Paste PGN / Import Game
    Frontend->>API: POST /review-stream (text/plain)
    API->>Engine: review_game_stream(pgn, depth)
    Engine->>Stockfish: popen_uci() Spawn Engine Process
    Engine-->>API: Yield {"type": "init", "total_ply": N}
    API-->>Frontend: HTTP 200 Stream Event: init
    Frontend->>Frontend: Render Progress Bar

    loop For Each Move in Mainline
        Engine->>Stockfish: analyse(board, depth, multipv=3)
        Stockfish-->>Engine: MultiPV lines & Centipawns
        Engine->>Engine: classify_move() & calc accuracy
        Engine-->>API: Yield {"type": "progress", "ply": i, "percent": P}
        API-->>Frontend: Stream Event: progress
        Frontend->>Frontend: Update Progress Bar & Coach Badge
    end

    Engine->>Stockfish: engine.quit()
    Engine-->>API: Yield {"type": "complete", "data": {...}}
    API-->>Frontend: Stream Event: complete
    Frontend->>User: Display Interactive Board, Accuracy & Evaluation Graph
```

---

## 3. Component Diagram

```mermaid
flowchart TD
    subgraph Frontend_Layer ["Frontend Client (React 18 / Vite)"]
        UI["UI Components\n(ChessBoard, MoveList, EvalBar)"]
        State["State Management\n(Selected Ply, Audio, Theme)"]
        APIClient["API Client\n(frontend/src/api.js)"]
        UI --> State
        State --> APIClient
    end

    subgraph Backend_Layer ["Backend Application (FastAPI)"]
        Router["API Routers & Middleware\n(main.py)"]
        Config["Configuration & Env\n(config.py)"]
        Logging["Structured Logger\n(logger.py)"]
        ReviewCore["Review Core\n(review_engine.py)"]
        LiveCore["Live Analysis\n(live_analysis.py)"]
        OpeningsDB[("Openings Database\n(openings.json)")]

        Router --> Config
        Router --> Logging
        Router --> ReviewCore
        Router --> LiveCore
        ReviewCore --> OpeningsDB
    end

    subgraph Engine_Layer ["Chess Engine Subsystem"]
        UCIAdapter["Python-Chess UCI Adapter"]
        StockfishBin[["Stockfish Binary\n(/usr/games/stockfish)"]]

        ReviewCore --> UCIAdapter
        LiveCore --> UCIAdapter
        UCIAdapter --> StockfishBin
    end

    APIClient -->|JSON / NDJSON over HTTP| Router
```

---

## 4. Deployment Topology

The application is fully containerized and can be deployed to any Docker-compatible infrastructure, VPS (DigitalOcean, AWS EC2, GCP Compute Engine), or managed container service (Railway, Render).

```mermaid
flowchart TD
    subgraph Host ["Production Host / Docker Engine"]
        subgraph BridgeNet ["Bridge Network: chessreview-network"]
            FrontendCont["Frontend Container\n(nginx:1.27-alpine)\nPort 80 -> Host 3000"]
            BackendCont["Backend Container\n(python:3.12-slim)\nPort 8000 -> Host 8000"]
            StockfishProc["Stockfish Process\n(Isolated Non-Root UID 10001)"]

            FrontendCont -->|Proxy / Direct API| BackendCont
            BackendCont --> StockfishProc
        end
    end

    ClientBrowser["Client Web Browser"] -->|Port 3000| FrontendCont
    ClientBrowser -->|Port 8000| BackendCont
```

---

## 5. Docker Networking Diagram

```mermaid
flowchart LR
    subgraph External ["External Clients"]
        Browser["User Browser"]
    end

    subgraph Network ["Docker Network: chessreview-network (Bridge)"]
        direction TB
        FrontendService["Service: frontend\nContainer: chessreview-frontend\nInternal Port: 80\nPublished Port: 3000\nHealth: /"]
        BackendService["Service: backend\nContainer: chessreview-backend\nInternal Port: 8000\nPublished Port: 8000\nHealth: /health"]

        FrontendService -.->|Internal DNS resolution| BackendService
    end

    Browser -->|http://localhost:3000| FrontendService
    Browser -->|http://localhost:8000| BackendService
```

---

## 6. Repository Layout

```
ChessReview/
├── .github/                      # GitHub configurations & CI/CD
│   ├── ISSUE_TEMPLATE/           # Structured issue forms
│   │   ├── bug_report.yml
│   │   ├── config.yml
│   │   └── feature_request.yml
│   ├── PULL_REQUEST_TEMPLATE.md  # Standard pull request checklist
│   └── workflows/
│       └── ci.yml                # Automated CI pipeline
├── backend/                      # FastAPI Python Application
│   ├── engine/                   # Local engine binary cache (gitignored)
│   ├── games/
│   │   └── sample.pgn            # Reference game sample
│   ├── opening_books/
│   │   └── openings.json         # ECO opening database (3,399 positions)
│   ├── __init__.py
│   ├── config.py                 # Centralized configuration & environment loader
│   ├── Dockerfile                # Production backend container build
│   ├── live_analysis.py          # Single position evaluation module
│   ├── logger.py                 # Structured logging utility
│   ├── main.py                   # FastAPI application & route definitions
│   └── review_engine.py          # Core chess analysis & classification logic
├── docs/                         # In-depth architectural & API manuals
│   ├── API.md                    # REST API reference manual
│   ├── ARCHITECTURE.md           # Mermaid system diagrams & topology
│   └── CHESS_ENGINE.md           # Heuristic math & classification matrix
├── frontend/                     # React / Vite SPA
│   ├── public/                   # Static browser assets
│   ├── src/                      # React components, styles, audio, and state
│   ├── Dockerfile                # Production Nginx multi-stage build
│   ├── nginx.conf                # Nginx SPA routing & gzip configuration
│   ├── package.json              # Frontend dependencies and build scripts
│   └── vite.config.js            # Vite build configuration
├── infra/
│   └── docker-compose.yml        # Multi-container orchestration definition
├── tests/                        # Automated test suite
│   ├── __init__.py
│   ├── conftest.py               # TestClient & mock board fixtures
│   ├── test_api.py               # REST API contract and endpoint tests
│   └── test_review_engine.py     # Move classification & accuracy unit tests
├── .dockerignore                 # Container build exclusion list
├── .editorconfig                 # Cross-editor styling rules
├── .env.example                  # Environment configuration template
├── .flake8                       # Flake8 style guide configuration
├── .gitignore                    # Master Git ignore rules
├── .pre-commit-config.yaml       # Git pre-commit hooks
├── CHANGELOG.md                  # Project version history
├── CODE_OF_CONDUCT.md            # Contributor Covenant v2.1
├── CONTRIBUTING.md               # Contribution guidelines & workflow
├── LICENSE                       # MIT Open Source License
├── Makefile                      # Developer command center
├── pyproject.toml                # Black, Ruff, isort, pytest configs
├── README.md                     # Project portfolio README
├── requirements-dev.txt          # Development, testing, and linting packages
├── requirements.txt              # Production Python dependencies
└── SECURITY.md                   # Vulnerability disclosure policy
```

