import { useState, useEffect, useRef } from "react";
import Chessboard from "chessboardjsx";

import { CUSTOM_PIECES } from "./CustomPieces";
import { getClassificationStyle } from '../utils/moveClassifications';

export default function ChessBoard({ fen, lastMoveSquares = [], arrows = [], lastMoveLabel = null, onDrop, onMouseOverSquare, onMouseOutSquare, onSquareClick, possibleMoves = [], selectedSquare = null, lightSquareStyle, darkSquareStyle, orientation = "white" }) {
  const [visibleLabel, setVisibleLabel] = useState(null);
  const [boardWidth, setBoardWidth] = useState(600);
  const containerRef = useRef(null);

  useEffect(() => {
    // Immediately hide the previous label when the move changes so it doesn't persist during animation
    setVisibleLabel(null);

    if (lastMoveLabel) {
      // Delay showing the new label to match animation duration (300ms) plus a clear buffer
      const timer = setTimeout(() => {
        setVisibleLabel(lastMoveLabel);
      }, 400);
      return () => clearTimeout(timer);
    }
  }, [lastMoveLabel]);

  useEffect(() => {
    const handleResize = (entries) => {
      for (let entry of entries) {
        if (entry.contentRect) {
          // Constrain maximum width
          setBoardWidth(Math.min(entry.contentRect.width, 600));
        }
      }
    };

    const observer = new ResizeObserver(handleResize);

    if (containerRef.current) {
      observer.observe(containerRef.current);
    }

    return () => {
      if (containerRef.current) observer.unobserve(containerRef.current);
      observer.disconnect();
    };
  }, []);

  const moveStyle = visibleLabel ? getClassificationStyle(visibleLabel) : null;
  const targetSquare = lastMoveSquares.length === 2 ? lastMoveSquares[1] : null;

  // Function to calculate position of a square (assuming white bottom)
  const getSquarePos = (square) => {
    if (!square) return null;
    const file = square.charCodeAt(0) - 97; // 'a' -> 0
    const rank = parseInt(square[1]) - 1;   // '1' -> 0

    // Board is 600px, so each square is 12.5%
    if (orientation === "white") {
      // White orientation: a1 is bottom-left (0, 0)
      // left = file * 12.5%
      // top = (7 - rank) * 12.5% (since top 0 is rank 8)
      return {
        left: file * 12.5 + "%",
        top: (7 - rank) * 12.5 + "%",
      };
    } else {
      // Black orientation: h8 is bottom-left (visually in code logic, but rendered top-left usually... wait)
      // In "black" orientation:
      // h8 is top-left (0,0) ? No, standard chess board logic:
      // a1 is top-right. h8 is bottom-left. 
      // Actually, let's verify visual:
      // White: a1 @ bottom-left.
      // Black: h8 @ bottom-left.

      // Simpler logic:
      // file 0 (a) -> becomes file 7 (h) visual position
      // rank 0 (1) -> becomes rank 7 (8) visual position

      const visualFile = 7 - file;
      const visualRank = 7 - rank; // If rank 0 (row 8 visual in white), in black it is row 1 visual.

      // Wait, let's re-derive:
      // White View:
      // Rows (top to bottom): 8, 7, ..., 1. Index 0..7.
      // Cols (left to right): a, b, ..., h. Index 0..7.
      // Square a1 (file 0, rank 0) -> Row 7 (bottom), Col 0 (left).

      // Black View:
      // Rows (top to bottom): 1, 2, ..., 8.
      // Cols (left to right): h, g, ..., a.
      // Square a1 (file 0, rank 0) -> Row 0 (top), Col 7 (right).

      // Formula for Black:
      // Left % = (7 - file) * 12.5
      // Top % = rank * 12.5

      return {
        left: (7 - file) * 12.5 + "%",
        top: rank * 12.5 + "%",
      };
    }
  };

  const iconPos = getSquarePos(targetSquare);
  const selectedPos = getSquarePos(selectedSquare);

  return (
    <div ref={containerRef} className="w-full h-full flex items-center justify-center bg-[#302e2b] relative">
      <div className="rounded overflow-hidden w-full flex justify-center">
        <Chessboard
          id="chessboardjsx"
          position={fen}
          width={boardWidth}
          draggable={true}
          onDrop={onDrop}
          onMouseOverSquare={onMouseOverSquare}
          onMouseOutSquare={onMouseOutSquare}
          onSquareClick={onSquareClick}
          orientation={orientation}
          pieces={CUSTOM_PIECES}
          darkSquareStyle={darkSquareStyle || { backgroundColor: '#769656' }}
          lightSquareStyle={lightSquareStyle || { backgroundColor: '#eeeed2' }}
          transitionDuration={300}
        />
      </div>

      {/* Selected Square Highlight */}
      {selectedPos && (
        <div
          className="absolute z-10 pointer-events-none bg-[rgba(255,255,50,0.5)]"
          style={{
            left: selectedPos.left,
            top: selectedPos.top,
            width: "12.5%",
            height: "12.5%",
          }}
        />
      )}

      {/* Move Classification Icon */}
      {moveStyle && moveStyle.img && iconPos && (
        <div
          className="absolute z-20 w-[4.5%] h-[4.5%] transform translate-x-[40%] text-white font-black text-xs sm:text-sm md:text-base lg:text-lg"
          style={{
            left: iconPos.left,
            top: iconPos.top,
            // Offset to top-right corner of the square
            marginTop: "-1%",
            marginLeft: "8%"
          }}
        >
          <img
            src={moveStyle.img}
            alt={moveStyle.label}
            className="w-full h-full object-contain drop-shadow-lg"
          />
        </div>
      )}

      {/* Legal Move Hints */}
      {possibleMoves.map((move, i) => {
        const pos = getSquarePos(move.to);
        if (!pos) return null;

        return (
          <div
            key={i}
            className="absolute z-10 pointer-events-none"
            style={{
              left: pos.left,
              top: pos.top,
              width: "12.5%",
              height: "12.5%",
              display: "flex",
              justifyContent: "center",
              alignItems: "center"
            }}
          >
            {move.isCapture ? (
              // Ring for capture
              <div className="w-[100%] h-[100%] rounded-full border-[6px] border-black/10" />
            ) : (
              // Dot for move
              <div className="w-[30%] h-[30%] bg-black/20 rounded-full" />
            )}
          </div>
        );
      })}
    </div>
  );
}
