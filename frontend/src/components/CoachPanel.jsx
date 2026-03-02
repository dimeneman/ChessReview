import React from 'react';
import { getClassificationStyle } from '../utils/moveClassifications';

export default function CoachPanel({ move, onNext, onPlayBestMove, theme }) {
    // Default theme fallback
    const btnColor = theme ? theme.dark : '#81b64c';

    if (!move) {
        return (
            <div className="bg-[#21201d] rounded shadow-lg p-4 text-center">
                <div className="text-gray-400 font-bold mb-3">Ready to review?</div>
                <button
                    onClick={onNext}
                    style={{ backgroundColor: btnColor }}
                    className="w-full text-white font-bold py-3 px-4 rounded transition-colors shadow-lg flex items-center justify-center gap-2 hover:opacity-90 active:scale-[0.98]"
                >
                    <span>➡️</span> Start Review
                </button>
            </div>
        );
    }

    const style = getClassificationStyle(move.label);

    // Construct text logic can remain or move to util. keeping simple here
    let feedbackText = `${move.played_san} is played`;
    if (style && style.label) {
        if (["Brilliant", "Great", "Best", "Excellent", "Good"].includes(style.label)) {
            feedbackText = `${move.played_san} is ${style.label.toLowerCase()}!`;
            if (style.label === "Best") feedbackText = `${move.played_san} is the best move!`;
        } else if (["Inaccuracy", "Mistake", "Blunder"].includes(style.label)) {
            feedbackText = `${move.played_san} is a ${style.label.toLowerCase()}`;
        } else {
            feedbackText = `${move.played_san} is ${style.label.toLowerCase()}`;
        }
    }

    const showBest = move.best_san && move.best_san !== "-" && move.best_san !== move.played_san && move.label !== "Best" && move.label !== "Theory" && move.label !== "Book";

    return (
        <div className="bg-[#21201d] rounded shadow-lg overflow-hidden">
            <div className="p-4">
                <div className="flex items-center gap-3 mb-2">
                    {/* Icon */}
                    <div className="w-8 h-8 flex items-center justify-center">
                        {style && style.img ? (
                            <img src={style.img} alt={move.label} className="w-full h-full object-contain" />
                        ) : (
                            <div className="w-full h-full bg-gray-600 rounded-full" />
                        )}
                    </div>

                    {/* Main Feedback Text */}
                    <h2 className="text-lg font-bold leading-tight" style={{ color: style ? style.color : '#ccc' }}>
                        {feedbackText}
                    </h2>
                </div>

                {/* Best Move Recommendation */}
                {showBest && (
                    <div className="ml-11 text-sm font-medium" style={{ color: btnColor }}>
                        The best move was
                        <span
                            onClick={() => onPlayBestMove(move.best_san)}
                            className="font-bold underline decoration-dotted ml-1 cursor-pointer hover:opacity-80 px-1 rounded transition-colors"
                        >
                            {move.best_san}
                        </span>
                    </div>
                )}
            </div>

            {/* Action Bar */}
            <div className="bg-[#262421] px-4 py-3 border-t border-[#3c3a37]">
                <button
                    onClick={onNext}
                    style={{ backgroundColor: btnColor }}
                    className="w-full text-white font-bold py-2 px-4 rounded transition-colors shadow flex items-center justify-center gap-2 hover:opacity-90 active:scale-[0.98]"
                >
                    Next Move ➡️
                </button>
            </div>
        </div>
    );
}
