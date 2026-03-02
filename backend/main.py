from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from review_engine import review_game, review_game_stream
from live_analysis import analyze_position
import requests

app = FastAPI(
    title="Chess Review API",
    description="Chess.com-style game review using Stockfish",
    version="1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Existing JSON endpoint (keep it) ----------

class PGNRequest(BaseModel):
    pgn: str

@app.post("/review")
def review(req: PGNRequest):
    return review_game(req.pgn)


# ---------- NEW RAW PGN endpoint (BEST FOR USERS) ----------

@app.post("/review-raw")
def review_raw(
    pgn: str = Body(..., media_type="text/plain"),
    depth: int = 18  # Default depth if not specified
):
    """
    Accepts raw PGN text (copy-paste friendly).
    Optionally accepts a 'depth' query parameter (e.g. ?depth=20).
    """
    # Ensure depth is within reasonable bounds
    depth = max(5, min(depth, 25))
    depth = max(5, min(depth, 25))
    return review_game(pgn, depth=depth)


@app.post("/review-stream")
def review_stream(
    pgn: str = Body(..., media_type="text/plain"),
    depth: int = 18
):
    """
    Streams analysis progress as NDJSON events.
    Yields: {"type": "init", ...} -> {"type": "progress", ...} -> {"type": "complete", ...}
    """
    depth = max(5, min(depth, 25))
    return StreamingResponse(
        review_game_stream(pgn, depth=depth),
        media_type="application/x-ndjson"
    )

class AnalyzeRequest(BaseModel):
    fen: str

@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    return analyze_position(req.fen)

class FetchGamesRequest(BaseModel):
    username: str
    year: int
    month: int

@app.post("/fetch-games")
def fetch_games(req: FetchGamesRequest):
    url = f"https://api.chess.com/pub/player/{req.username}/games/{req.year}/{req.month:02d}"
    headers = {
        "User-Agent": "ChessReviewApp/1.0 (contact@example.com)"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}
