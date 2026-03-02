import React, { useEffect, useRef } from 'react';

// Piece symbol mapping
const PIECE_SYMBOLS = {
  'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': ''
};

import { getClassificationStyle } from '../utils/moveClassifications';

function formatSan(san) {
  if (!san) return "";
  const firstChar = san[0];
  if (PIECE_SYMBOLS[firstChar] !== undefined) {
    return (
      <span className="flex items-center gap-0.5">
        <span className="text-lg leading-none">{PIECE_SYMBOLS[firstChar]}</span>
        <span>{san.slice(1)}</span>
      </span>
    );
  }
  return san;
}

function MoveCell({ move, isActive, onClick }) {
  if (!move) return <div className="flex-1"></div>;

  const style = getClassificationStyle(move.label);

  let tooltip = `${move.move_no}${move.side === 'W' ? '.' : '...'} ${move.played_san}`;
  tooltip += `\nType: ${move.label}`;
  if (move.cp_loss !== undefined) tooltip += `\nCP Loss: ${move.cp_loss}`;
  if (move.best_san && move.best_san !== "-" && move.best_san !== move.played_san) {
    tooltip += `\nBest Move: ${move.best_san}`;
  }

  return (
    <div
      onClick={onClick}
      title={tooltip}
      className={`
        flex-1 flex items-center gap-2 px-2 py-1 cursor-pointer rounded
        ${isActive ? 'bg-[#454341] brightness-125' : 'hover:bg-[#383634]'}
      `}
    >
      {/* Eval Icon Blob */}
      <div className="w-5 h-5 flex items-center justify-center shrink-0">
        {style && style.img ? (
          <img src={style.img} alt={move.label} className="w-full h-full object-contain" />
        ) : (
          <div className="w-2 h-2 rounded-full bg-gray-600" />
        )}
      </div>

      {/* Move Text */}
      <div className={`
        font-medium text-sm flex items-center
        ${isActive ? 'text-white' : 'text-[#bababa]'}
      `}>
        {formatSan(move.played_san)}
      </div>
    </div>
  );
}

export default function MoveList({ moves, currentPly, onSelect }) {
  const scrollRef = useRef(null);

  // Scroll active move into view without scrolling the main page
  useEffect(() => {
    if (scrollRef.current) {
      const parent = scrollRef.current.parentElement;
      if (parent) {
        const parentRect = parent.getBoundingClientRect();
        const childRect = scrollRef.current.getBoundingClientRect();

        // Calculate current scroll position
        const currentScroll = parent.scrollTop;

        // Calculate where child is relative to parent's top
        const childTopRelative = childRect.top - parentRect.top;

        // Center it
        const offset = childTopRelative - (parent.clientHeight / 2) + (scrollRef.current.clientHeight / 2);

        parent.scrollTo({
          top: currentScroll + offset,
          behavior: 'smooth'
        });
      }
    }
  }, [currentPly]);

  // Group moves into pairs
  const movePairs = [];
  for (let i = 0; i < moves.length; i += 2) {
    movePairs.push({
      number: moves[i].move_no,
      white: moves[i],
      black: moves[i + 1] || null,
      whiteIndex: i,
      blackIndex: i + 1
    });
  }

  return (
    <div className="bg-[#262421] rounded shadow-lg flex flex-col h-[300px]">
      {/* Header */}
      <div className="flex bg-[#211f1c] text-[#8b8987] text-xs font-bold py-1 px-4 border-b border-[#3c3a37]">
        <div className="w-8">#</div>
        <div className="flex-1">White</div>
        <div className="flex-1">Black</div>
      </div>

      {/* List */}
      <div className="overflow-y-auto flex-1 p-1 custom-scrollbar">
        {movePairs.map((pair, idx) => {
          const isWhiteActive = currentPly === pair.whiteIndex;
          const isBlackActive = currentPly === pair.blackIndex;
          const isCurrentRow = isWhiteActive || isBlackActive;

          return (
            <div
              key={idx}
              ref={isCurrentRow ? scrollRef : null}
              className={`flex items-center text-[#8b8987] font-mono text-xs rounded-sm ${idx % 2 === 0 ? 'bg-[#2b2926]' : ''}`}
            >
              <div className="w-8 text-center">{pair.number}.</div>

              <MoveCell
                move={pair.white}
                isActive={isWhiteActive}
                onClick={() => onSelect(pair.whiteIndex)}
              />

              <MoveCell
                move={pair.black}
                isActive={isBlackActive}
                onClick={() => pair.black ? onSelect(pair.blackIndex) : null}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}
