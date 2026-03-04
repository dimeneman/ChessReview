import React, { useState, useRef, useEffect } from 'react';
import { BOARD_THEMES } from '../utils/themes';

export default function ThemeSelector({ currentTheme, onSelect }) {
    const [isOpen, setIsOpen] = useState(false);
    const [dropdownPos, setDropdownPos] = useState({ top: 0, right: 0 });
    const buttonRef = useRef(null);

    const theme = BOARD_THEMES[currentTheme] || BOARD_THEMES['green'];
    if (!theme) return null;

    const toggle = () => {
        if (!isOpen && buttonRef.current) {
            const rect = buttonRef.current.getBoundingClientRect();
            setDropdownPos({
                top: rect.bottom + 8,
                right: window.innerWidth - rect.right,
            });
        }
        setIsOpen(prev => !prev);
    };

    // Close on outside click
    useEffect(() => {
        if (!isOpen) return;
        const handleClick = () => setIsOpen(false);
        window.addEventListener('click', handleClick);
        return () => window.removeEventListener('click', handleClick);
    }, [isOpen]);

    return (
        <div className="relative">
            <button
                ref={buttonRef}
                onClick={(e) => { e.stopPropagation(); toggle(); }}
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded border border-blue-500 transition-colors shadow-lg"
                title="Change Board Theme"
            >
                <div className="flex gap-0.5">
                    <div className="w-3 h-3 border border-white/20" style={{ backgroundColor: theme.light }}></div>
                    <div className="w-3 h-3 border border-white/20" style={{ backgroundColor: theme.dark }}></div>
                </div>
                <span className="text-sm font-bold">{theme.name}</span>
                <span className="text-xs text-white/70">▼</span>
            </button>

            {isOpen && (
                <div
                    className="fixed w-48 bg-[#262421] border border-[#3c3a37] rounded-lg shadow-xl z-[9999] overflow-hidden"
                    style={{ top: dropdownPos.top, right: dropdownPos.right }}
                    onClick={(e) => e.stopPropagation()}
                >
                    <div className="py-1">
                        {Object.entries(BOARD_THEMES).map(([key, themeOption]) => (
                            <button
                                key={key}
                                onClick={() => {
                                    onSelect(key);
                                    setIsOpen(false);
                                }}
                                className={`w-full text-left px-4 py-2 flex items-center gap-3 hover:bg-[#302e2b] transition-colors ${currentTheme === key ? 'bg-[#302e2b]' : ''}`}
                            >
                                <div className="flex border border-gray-600">
                                    <div className="w-4 h-4" style={{ backgroundColor: themeOption.light }} />
                                    <div className="w-4 h-4" style={{ backgroundColor: themeOption.dark }} />
                                </div>
                                <span className={`text-sm ${currentTheme === key ? 'text-white font-bold' : 'text-gray-300'}`}>
                                    {themeOption.name}
                                </span>
                            </button>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
