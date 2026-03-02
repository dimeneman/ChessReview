import { CUSTOM_PIECES } from "./CustomPieces";

export default function AccuracyPanel({ white, black, theme }) {
  // Use theme color if available, else fallback to default green
  const bgColor = theme ? theme.dark : "#769656";
  const borderColor = "transparent"; // Or derive from theme if needed

  return (
    <div>
      <h4 className="text-sm font-bold mb-3 text-gray-300">Accuracy</h4>
      <div className="grid grid-cols-2 gap-3">
        {/* White */}
        <div
          className="rounded p-3 text-center border-2 border-white/10 shadow-md transition-colors duration-300"
          style={{ backgroundColor: bgColor, borderColor: "rgba(255,255,255,0.1)" }}
        >
          <div className="flex items-center justify-center mb-1">
            <div className="w-10 h-10 flex items-center justify-center">
              <CUSTOM_PIECES.wK squareWidth="40px" />
            </div>
          </div>
          <div className="text-white/80 text-xs uppercase font-bold mb-1">White</div>
          <div className="text-2xl font-black text-white drop-shadow-sm">
            {white}<span className="text-sm font-normal text-white/80 ml-0.5">%</span>
          </div>
        </div>

        {/* Black */}
        <div
          className="rounded p-3 text-center border-2 border-white/10 shadow-md transition-colors duration-300"
          style={{ backgroundColor: bgColor, borderColor: "rgba(255,255,255,0.1)" }}
        >
          <div className="flex items-center justify-center mb-1">
            <div className="w-10 h-10 flex items-center justify-center">
              <CUSTOM_PIECES.bK squareWidth="40px" />
            </div>
          </div>
          <div className="text-white/80 text-xs uppercase font-bold mb-1">Black</div>
          <div className="text-2xl font-black text-white drop-shadow-sm">
            {black}<span className="text-sm font-normal text-white/80 ml-0.5">%</span>
          </div>
        </div>
      </div>
    </div>
  );
}
