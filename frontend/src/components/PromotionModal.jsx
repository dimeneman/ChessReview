import React from 'react';
import { CUSTOM_PIECES } from './CustomPieces';

export default function PromotionModal({ color, onSelect }) {
    const pieces = ['q', 'r', 'b', 'n'];
    // white pieces are wQ, wR etc. black are bQ, bR etc.
    const prefix = color === 'w' ? 'w' : 'b';

    return (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/50 rounded">
            <div className="bg-[#262421] p-4 rounded-lg shadow-2xl flex gap-4 border border-[#3c3a37]">
                {pieces.map(p => {
                    const PieceComponent = CUSTOM_PIECES[`${prefix}${p.toUpperCase()}`];
                    return (
                        <div
                            key={p}
                            onClick={() => onSelect(p)}
                            className="w-16 h-16 bg-[#302e2b] hover:bg-[#81b64c] rounded cursor-pointer flex items-center justify-center transition-colors border border-[#3c3a37] hover:border-[#81b64c]"
                        >
                            {PieceComponent && <PieceComponent squareWidth="50px" />}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
