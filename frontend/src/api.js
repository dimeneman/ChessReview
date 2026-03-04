const API_URL = "https://chessreview-production.up.railway.app";

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

          if (event.type === 'complete') {
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
