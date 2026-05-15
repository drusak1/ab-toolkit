import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Histogram } from "../api";

type Series = { name: string; color: string; data: Histogram };

export default function HistogramChart({ series, height = 280 }: { series: Series[]; height?: number }) {
  if (!series.length) return null;
  const ref = series[0].data;
  const data = ref.counts.map((_, i) => {
    const row: any = { x: ((ref.bins[i] + ref.bins[i + 1]) / 2).toFixed(1) };
    series.forEach((s) => (row[s.name] = s.data.counts[i] ?? 0));
    return row;
  });
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis dataKey="x" tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip />
        <Legend />
        {series.map((s) => (
          <Bar key={s.name} dataKey={s.name} fill={s.color} fillOpacity={0.7} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
