import React, { useState } from 'react';
import { fetchGames } from '../api';

const GameImportModal = ({ onClose, onSelectGame }) => {
    const [username, setUsername] = useState('');
    const [month, setMonth] = useState(new Date().getMonth() + 1);
    const [year, setYear] = useState(new Date().getFullYear());
    const [filterType, setFilterType] = useState('all');
    const [games, setGames] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ];

    const filteredGames = games.filter(game => {
        if (filterType === 'all') return true;
        return game.time_class === filterType;
    });

    const handleFetch = async () => {
        if (!username) return;
        setLoading(true);
        setError(null);
        setGames([]);

        try {
            const data = await fetchGames(username, year, month);

            if (data && data.games) {
                // Sort by date descending
                const sortedGames = data.games.sort((a, b) => b.end_time - a.end_time);
                setGames(sortedGames);
            } else if (data && data.error) {
                setError(data.error);
            } else {
                setError("No games found or error fetching data.");
            }
        } catch (err) {
            setError("Failed to fetch games.");
        } finally {
            setLoading(false);
        }
    };

    const getResultIcon = (game, user) => {
        let result = null;
        let color = null;

        const userLower = user.toLowerCase();
        const isWhite = game.white.username.toLowerCase() === userLower;
        const isBlack = game.black.username.toLowerCase() === userLower;

        if (!isWhite && !isBlack) return { icon: "?", color: "text-gray-400" };

        const myResult = isWhite ? game.white.result : game.black.result;

        // Chess.com result codes: 'win', 'checkmated', 'agreed', 'repetition', 'timeout', 'resigned', etc.
        if (myResult === 'win') {
            return { icon: "+", bg: "bg-green-600" };
        } else if (['checkmated', 'timeout', 'resigned', 'abandoned', 'lose'].includes(myResult)) {
            return { icon: "-", bg: "bg-red-600" };
        } else {
            return { icon: "=", bg: "bg-gray-500" }; // Draw
        }
    };

    const getGameIcon = (timeClass) => {
        switch (timeClass) {
            case 'bullet': return '🚄';
            case 'blitz': return '⚡';
            case 'rapid': return '⏱️';
            case 'daily': return '☀️';
            default: return '♟️';
        }
    };

    return (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 backdrop-blur-sm">
            <div className="bg-[#262421] w-[800px] max-h-[80vh] rounded-lg shadow-2xl flex flex-col border border-[#3c3a37]">

                {/* Header */}
                <div className="p-4 border-b border-[#3c3a37] flex justify-between items-center bg-[#211f1e] rounded-t-lg">
                    <h2 className="text-lg font-bold text-white">Select a game from Chess.com</h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">✕</button>
                </div>

                {/* Filters */}
                <div className="p-4 flex flex-col gap-4 bg-[#262421]">
                    <div className="flex gap-2">
                        <input
                            type="text"
                            placeholder="Username"
                            className="bg-[#3c3a37] text-white px-3 py-2 rounded flex-1 focus:outline-none focus:ring-2 focus:ring-[#81b64c]"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleFetch()}
                        />

                        <select
                            className="bg-[#3c3a37] text-white px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-[#81b64c]"
                            value={month}
                            onChange={(e) => setMonth(parseInt(e.target.value))}
                        >
                            {months.map((m, i) => (
                                <option key={i} value={i + 1}>{m}</option>
                            ))}
                        </select>

                        <select
                            className="bg-[#3c3a37] text-white px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-[#81b64c]"
                            value={year}
                            onChange={(e) => setYear(parseInt(e.target.value))}
                        >
                            {Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - i).map(y => (
                                <option key={y} value={y}>{y}</option>
                            ))}
                        </select>

                        <select
                            className="bg-[#3c3a37] text-white px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-[#81b64c]"
                            value={filterType}
                            onChange={(e) => setFilterType(e.target.value)}
                        >
                            <option value="all">All Types</option>
                            <option value="rapid">Rapid</option>
                            <option value="blitz">Blitz</option>
                            <option value="bullet">Bullet</option>
                            <option value="daily">Daily</option>
                        </select>

                        <button
                            onClick={handleFetch}
                            disabled={loading}
                            className="bg-[#81b64c] hover:bg-[#a3d160] text-white font-bold px-4 py-2 rounded transition-colors disabled:opacity-50"
                        >
                            {loading ? "..." : "Fetch"}
                        </button>
                    </div>
                    {error && <div className="text-red-400 text-sm">{error}</div>}
                </div>

                {/* Game List */}
                <div className="flex-1 overflow-y-auto p-2 scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-transparent">
                    {filteredGames.length === 0 && !loading && (
                        <div className="text-center text-gray-500 py-10">No games found</div>
                    )}

                    <div className="grid gap-2">
                        {filteredGames.map((game, idx) => {
                            const res = getResultIcon(game, username);
                            const date = new Date(game.end_time * 1000).toLocaleDateString('en-GB', {
                                day: 'numeric', month: 'short', year: 'numeric'
                            });

                            const isWhite = game.white.username.toLowerCase() === username.toLowerCase();
                            const myRating = isWhite ? game.white.rating : game.black.rating;
                            const oppRating = isWhite ? game.black.rating : game.white.rating;
                            const oppName = isWhite ? game.black.username : game.white.username;

                            return (
                                <div
                                    key={idx}
                                    className="flex items-center justify-between p-3 bg-[#302e2b] hover:bg-[#3d3b38] rounded transition-colors group cursor-pointer border border-transparent hover:border-[#4c4a47]"
                                    onClick={() => onSelectGame(game.pgn)}
                                >
                                    <div className="flex items-center gap-4">
                                        <div className="text-2xl w-8 text-center text-[#81b64c] drop-shadow-sm">
                                            {getGameIcon(game.time_class)}
                                        </div>

                                        <div className="flex flex-col text-sm">
                                            <div className="flex items-center gap-2">
                                                <span className="w-3 h-3 rounded-full bg-white border border-gray-500"></span>
                                                <span className="text-white font-medium">{game.white.username}</span>
                                                <span className="text-gray-400">({game.white.rating})</span>
                                            </div>
                                            <div className="flex items-center gap-2 mt-1">
                                                <span className="w-3 h-3 rounded-full bg-black border border-gray-500"></span>
                                                <span className="text-white font-medium">{game.black.username}</span>
                                                <span className="text-gray-400">({game.black.rating})</span>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-4">
                                        <span className="text-gray-400 text-xs font-mono">{date}</span>

                                        <div className={`w-8 h-8 flex items-center justify-center rounded text-white font-bold ${res.bg}`}>
                                            {res.icon}
                                        </div>

                                        <button
                                            className="p-2 bg-[#454341] hover:bg-[#615f5c] text-white rounded transition-colors"
                                            title="Analyze"
                                        >
                                            🔍
                                        </button>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default GameImportModal;
