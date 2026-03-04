import { useRef, useState, useEffect } from "react";
import { Chess } from "chess.js";

import PGNInput from "./components/PGNInput";
import ChessBoard from "./components/ChessBoard";
import MoveList from "./components/MoveList";
import MoveNavigation from "./components/MoveNavigation";
import EvalGraph from "./components/EvalGraph";
import AccuracyPanel from "./components/AccuracyPanel";
import StatsPanel from "./components/StatsPanel";
import CoachPanel from "./components/CoachPanel";
import PromotionModal from "./components/PromotionModal";
import ThemeSelector from "./components/ThemeSelector";
import { BOARD_THEMES } from "./utils/themes";
import { reviewGameStream, analyzePosition } from "./api";
import GameImportModal from "./components/GameImportModal";
import AnalysisLoader from "./components/AnalysisLoader";

// Audio Imports
import moveSound from "./audio/move.mp3";
import captureSound from "./audio/capture.mp3";
import castleSound from "./audio/castle.mp3";
import checkSound from "./audio/check.mp3";
import promoteSound from "./audio/promote.mp3";
import gameEndSound from "./audio/gameend.mp3";

// Images
import rotateIcon from "./images/rotate.png";
import chessLogo from "./images/chess_logo.jpg";

// Audio Objects
const audio = {
  move: new Audio(moveSound),
  capture: new Audio(captureSound),
  castle: new Audio(castleSound),
  check: new Audio(checkSound),
  promote: new Audio(promoteSound),
  gameEnd: new Audio(gameEndSound),
};

const playMoveSound = (move, chess) => {
  if (!move) return;

  // Helper to play and rewind
  const playTrack = (track) => {
    track.currentTime = 0;
    track.play().catch(e => console.warn("Audio play failed", e));
  };

  // Game Over (Checkmate or Draw) - check state *after* move
  if (chess.isGameOver()) {
    playTrack(audio.gameEnd);
    return;
  }

  // Check
  if (chess.inCheck()) {
    playTrack(audio.check);
    return;
  }

  // Promotion
  if (move.flags && move.flags.includes('p')) {
    playTrack(audio.promote);
    return;
  }

  // Castle (k or q flags in chess.js)
  if (move.flags && (move.flags.includes('k') || move.flags.includes('q'))) {
    playTrack(audio.castle);
    return;
  }

  // Capture
  if (move.flags && (move.flags.includes('c') || move.flags.includes('e'))) {
    playTrack(audio.capture);
    return;
  }

  // Normal Move
  playTrack(audio.move);
};

export default function App() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [showImportModal, setShowImportModal] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(null);

  // Use explicit FEN instead of "start" to ensure consistency
  const [fen, setFen] = useState("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1");
  const [currentPly, setCurrentPly] = useState(0);
  const [lastMoveSquares, setLastMoveSquares] = useState([]);
  const [arrows, setArrows] = useState([]);
  const [possibleMoves, setPossibleMoves] = useState([]);
  /* Removed duplicates */
  const [selectedSquare, setSelectedSquare] = useState(null);
  const [customMoveLabel, setCustomMoveLabel] = useState(null);
  const [deviationData, setDeviationData] = useState(null);
  const [promotionMove, setPromotionMove] = useState(null);
  const [currentTheme, setCurrentTheme] = useState('green');
  const [orientation, setOrientation] = useState("white");
  const [liveEval, setLiveEval] = useState(null);

  const chessRef = useRef(new Chess());

  const handleGameAnalysis = async (pgn, depth = 18) => {
    setError(null);
    setAnalyzing(true);
    setAnalysisProgress({ percent: 0, cur_move: "Initializing...", ply: 0 });

    try {
      const res = await reviewGameStream(pgn, (event) => {
        if (event.type === 'progress') {
          setAnalysisProgress(event);
        } else if (event.type === 'init') {
          // Optional: set total ply 
        }
      }, depth);

      if (!res) {
        throw new Error("Failed to connect to analysis server.");
      }
      if (res.error) {
        throw new Error(res.error);
      }
      if (!res.moves || !Array.isArray(res.moves)) {
        throw new Error("Received invalid data from server.");
      }
      setData(res);
      setTimeout(() => loadPosition(0), 10);
    } catch (e) {
      setError(e.message || "An unexpected error occurred.");
    } finally {
      setAnalyzing(false);
      setAnalysisProgress(null);
    }
  };

  const makeMove = async (move) => {
    const chess = chessRef.current;

    // Safety check: ensure robust move handling
    try {
      // Validation check before mutation
      const temp = new Chess(chess.fen());
      try {
        if (!temp.move(move)) return false;
      } catch { return false; }
    } catch { return false; }

    try {
      // Capture FEN BEFORE making the move, for deviation analysis
      const fenBefore = chess.fen();
      const result = chess.move(move);
      if (result) {
        const newFen = chess.fen();
        setFen(newFen);
        setLastMoveSquares([result.from, result.to]);
        setPossibleMoves([]);
        setSelectedSquare(null);
        setCustomMoveLabel(null);

        const moveIndex = chess.history().length - 1;
        const newPly = moveIndex + 1;
        setCurrentPly(newPly);

        // Check if we are following the game path
        let onMainLine = false;
        // Verify data structure exists before accessing
        if (data && data.moves && moveIndex < data.moves.length) {
          const nextGameMove = data.moves[moveIndex];
          if (nextGameMove.played_san === result.san) {
            onMainLine = true;
            setDeviationData(null);
          }
        }

        if (!onMainLine) {
          // Set a temporary state immediately so the UI shows something
          setDeviationData({
            played_san: result.san,
            label: "Analyzing...",
            best_san: "-",
            cp_loss: 0,
          });

          // Analyze the position BEFORE the move (to classify it) — sequential to avoid Stockfish process contention
          const analysisBefore = await analyzePosition(fenBefore);
          console.log("[DeviationAnalysis] result.san:", result.san, "| analysisBefore:", analysisBefore);

          let label = "Unknown";
          let bestSan = "-";
          let cp_loss = 0;
          let evalBefore = 0;

          // Helper: strip check/mate symbols for comparison (chess.js vs python-chess may differ rarely)
          const normSan = (s) => (s || "").replace(/[+#]/g, "").trim();

          if (analysisBefore && !analysisBefore.error) {
            bestSan = analysisBefore.best_san || "-";
            evalBefore = analysisBefore.evaluation ?? 0;

            // Show best move arrow (only if the player didn't play the best move)
            if (analysisBefore.best_move && normSan(result.san) !== normSan(analysisBefore.best_san)) {
              const from = analysisBefore.best_move.substring(0, 2);
              const to = analysisBefore.best_move.substring(2, 4);
              setArrows([[from, to, "green"]]);
            } else {
              setArrows([]);
            }

            // Forced move: only 1 legal option
            if (analysisBefore.is_forced) {
              label = "Forced";
            } else if (normSan(result.san) === normSan(analysisBefore.best_san)) {
              label = "Best";
            }
            // If not best/forced, we'll compute cp_loss after getting analysisAfter below
          } else {
            console.warn("[DeviationAnalysis] analysisBefore failed:", analysisBefore);
            // Fallback: use game data if within game sequence
            if (data && data.moves && moveIndex < data.moves.length) {
              const gameMoveAtIndex = data.moves[moveIndex];
              if (gameMoveAtIndex) {
                bestSan = gameMoveAtIndex.best_san || "-";
                cp_loss = gameMoveAtIndex.cp_loss || 0;
                if (normSan(gameMoveAtIndex.best_san) === normSan(result.san)) label = "Best";
                else if (cp_loss <= 20) label = "Excellent";
                else if (cp_loss <= 50) label = "Good";
                else if (cp_loss <= 100) label = "Inaccuracy";
                else if (cp_loss <= 300) label = "Mistake";
                else label = "Blunder";
              }
            }
          }

          // Analyze position AFTER the move for eval bar + cp_loss computation
          const analysisAfter = await analyzePosition(newFen);
          console.log("[DeviationAnalysis] analysisAfter:", analysisAfter);

          if (analysisAfter && !analysisAfter.error && analysisAfter.evaluation !== undefined) {
            const evalAfter = analysisAfter.evaluation;

            // Compute cp_loss only if label is still unresolved
            if (label === "Unknown" || (analysisBefore && !analysisBefore.error && label !== "Best" && label !== "Forced")) {
              const side = result.color; // 'w' or 'b'
              let cpLossRaw;
              if (side === 'w') {
                cpLossRaw = evalBefore - evalAfter;
              } else {
                cpLossRaw = evalAfter - evalBefore;
              }
              cp_loss = Math.max(0, Math.round(cpLossRaw * 100));
              console.log("[DeviationAnalysis] evalBefore:", evalBefore, "evalAfter:", evalAfter, "cp_loss:", cp_loss, "side:", side);

              if (label !== "Best" && label !== "Forced") {
                if (cp_loss <= 20) label = "Excellent";
                else if (cp_loss <= 50) label = "Good";
                else if (cp_loss <= 100) label = "Inaccuracy";
                else if (cp_loss <= 300) label = "Mistake";
                else label = "Blunder";
              }
            }

            // Update eval bar from position AFTER the move (clamp ±100 → ±1)
            const normalizedEval = Math.max(-1, Math.min(1, evalAfter / 100.0));
            setLiveEval(normalizedEval);
          } else if (analysisBefore && !analysisBefore.error) {
            // Terminal position (checkmate etc.) — use before eval as fallback
            const normalizedEval = Math.max(-1, Math.min(1, evalBefore / 100.0));
            setLiveEval(normalizedEval);
          }

          setDeviationData({
            played_san: result.san,
            label,
            best_san: bestSan,
            cp_loss,
          });

          setCustomMoveLabel(null);
        }

        playMoveSound(result, chess);
        return true;
      }
    } catch (e) {
      console.error("makeMove error:", e);
      return false;
    }
    return false;
  };

  const handleMoveAttempt = (from, to) => {
    // Robust check: ask chess.js if this is a promotion
    try {
      const tempGame = new Chess(chessRef.current.fen());
      const move = tempGame.move({
        from,
        to,
        promotion: 'q',
      });

      // If the move is legal AND includes promotion flag
      if (move && move.flags.includes('p')) {
        setPromotionMove({ from, to });
        return;
      }
    } catch (e) {
      // invalid move or error
    }

    makeMove({
      from,
      to,
      promotion: "q",
    });
  };

  const onDrop = ({ sourceSquare, targetSquare }) => {
    handleMoveAttempt(sourceSquare, targetSquare);
  };


  const onSquareClick = (square) => {
    if (selectedSquare) {
      const move = possibleMoves.find(m => m.to === square);
      if (move) {
        handleMoveAttempt(selectedSquare, square);
        return;
      }
    }

    const piece = chessRef.current.get(square);
    if (piece && piece.color === chessRef.current.turn()) {
      if (selectedSquare === square) {
        setSelectedSquare(null);
        setPossibleMoves([]);
      } else {
        setSelectedSquare(square);
        const moves = chessRef.current.moves({
          square: square,
          verbose: true
        });
        setPossibleMoves(moves.map(move => ({
          to: move.to,
          isCapture: move.flags.includes("c") || move.flags.includes("e")
        })));
      }
    } else {
      setSelectedSquare(null);
      setPossibleMoves([]);
    }
  };

  const onMouseOverSquare = (square) => {
    if (selectedSquare) return;

    const moves = chessRef.current.moves({
      square: square,
      verbose: true
    });
    if (moves.length === 0) {
      setPossibleMoves([]);
      return;
    }
    setPossibleMoves(moves.map(move => ({
      to: move.to,
      isCapture: move.flags.includes("c") || move.flags.includes("e")
    })));
  };

  const onMouseOutSquare = () => {
    if (selectedSquare) return;
    setPossibleMoves([]);
  };

  const loadPosition = (ply, playSound = true) => {
    if (!data || !data.moves) return;

    setSelectedSquare(null);
    setPossibleMoves([]);
    setCustomMoveLabel(null);
    setDeviationData(null);
    setLiveEval(null);

    // Clamp ply
    const maxPly = data.moves.length;
    const requestedPly = ply;
    ply = Math.max(0, Math.min(ply, maxPly));

    const chess = chessRef.current;
    chess.reset();

    let lastMove = null;
    for (let i = 0; i < ply; i++) {
      if (data.moves[i]) {
        lastMove = chess.move(data.moves[i].played_san);
      }
    }

    // Only play sound if we actually moved to a valid new ply and requestedPly was within bounds
    // This prevents sound when hitting right arrow at the end of the game
    if (playSound && lastMove && requestedPly <= maxPly && requestedPly > 0) {
      // Also check if we are just reloading the same position (though that might be desired sometimes, usually not for navigation)
      // For now, the main issue is hitting 'next' at the end.
      playMoveSound(lastMove, chess);
    }

    const newFen = chess.fen();
    setFen(newFen);
    setCurrentPly(ply);

    if (lastMove) {
      setLastMoveSquares([lastMove.from, lastMove.to]);
    } else {
      setLastMoveSquares([]);
    }

    const moveIndex = ply - 1;
    if (moveIndex >= 0 && data.moves[moveIndex]) {
      const moveData = data.moves[moveIndex];
      const bestSan = moveData.best_san;
      if (bestSan && bestSan !== "-" && bestSan !== moveData.played_san) {
        try {
          // Replay to get previous state for arrow calculation
          const prevChess = new Chess();
          for (let i = 0; i < moveIndex; i++) {
            if (data.moves[i]) prevChess.move(data.moves[i].played_san);
          }
          const move = prevChess.move(bestSan);
          if (move) {
            setArrows([[move.from, move.to, "green"]]);
          } else {
            setArrows([]);
          }
        } catch {
          setArrows([]);
        }
      } else {
        setArrows([]);
      }
    } else {
      setArrows([]);
    }
  };

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (!data || !data.moves) return;
      if (e.key === "ArrowLeft") {
        loadPosition(currentPly - 1);
      } else if (e.key === "ArrowRight") {
        loadPosition(currentPly + 1, true);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [data, currentPly]);

  if (error) {
    return (
      <div className="min-h-screen bg-[#302e2b] flex items-center justify-center text-white flex-col gap-4">
        <h2 className="text-xl font-bold text-red-500">Analysis Error</h2>
        <p>{error}</p>
        <button
          className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded"
          onClick={() => { setError(null); setData(null); }}
        >
          Try Again
        </button>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-[#302e2b] flex items-center justify-center relative">
        <PGNInput
          onSubmit={handleGameAnalysis}
          onImportClick={() => setShowImportModal(true)}
          analyzing={analyzing}
        />
        {showImportModal && (
          <GameImportModal
            onClose={() => setShowImportModal(false)}
            onSelectGame={(pgn) => {
              setShowImportModal(false);
              handleGameAnalysis(pgn);
            }}
          />
        )}
        {analyzing && analysisProgress && <AnalysisLoader progress={analysisProgress} />}
      </div>
    );
  }

  const currentMoveData = (data.moves && currentPly > 0) ? data.moves[currentPly - 1] : null;

  return (
    <div className="min-h-screen bg-[#302e2b] text-white">
      {/* Top Header */}
      <div className="bg-[#262421] border-b border-[#3c3a37] px-2 sm:px-4 py-2 sm:py-3">
        <div className="max-w-[1600px] mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2 sm:gap-3 shrink-0">
            <img src={chessLogo} alt="DecodeChess Logo" className="w-6 h-6 sm:w-8 sm:h-8 rounded" />
            <h1 className="text-lg sm:text-lg font-bold tracking-tight whitespace-nowrap">DecodeChess</h1>
          </div>
          <div className="flex items-center gap-2 sm:gap-4 shrink-0 overflow-x-auto no-scrollbar">
            <ThemeSelector currentTheme={currentTheme} onSelect={setCurrentTheme} />
            <button
              className="p-1.5 sm:p-2 bg-[#3c3a37] hover:bg-[#4a4845] rounded transition-colors shrink-0"
              onClick={() => setOrientation(prev => prev === "white" ? "black" : "white")}
              title="Flip Board"
            >
              <img src={rotateIcon} alt="Rotate" className="w-4 h-4 sm:w-5 sm:h-5 opacity-80 hover:opacity-100" />
            </button>
            <button className="text-gray-400 hover:text-white text-lg sm:text-base px-1 shrink-0" onClick={() => setData(null)}>✕</button>
          </div>
        </div>
      </div>

      <div className="max-w-[1600px] mx-auto p-4 lg:p-6">
        <div className="flex flex-col lg:flex-row gap-6 items-center lg:items-start">

          {/* LEFT: Board Section */}
          <div className="w-full lg:max-w-[650px] flex-shrink-0 flex flex-col items-center">
            <div className="w-full max-w-[600px] flex gap-2 lg:gap-3 items-stretch mt-4 lg:mt-12 justify-center">
              {/* Eval Bar */}
              {(() => {
                const evalRaw = liveEval !== null ? liveEval : (currentMoveData ? currentMoveData.eval : 0);
                const evalPercent = ((evalRaw + 1) / 2) * 100;
                let evalText = Math.abs(evalRaw * 10).toFixed(1);
                if (Math.abs(evalRaw) === 1) evalText = "M";
                const isWhiteWinning = evalRaw >= 0;

                const isWhiteBottom = orientation === "white";

                return (
                  <div className={`w-5 lg:w-7 flex-shrink-0 bg-[#333333] rounded-sm overflow-hidden flex ${isWhiteBottom ? 'flex-col-reverse' : 'flex-col'} relative shadow-lg font-bold text-[10px] lg:text-xs leading-none select-none`}>
                    <div
                      className="bg-zinc-200 transition-all duration-300 w-full"
                      style={{ height: `${evalPercent}%` }}
                    />
                    {/* Center line */}
                    <div className="absolute top-1/2 left-0 w-full h-[2px] bg-black/30 z-10" />

                    {/* Text */}
                    {isWhiteWinning ? (
                      <div className={`absolute ${isWhiteBottom ? 'bottom-1' : 'top-1'} w-full text-center text-black z-20`}>
                        {evalText}
                      </div>
                    ) : (
                      <div className={`absolute ${isWhiteBottom ? 'top-1' : 'bottom-1'} w-full text-center text-gray-200 z-20`}>
                        {evalText}
                      </div>
                    )}
                  </div>
                );
              })()}

              {/* Chessboard Column */}
              <div className="flex-1 flex flex-col gap-2 min-w-0">
                {/* Top Player */}
                <div className="flex items-center gap-3 px-2">
                  <div className="w-8 h-8 rounded bg-[#3c3a37] flex items-center justify-center text-sm font-bold border border-[#504e4b]">
                    {(orientation === "white" ? data.players?.black : data.players?.white)?.[0] || "?"}
                  </div>
                  <span className="font-semibold text-gray-200">
                    {orientation === "white" ? (data.players?.black || "Black") : (data.players?.white || "White")}
                  </span>
                </div>

                <div className="w-full aspect-square max-w-[600px] rounded shadow-2xl relative">
                  <ChessBoard
                    fen={fen}
                    lastMoveSquares={lastMoveSquares}
                    lastMoveLabel={deviationData ? deviationData.label : (customMoveLabel || (currentMoveData ? currentMoveData.label : null))}
                    arrows={arrows}
                    onDrop={onDrop}
                    onMouseOverSquare={onMouseOverSquare}
                    onMouseOutSquare={onMouseOutSquare}
                    onSquareClick={onSquareClick}
                    possibleMoves={possibleMoves}
                    selectedSquare={selectedSquare}
                    orientation={orientation}
                    darkSquareStyle={{ backgroundColor: BOARD_THEMES[currentTheme].dark }}
                    lightSquareStyle={{ backgroundColor: BOARD_THEMES[currentTheme].light }}
                  />

                  {/* Promotion Modal */}
                  {promotionMove && (
                    <PromotionModal
                      color={chessRef.current.turn()}
                      onSelect={(piece) => {
                        makeMove({ ...promotionMove, promotion: piece });
                        setPromotionMove(null);
                      }}
                    />
                  )}
                </div>

                {/* Bottom Player */}
                <div className="flex items-center gap-3 px-2">
                  <div className="w-8 h-8 rounded bg-[#3c3a37] flex items-center justify-center text-sm font-bold border border-[#504e4b]">
                    {(orientation === "white" ? data.players?.white : data.players?.black)?.[0] || "?"}
                  </div>
                  <span className="font-semibold text-gray-200">
                    {orientation === "white" ? (data.players?.white || "White") : (data.players?.black || "Black")}
                  </span>
                </div>
              </div>
            </div>

            {/* Navigation */}
            <div className="w-full max-w-[600px] mt-4 bg-[#262421] rounded p-3 shadow-lg">
              <MoveNavigation
                currentPly={currentPly}
                maxPly={data.moves.length}
                onJump={loadPosition}
              />
            </div>
          </div>

          {/* RIGHT: Sidebar */}
          <div className="w-full lg:flex-1 lg:max-w-[450px] space-y-4">

            {/* Coach Comment */}
            <CoachPanel
              move={deviationData || currentMoveData}
              onNext={() => loadPosition(currentPly + 1, true)}
              onPlayBestMove={(san) => {
                loadPosition(currentPly - 1);
                makeMove(san);
              }}
              theme={BOARD_THEMES[currentTheme]}
            />

            {/* Move List */}
            {/* Move List */}
            <MoveList
              moves={data.moves}
              currentPly={deviationData ? -1 : currentPly - 1} // Deselect if deviating
              onSelect={(idx) => loadPosition(idx + 1)}
            />

            {/* Evaluation Graph */}
            <div className="bg-black rounded shadow-lg overflow-hidden">
              <div className="h-24">
                <EvalGraph data={data.eval_graph} moves={data.moves} />
              </div>
            </div>

            {/* Accuracy */}
            <div className="bg-[#262421] rounded shadow-lg p-4">
              <AccuracyPanel
                white={data.white_accuracy}
                black={data.black_accuracy}
                theme={BOARD_THEMES[currentTheme]}
              />
            </div>

          </div>

          {/* THIRD COLUMN: Move Analysis */}
          <div className="w-full lg:w-[300px] space-y-4">
            <div className="bg-[#262421] rounded shadow-lg p-4">
              <StatsPanel moves={data.moves} opening={(currentMoveData && currentMoveData.opening) || "Starting Position"} />
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
