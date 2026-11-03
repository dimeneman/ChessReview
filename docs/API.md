# ChessReview API Reference Manual

The **ChessReview API** is a high-performance REST and streaming API built with **FastAPI** that powers Chess.com-style game evaluations, centipawn loss calculations, live FEN position analysis, and Chess.com archive integration.

* **Base URL (Local / Docker):** `http://localhost:8000`
* **Interactive OpenAPI Docs (Swagger UI):** `http://localhost:8000/docs`
* **Alternative ReDoc UI:** `http://localhost:8000/redoc`
* **OpenAPI JSON Schema:** `http://localhost:8000/openapi.json`

---

## Table of Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Service root status and documentation links |
| `GET` | `/health` | Container health probe (uptime, version, engine status) |
| `POST` | `/review` | Full game review via JSON payload |
| `POST` | `/review-raw` | Full game review via raw plain-text PGN |
| `POST` | `/review-stream` | Real-time streaming game review via NDJSON events |
| `POST` | `/analyze` | Live position analysis for a single FEN string |
| `POST` | `/fetch-games` | Fetch monthly game archives from Chess.com public API |

---

## 1. System Endpoints

### `GET /`
Returns basic metadata about the service.

#### Response (`200 OK`)
```json
{
  "service": "ChessReview API",
  "version": "1.0.0",
  "status": "online",
  "docs_url": "/docs",
  "health_url": "/health"
}
```

#### Example cURL
```bash
curl -X GET http://localhost:8000/
```

---

### `GET /health`
Used by Docker container health checks and Kubernetes liveness/readiness probes to verify service state and engine availability.

#### Response (`200 OK`)
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production",
  "uptime_seconds": 142.58,
  "engine_available": true,
  "engine_path": "/usr/games/stockfish",
  "timestamp": "2026-11-03T12:00:00.000000+00:00"
}
```

#### Example cURL
```bash
curl -X GET http://localhost:8000/health
```

---

## 2. Game Review Endpoints

### `POST /review`
Evaluates an entire chess game submitted as a JSON object.

#### Headers
* `Content-Type: application/json`

#### Request Body
```json
{
  "pgn": "1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7# 1-0"
}
```

#### Response (`200 OK`)
```json
{
  "moves": [
    {
      "ply": 1,
      "move_no": 1,
      "side": "W",
      "played_san": "e4",
      "best_san": "e4",
      "is_book_move": true,
      "cp_loss": 0,
      "label": "Theory",
      "coach_comment": "Book move following opening theory.",
      "eval": 0.25,
      "opening": "King's Pawn Game"
    }
  ],
  "opening": "King's Pawn Game",
  "white_accuracy": 98.5,
  "black_accuracy": 72.1,
  "eval_graph": [0.25, 0.20, 0.85, 0.60, 2.10, -0.10, 1.0]
}
```

#### Error Response (`400 Bad Request`)
```json
{
  "detail": "PGN text cannot be empty."
}
```

#### Example cURL
```bash
curl -X POST http://localhost:8000/review \
  -H "Content-Type: application/json" \
  -d '{"pgn": "1. e4 e5 2. Nf3 Nc6 3. Bb5 1-0"}'
```

---

### `POST /review-raw`
Accepts raw plain-text PGN string directly in the request body (ideal for copy-pasting from Chess.com or Lichess).

#### Query Parameters
* `depth` *(optional, integer, default: 18, range: 5–25)*: Search depth for the Stockfish engine.

#### Headers
* `Content-Type: text/plain`

#### Example cURL
```bash
curl -X POST "http://localhost:8000/review-raw?depth=16" \
  -H "Content-Type: text/plain" \
  --data-binary "1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 1-0"
```

---

### `POST /review-stream`
Analyzes a chess game and streams real-time progress using **Newline-Delimited JSON (NDJSON)**. This powers progress bars and incremental move rendering on the frontend.

#### Query Parameters
* `depth` *(optional, integer, default: 18)*: Search depth.

#### Headers
* `Content-Type: text/plain`
* `Accept: application/x-ndjson`

#### Stream Events
```json
{"type": "init", "total_ply": 48, "players": {"white": "MagnusCarlsen", "black": "Hikaru"}}
{"type": "progress", "ply": 1, "cur_move": "e4", "percent": 0.0}
{"type": "progress", "ply": 2, "cur_move": "e5", "percent": 2.1}
...
{"type": "complete", "data": { "moves": [...], "white_accuracy": 94.2, "black_accuracy": 89.8, "eval_graph": [...] }}
```

#### Example cURL
```bash
curl -N -X POST "http://localhost:8000/review-stream?depth=14" \
  -H "Content-Type: text/plain" \
  --data-binary @backend/games/sample.pgn
```

---

## 3. Position Analysis Endpoint

### `POST /analyze`
Analyzes an individual board position expressed in **FEN (Forsyth-Edwards Notation)** format.

#### Request Body
```json
{
  "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
}
```

#### Response (`200 OK`)
```json
{
  "best_move": "e7e5",
  "best_san": "e5",
  "evaluation": 0.25,
  "turn": "black",
  "is_forced": false,
  "is_game_over": false
}
```

#### Game-Over Position Example (Checkmate)
When passed a checkmate or stalemate position, the API automatically detects the terminal state without spawning an engine subprocess:
```json
{
  "best_move": null,
  "best_san": "-",
  "evaluation": -100.0,
  "turn": "white",
  "is_forced": false,
  "is_game_over": true
}
```

#### Example cURL
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"fen": "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"}'
```

---

## 4. Third-Party Integration Endpoint

### `POST /fetch-games`
Proxies requests to the public Chess.com API archive to fetch a player's games for a specified month.

#### Request Body
```json
{
  "username": "hikaru",
  "year": 2026,
  "month": 1
}
```

#### Response (`200 OK`)
```json
{
  "games": [
    {
      "url": "https://www.chess.com/game/live/...",
      "pgn": "...",
      "time_control": "180+2",
      "white": { "rating": 3200, "result": "win", "username": "hikaru" },
      "black": { "rating": 3150, "result": "resigned", "username": "opponent" }
    }
  ]
}
```

#### Example cURL
```bash
curl -X POST http://localhost:8000/fetch-games \
  -H "Content-Type: application/json" \
  -d '{"username": "hikaru", "year": 2026, "month": 1}'
```

