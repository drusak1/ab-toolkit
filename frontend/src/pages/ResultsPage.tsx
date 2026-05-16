import { useEffect, useState } from "react";
import { api, type ExpRun, type Experiment, type MetricRow } from "../api";
import HistogramChart from "../components/Histogram";
import DensitySparkline from "../components/DensitySparkline";
import ForestPlot from "../components/ForestPlot";

function pct(n: number, digits = 2) { return `${(n * 100).toFixed(digits)}%`; }

function MetricRowCells({ r }: { r: MetricRow }) {
  const tone = !r.is_significant ? "" : r.abs_lift > 0 ? "sig-yes" : "sig-no";
  return (
    <tr style={{ background: r.is_primary ? "#fafbff" : undefined }}>
      <td>
        <b>{r.metric_name}</b>
        {r.is_primary && <span className="pill pill-primary" style={{ marginLeft: 8 }}>PRIMARY</span>}
      </td>
      <td>{r.mean_a.toFixed(2)} <span className="muted">({r.n_a.toLocaleString()})</span></td>
      <td>{r.mean_b.toFixed(2)} <span className="muted">({r.n_b.toLocaleString()})</span></td>
      <td className={tone}><b>{r.abs_lift >= 0 ? "+" : ""}{r.abs_lift.toFixed(2)}</b></td>
      <td className={tone}><b>{r.rel_lift >= 0 ? "+" : ""}{pct(r.rel_lift)}</b></td>
      <td className="muted">[{r.ci_low.toFixed(2)}, {r.ci_high.toFixed(2)}]</td>
      <td className={tone}>{r.pvalue.toFixed(4)}</td>
      <td><DensitySparkline post={r.posterior} /></td>
      <td className="muted">{pct(r.posterior.chance_to_win, 1)}</td>
    </tr>
  );
}

export default function ResultsPage() {
  const [list, setList] = useState<Experiment[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [run, setRun] = useState<ExpRun | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const reload = () => api.expList().then((l) => { setList(l); if (l.length && selected == null) setSelected(l[0].id); });
  useEffect(() => { reload(); }, []);

  const submit = async () => {
    if (selected == null) return;
    setErr(null); setLoading(true); setRun(null);
    try { setRun(await api.expRun(selected)); }
    catch (e: any) { setErr(String(e)); }
    finally { setLoading(false); }
  };

  const remove = async () => {
    if (selected == null) return;
    if (!confirm("Удалить эксперимент?")) return;
    await api.expDelete(selected);
    setSelected(null); setRun(null); reload();
  };

  const primary = run?.metrics.find((m) => m.is_primary);
  const summaryClass = run && primary
    ? (primary.is_significant ? (primary.abs_lift > 0 ? "success" : "danger") : "")
    : "";

  return (
    <>
      <h1>Результаты</h1>

      <div className="card">
        <div style={{ display: "flex", gap: 12, alignItems: "end" }}>
          <div className="field" style={{ flex: 1 }}>
            <label>Эксперимент</label>
            <select value={selected ?? ""} onChange={(e) => setSelected(+e.target.value)}>
              <option value="">— выбрать —</option>
              {list.map((e) => <option key={e.id} value={e.id}>{e.name} (#{e.id})</option>)}
            </select>
          </div>
          <button onClick={submit} disabled={loading || selected == null}>{loading ? "Считаю…" : "Запустить анализ"}</button>
          {selected != null && <button className="secondary" onClick={remove}>Удалить</button>}
        </div>
      </div>

      {err && <div className="err">{err}</div>}

      {run && (
        <>
          <div className={`banner ${summaryClass}`}>
            <div className="banner-title">{run.summary}</div>
          </div>

          <div className={`banner ${run.srm.is_healthy ? "success" : "danger"}`} style={{ padding: "12px 16px" }}>
            <div style={{ display: "flex", gap: 16, alignItems: "center", flexWrap: "wrap" }}>
              <span className={`pill ${run.srm.is_healthy ? "pill-green" : "pill-red"}`}>
                {run.srm.is_healthy ? "✓ Health OK" : "⚠ SRM"}
              </span>
              <span className="muted">A: {run.srm.observed[0].toLocaleString()} / B: {run.srm.observed[1].toLocaleString()}</span>
              <span className="muted">χ² = {run.srm.chi2.toFixed(2)}, p = {run.srm.pvalue.toFixed(4)}</span>
            </div>
          </div>

          <div className="card">
            <h2>Метрики</h2>
            <div style={{ overflowX: "auto" }}>
              <table>
                <thead>
                  <tr>
                    <th>Метрика</th>
                    <th>Control</th>
                    <th>Variant</th>
                    <th>Abs lift</th>
                    <th>Rel lift</th>
                    <th>95% CI</th>
                    <th>p-value</th>
                    <th style={{ width: 90 }}>posterior</th>
                    <th>P(B&gt;A)</th>
                  </tr>
                </thead>
                <tbody>
                  {run.metrics.map((m) => <MetricRowCells key={m.metric_id} r={m} />)}
                </tbody>
              </table>
            </div>
          </div>

          <div className="card">
            <h2>Forest plot — Δ (mean_B − mean_A)</h2>
            <ForestPlot rows={run.metrics} />
          </div>

          <div className="card">
            <h2>Распределение primary метрики</h2>
            <HistogramChart
              series={[
                { name: "group A", color: "#6366f1", data: run.histogram_a },
                { name: "group B", color: "#f59e0b", data: run.histogram_b },
              ]}
              height={320}
            />
          </div>

          <details className="card">
            <summary style={{ fontWeight: 600 }}>Параметры эксперимента</summary>
            <table style={{ marginTop: 16 }}>
              <tbody>
                <tr><td className="muted">Название</td><td><b>{run.experiment.name}</b></td></tr>
                <tr><td className="muted">Dataset ID</td><td>#{run.experiment.dataset_id}</td></tr>
                <tr><td className="muted">Primary metric ID</td><td>#{run.experiment.primary_metric_id}</td></tr>
                <tr><td className="muted">Secondary metrics</td><td>{run.experiment.secondary_metric_ids.length ? run.experiment.secondary_metric_ids.map((id) => `#${id}`).join(", ") : "—"}</td></tr>
                <tr><td className="muted">Период</td><td>{run.experiment.start_date.slice(0,10)} → {run.experiment.end_date.slice(0,10)}</td></tr>
                <tr><td className="muted">Stat. test</td><td>{run.experiment.stat_test}{run.experiment.cuped ? " + CUPED" : ""}{run.experiment.stratification ? ` + stratified (${run.experiment.strat_column})` : ""}</td></tr>
                <tr><td className="muted">α / β</td><td>{run.experiment.alpha} / {run.experiment.beta}</td></tr>
                <tr><td className="muted">Buckets</td><td>{run.experiment.n_buckets}</td></tr>
                <tr><td className="muted">Соль</td><td><code>{run.experiment.salt}</code></td></tr>
                <tr><td className="muted">Создан</td><td className="muted">{run.experiment.created_at.slice(0, 19).replace("T", " ")}</td></tr>
              </tbody>
            </table>
          </details>
        </>
      )}
    </>
  );
}
