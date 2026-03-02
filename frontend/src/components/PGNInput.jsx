import { useState } from 'react';
import chessLogo from '../images/chess_logo.jpg';

export default function PGNInput({ onSubmit, onImportClick, analyzing }) {
  const [pgn, setPgn] = useState("");
  const [depth, setDepth] = useState(18);
  const [localLoading, setLocalLoading] = useState(false);
  const [error, setError] = useState(null);

  const isLoading = analyzing || localLoading;

  const handleSubmit = async () => {
    if (!pgn.trim()) return;

    if (!pgn.trim()) return;

    setLocalLoading(true);
    setError(null);

    try {
      await onSubmit(pgn, depth);
    } catch (err) {
      console.error("Error submitting PGN:", err);
      const errorMsg = err.response?.data?.error || err.message || "Failed to analyze game. Check that the backend is running.";
      setError(errorMsg);
      setError(errorMsg);
      setLocalLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center w-full max-w-3xl px-4">
      <div className="bg-[#262421] w-full rounded-lg shadow-2xl overflow-hidden border border-[#3c3a37]">

        {/* Header */}
        <div className="bg-[#373531] px-6 py-4 border-b border-[#4a4845]">
          <h2 className="text-xl font-bold text-white flex items-center gap-3">
            <img src={chessLogo} alt="DecodeChess Logo" className="w-8 h-8 rounded" />
            DecodeChess
          </h2>
        </div>

        {/* Body */}
        <div className="p-6">
          <p className="text-gray-400 mb-3 text-sm flex justify-between items-center">
            <span>Paste your PGN (Portable Game Notation) below to analyze your game with Stockfish.</span>
            <button
              onClick={onImportClick}
              className="bg-[#373531] hover:bg-[#454341] text-[#81b64c] px-3 py-1 rounded text-xs font-bold border border-[#4a4845] transition-colors"
            >
              ☁️ Import from Chess.com
            </button>
          </p>

          <textarea
            className="w-full h-56 bg-[#1a1917] border border-[#4a4845] rounded p-4 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-[#81b64c] transition-shadow resize-none text-gray-300 placeholder-gray-600"
            placeholder='[Event "Casual Game"]
[White "Player1"]
[Black "Player2"]

1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. b4 ...'
            value={pgn}
            onChange={(e) => setPgn(e.target.value)}
          />

          {error && (
            <div className="mt-3 p-3 bg-red-900/30 border border-red-700/50 rounded text-red-300 text-sm">
              ❌ {error}
            </div>
          )}

          <div className="flex items-center gap-4 mt-4 bg-[#1a1917] p-3 rounded border border-[#4a4845]">
            <span className="text-gray-400 text-sm font-bold">Analysis Depth:</span>
            <input
              type="range"
              min="5"
              max="25"
              step="1"
              value={depth}
              onChange={(e) => setDepth(Number(e.target.value))}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-[#81b64c]"
            />
            <span className="text-[#81b64c] font-bold w-6 text-right">{depth}</span>
          </div>

          <div className="flex justify-end mt-4">
            <button
              onClick={handleSubmit}
              disabled={isLoading || !pgn.trim()}
              className={`
                px-10 py-3 rounded font-bold text-white transition-all transform active:scale-95
                ${isLoading || !pgn.trim()
                  ? "bg-gray-600 cursor-not-allowed"
                  : "bg-[#81b64c] hover:bg-[#709e43] active:bg-[#5e8837]"}
                shadow-lg
              `}
            >
              {isLoading ? "Analyzing..." : "Review Game"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
