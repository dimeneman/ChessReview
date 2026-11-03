/**
 * ChessReview Frontend API Client.
 * Connects to the FastAPI backend for game reviews, position evaluations, and Chess.com archives.
 * Supports environment variable configuration via VITE_API_URL with production fallback.
 */

const API_URL = import.meta.env.VITE_API_URL || "https://chessreview-production.up.railway.app";

/**
 * Submits a raw PGN string for full game evaluation.
 * @param {string} pgn - Portable Game Notation text.
 * @param {number} depth - Engine search depth (5-25).
 * @returns {Promise<object|null>} Analysis results or null on error.
 */
export async function reviewGame(pgn, depth = 18) {
  try {
    const response = await fetch(`${API_URL}/review-raw?depth=${depth}`, {
      method: "POST",
      headers: {
        "Content-Type": "text/plain",
      },
      body: pgn,
    });
    return await response.json();
  } catch (error) {
    console.error("Error reviewing game:", error);
    return null;
  }
}

/**
 * Submits a PGN string and streams real-time progress events using NDJSON.
 * @param {string} pgn - PGN text string.
 * @param {Function} onProgress - Callback invoked on progress events.
 * @param {number} depth - Engine search depth.
 * @returns {Promise<object>} Complete analysis payload or error object.
 */
export async function reviewGameStream(pgn, onProgress, depth = 18) {
  try {
    const response = await fetch(`${API_URL}/review-stream?depth=${depth}`, {
      method: "POST",
      headers: {
        "Content-Type": "text/plain",
      },
      body: pgn,
    });

    if (!response.ok) {
      const text = await response.text();
      return { error: text || response.statusText };
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.trim()) continue;
        try {
          const event = JSON.parse(line);

          if (event.error) {
            return { error: event.error };
          }

          onProgress(event);

          if (event.type === "complete") {
            return event.data;
          }
        } catch (e) {
          console.error("Error parsing stream line", e);
        }
      }
    }
  } catch (error) {
    console.error("Error reviewing game:", error);
    return { error: error.message };
  }
}

/**
 * Evaluates a single FEN chess board position.
 * @param {string} fen - Forsyth-Edwards Notation string.
 * @returns {Promise<object|null>} Position evaluation or null on error.
 */
export async function analyzePosition(fen) {
  try {
    const response = await fetch(`${API_URL}/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ fen }),
    });
    return await response.json();
  } catch (error) {
    console.error("Error analyzing position:", error);
    return null;
  }
}

/**
 * Fetches player games for a specific year and month from Chess.com public archives.
 * @param {string} username - Player username.
 * @param {number} year - Four-digit year.
 * @param {number} month - Month (1-12).
 * @returns {Promise<object|null>} Archive games or null on error.
 */
export async function fetchGames(username, year, month) {
  try {
    const response = await fetch(`${API_URL}/fetch-games`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, year, month }),
    });
    return await response.json();
  } catch (error) {
    console.error("Error fetching games:", error);
    return null;
  }
}
