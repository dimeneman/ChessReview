import React from 'react';

const AnalysisLoader = ({ progress }) => {
    const percent = progress?.percent || 0;

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 backdrop-blur-sm">
            <div className="bg-[#262421] p-6 rounded-lg shadow-xl w-[500px] border border-[#3c3a37] animate-fade-in">
                <div className="flex justify-between items-center mb-2">
                    <h3 className="text-xl font-bold text-white">Evaluating...</h3>
                    <span className="text-xl font-bold text-white">{percent}%</span>
                </div>

                <div className="w-full bg-gray-600 rounded-full h-2.5 mb-4 overflow-hidden">
                    <div
                        className="bg-blue-500 h-2.5 rounded-full transition-all duration-300 ease-out shadow-[0_0_10px_rgba(59,130,246,0.5)]"
                        style={{ width: `${percent}%` }}
                    ></div>
                </div>

                <p className="text-gray-400 text-sm">
                    If this takes a while, you can try lowering the engine depth in the settings.
                </p>
                {progress?.cur_move && (
                    <p className="text-gray-500 text-xs mt-2 font-mono">
                        Analyzing: {progress.cur_move} (Ply {progress.ply})
                    </p>
                )}
            </div>
        </div>
    );
};

export default AnalysisLoader;
