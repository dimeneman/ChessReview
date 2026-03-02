export default function MoveNavigation({ currentPly, maxPly, onJump }) {
  const buttonClass = "px-4 py-2 bg-[#373531] hover:bg-[#454341] border border-[#4a4845] text-white rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex-1";

  return (
    <div className="flex justify-between gap-2">
      <button
        className={buttonClass}
        onClick={() => onJump(0)}
        disabled={currentPly === 0}
      >
        ⏮
      </button>
      <button
        className={buttonClass}
        onClick={() => onJump(Math.max(currentPly - 1, 0))}
        disabled={currentPly === 0}
      >
        ◀
      </button>
      <button
        className={buttonClass}
        onClick={() => onJump(Math.min(currentPly + 1, maxPly))}
        disabled={currentPly >= maxPly}
      >
        ▶
      </button>
      <button
        className={buttonClass}
        onClick={() => onJump(maxPly)}
        disabled={currentPly >= maxPly}
      >
        ⏭
      </button>
    </div>
  );
}
