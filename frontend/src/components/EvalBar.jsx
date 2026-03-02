export default function EvalBar({ value }) {
  // value is between -1 and +1
  const percent = ((value + 1) / 2) * 100;

  return (
    <div className="w-4 h-[420px] bg-black rounded overflow-hidden flex flex-col">
      <div
        className="bg-white transition-all duration-300"
        style={{ height: `${percent}%` }}
      />
    </div>
  );
}
