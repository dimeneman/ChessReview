import React, { useMemo } from 'react';
import { getClassificationStyle } from '../utils/moveClassifications';

const LABELS = [
    { name: 'Theory', displayName: 'Theory', color: 'text-amber-600', icon: '📖' },
    { name: 'Brilliant', color: 'text-cyan-400', icon: '!!' },
    { name: 'Great', color: 'text-blue-400', icon: '!' },
    { name: 'Best', color: 'text-green-300', icon: '✓' },
    { name: 'Excellent', color: 'text-green-500', icon: '👍' },
    { name: 'Good', color: 'text-green-500', icon: '✔️' },
    { name: 'Inaccuracy', color: 'text-orange-400', icon: '?!' },
    { name: 'Mistake', color: 'text-red-400', icon: '?' },
    { name: 'Blunder', color: 'text-red-600', icon: '??' },
    { name: 'Missed Win', displayName: 'Miss', color: 'text-orange-600', icon: '⚠' },
];

export default function StatsPanel({ moves, opening }) {
    const stats = useMemo(() => {
        const s = { W: {}, B: {} };
        LABELS.forEach(l => {
            s.W[l.name] = 0;
            s.B[l.name] = 0;
        });

        moves.forEach(m => {
            if (s[m.side] && s[m.side][m.label] !== undefined) {
                s[m.side][m.label]++;
            }
        });
        return s;
    }, [moves]);

    return (
        <div className="p-2">
            {opening && (
                <div className="mb-6 p-3 bg-[#302e2b] rounded border-l-4 border-orange-500">
                    <div className="text-xs text-gray-400 uppercase tracking-wider font-bold mb-1">Opening</div>
                    <div className="text-lg font-bold text-white leading-tight">{opening}</div>
                </div>
            )}

            <h4 className="text-lg font-bold mb-4 text-gray-200 border-b border-[#3c3a37] pb-2">Move Analysis</h4>
            <div className="space-y-2 text-sm">
                <div className="grid grid-cols-3 gap-4 pb-2 font-bold text-gray-400 text-center uppercase tracking-wider text-xs">
                    <div>White</div>
                    <div>Type</div>
                    <div>Black</div>
                </div>

                {LABELS.map(label => {
                    const style = getClassificationStyle(label.name);
                    const isMissedWin = label.name === 'Missed Win';

                    return (
                        <div
                            key={label.name}
                            className="grid grid-cols-3 gap-4 items-center py-2 hover:bg-[#373531] rounded px-3 transition-colors"
                        >
                            <div className="text-center font-mono text-base text-gray-300 font-bold">
                                {stats.W[label.name] || 0}
                            </div>

                            <div className={`flex items-center justify-center gap-2 ${label.color} font-bold text-sm`}>
                                {isMissedWin ? (
                                    <span className="text-lg">{label.icon}</span>
                                ) : (
                                    style && style.img && <img src={style.img} alt={label.name} className="w-5 h-5 object-contain" />
                                )}
                                <span>{label.displayName || label.name}</span>
                            </div>

                            <div className="text-center font-mono text-base text-gray-300 font-bold">
                                {stats.B[label.name] || 0}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
