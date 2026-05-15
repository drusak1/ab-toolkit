import type { MetricRow } from "../api";

export default function ForestPlot({ rows, width = 700, rowHeight = 36 }: { rows: MetricRow[]; width?: number; rowHeight?: number }) {
  if (!rows.length) return null;
  const allLow = Math.min(...rows.map((r) => r.ci_low));
  const allHigh = Math.max(...rows.map((r) => r.ci_high));
  const pad = (allHigh - allLow) * 0.1 || 1;
  const xMin = Math.min(allLow - pad, -pad);
  const xMax = Math.max(allHigh + pad, pad);
  const range = xMax - xMin;

  const labelW = 200;
  const plotW = width - labelW - 16;
  const height = rows.length * rowHeight + 30;
  const sx = (v: number) => labelW + ((v - xMin) / range) * plotW;
  const zeroX = sx(0);

  return (
    <svg width={width} height={height} style={{ display: "block" }}>
      {/* Zero line */}
      <line x1={zeroX} x2={zeroX} y1={10} y2={height - 20} stroke="#9ca3af" strokeWidth={1} strokeDasharray="3 3" />
      {/* X axis labels */}
      <text x={labelW} y={height - 4} fontSize={10} fill="#6b7280">{xMin.toFixed(2)}</text>
      <text x={width - 4} y={height - 4} fontSize={10} fill="#6b7280" textAnchor="end">{xMax.toFixed(2)}</text>
      <text x={zeroX} y={height - 4} fontSize={10} fill="#6b7280" textAnchor="middle">0</text>

      {rows.map((r, i) => {
        const y = 20 + i * rowHeight;
        const x1 = sx(r.ci_low);
        const x2 = sx(r.ci_high);
        const xMid = sx(r.abs_lift);
        let color = "#6b7280";
        if (r.is_significant) color = r.abs_lift > 0 ? "#10b981" : "#ef4444";
        return (
          <g key={r.metric_id}>
            <text x={labelW - 8} y={y + 5} fontSize={12} fill="#374151" textAnchor="end">
              {r.metric_name}{r.is_primary ? " *" : ""}
            </text>
            <line x1={x1} x2={x2} y1={y} y2={y} stroke={color} strokeWidth={2} />
            <line x1={x1} x2={x1} y1={y - 4} y2={y + 4} stroke={color} strokeWidth={2} />
            <line x1={x2} x2={x2} y1={y - 4} y2={y + 4} stroke={color} strokeWidth={2} />
            <circle cx={xMid} cy={y} r={4} fill={color} />
          </g>
        );
      })}
    </svg>
  );
}
