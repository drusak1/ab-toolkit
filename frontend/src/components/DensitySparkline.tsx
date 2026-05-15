import type { BayesPosterior } from "../api";

export default function DensitySparkline({ post, width = 80, height = 28 }: { post: BayesPosterior; width?: number; height?: number }) {
  const { density_x, density_y, ci_low, ci_high } = post;
  if (!density_x.length) return null;
  const xMin = density_x[0], xMax = density_x[density_x.length - 1];
  const yMax = Math.max(...density_y);
  const range = xMax - xMin || 1;

  const sx = (x: number) => ((x - xMin) / range) * width;
  const sy = (y: number) => height - (y / yMax) * (height - 2) - 1;

  // Build area path
  const pts = density_x.map((x, i) => `${sx(x).toFixed(1)},${sy(density_y[i]).toFixed(1)}`);
  const area = `M${sx(xMin)},${height} L${pts.join(" L")} L${sx(xMax)},${height} Z`;

  // Color by where CI sits relative to zero
  let fill = "#9ca3af"; // grey neutral
  if (ci_low > 0) fill = "#10b981"; // green positive
  else if (ci_high < 0) fill = "#ef4444"; // red negative

  const zeroX = xMin <= 0 && xMax >= 0 ? sx(0) : null;

  return (
    <svg width={width} height={height} style={{ display: "block" }}>
      <path d={area} fill={fill} fillOpacity={0.25} stroke={fill} strokeWidth={1} />
      {zeroX != null && <line x1={zeroX} x2={zeroX} y1={0} y2={height} stroke="#374151" strokeWidth={1} strokeDasharray="2 2" />}
    </svg>
  );
}
