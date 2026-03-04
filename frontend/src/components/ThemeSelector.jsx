import React, { useState } from 'react';
import { BOARD_THEMES } from '../utils/themes';

export default function ThemeSelector({ currentTheme, onSelect }) {
    const [isOpen, setIsOpen] = useState(false);

    // Safety check
    const theme = BOARD_THEMES[currentTheme] || BOARD_THEMES['green'];
    if (!theme) return null;

    const toggle = () => setIsOpen(!isOpen);

    return (
        <div className="relative z-50">
            <button
                onClick={toggle}
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded border border-blue-500 transition-colors shadow-lg"
                title="Change Board Theme"
            >
                <div className="flex gap-0.5">
                    {/* Tiny preview icon */}
                    <div className="w-3 h-3 border border-white/20" style={{ backgroundColor: theme.light }}></div>
                    <div className="w-3 h-3 border border-white/20" style={{ backgroundColor: theme.dark }}></div>
                </div>
                <span className="text-sm font-bold">{theme.name}</span>
                <span className="text-xs text-white/70">▼</span>
            </button>

            {isOpen && (
                <div className="absolute top-full right-0 mt-2 w-48 bg-[#262421] border border-[#3c3a37] rounded-lg shadow-xl z-50 overflow-hidden">
                    <div className="py-1">
                        {Object.entries(BOARD_THEMES).map(([key, theme]) => (
                            <button
                                key={key}
                                onClick={() => {
                                    onSelect(key);
                                    setIsOpen(false);
                                }}
                                className={`w-full text-left px-4 py-2 flex items-center gap-3 hover:bg-[#302e2b] transition-colors ${currentTheme === key ? 'bg-[#302e2b]' : ''}`}
                            >
                                <div className="flex border border-gray-600">
                                    <div className="w-4 h-4" style={{ backgroundColor: theme.light }} />
                                    <div className="w-4 h-4" style={{ backgroundColor: theme.dark }} />
                                </div>
                                <span className={`text-sm ${currentTheme === key ? 'text-white font-bold' : 'text-gray-300'}`}>
                                    {theme.name}
                                </span>
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* Click outside closer overlay - behind dropdown (z-40 < z-50) */}
            {isOpen && (
                <div className="fixed inset-0 z-40" onMouseDown={() => setIsOpen(false)} />
            )}
        </div>
    );
}
