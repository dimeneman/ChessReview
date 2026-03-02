import { AreaChart, Area, XAxis, YAxis, ResponsiveContainer, ReferenceLine, Tooltip } from "recharts";
import { getClassificationStyle } from "../utils/moveClassifications";

const CustomDot = (props) => {
  const { cx, cy, payload } = props;

  if (!payload || !payload.move || !payload.move.label) return null;

  const style = getClassificationStyle(payload.move.label);

  if (!style || !style.color) return null;

  return (
    <circle cx={cx} cy={cy} r={3} fill={style.color} stroke="none" />
  );
};

export default function EvalGraph({ data, moves }) {
  if (!data) return null;

  const chartData = data.map((v, i) => {
    return {
      ply: i + 1,
      eval: v,
      move: moves && moves[i] ? moves[i] : null
    };
  });

  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={chartData} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
        <XAxis dataKey="ply" hide />
        <YAxis domain={[-1, 1]} hide />

        <ReferenceLine y={0} stroke="#4a4845" strokeWidth={1} />

        <Area
          type="monotone"
          dataKey="eval"
          stroke="#ffffff"
          strokeWidth={2}
          fill="#ffffff"
          fillOpacity={1}
          baseValue={-1}
          dot={<CustomDot />}
          isAnimationActive={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
