import { useEffect, useMemo, useState } from "react";
import { api, type Dataset, type DurationCalc, type MetricDef } from "../api";

export default function DesignPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [metrics, setMetrics] = useState<MetricDef[]>([]);
  const [datasetId, setDatasetId] = useState<number | null>(null);
  const [metricId, setMetricId] = useState<number | null>(null);
  const [preStart, setPreStart] = useState("2022-03-01");
  const [preEnd, setPreEnd] = useState("2022-03-15");
  const [mdePct, setMdePct] = useState(3);
  const [alpha, setAlpha] = useState(0.05);
  const [beta, setBeta] = useState(0.1);
  const [dailyUsers, setDailyUsers] = useState<number | "">("");
  const [calc, setCalc] = useState<DurationCalc | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    Promise.all([api.datasets(), api.metrics()]).then(([d, m]) => {
      setDatasets(d); setMetrics(m);
      if (d.length && datasetId == null) setDatasetId(d[0].id);
    });
  }, []);

  const availableMetrics = useMemo(
    () => metrics.filter((m) => m.dataset_id === datasetId),
    [metrics, datasetId]
  );

  useEffect(() => {
    if (availableMetrics.length && (metricId == null || !availableMetrics.find((m) => m.id === metricId))) {
      setMetricId(availableMetrics[0].id);
    }
  }, [availableMetrics, metricId]);

  const submit = async () => {
    if (datasetId == null || metricId == null) { setErr("выбери датасет и метрику"); return; }
    setErr(null); setLoading(true);
    try {
      const r = await api.duration({
        dataset_id: datasetId,
        metric_id: metricId,
        pre_start: new Date(preStart).toISOString(),
        pre_end: new Date(preEnd).toISOString(),
        mde_pct: mdePct, alpha, beta,
        daily_users: dailyUsers === "" ? null : dailyUsers,
      });
      setCalc(r);
    } catch (e: any) { setErr(String(e)); }
    finally { setLoading(false); }
  };

  useEffect(() => {
    if (!calc) return;
    const t = setTimeout(submit, 300);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mdePct, alpha, beta, dailyUsers]);

  const daysClass = calc ? (calc.days_required <= 14 ? "green" : calc.days_required <= 30 ? "amber" : "red") : "";

  return (
    <>
      <h1>Дизайн эксперимента</h1>

      <div className="card">
        <h2>Pre-period</h2>
        <p className="muted" style={{ marginTop: 0 }}>Историческое окно для оценки baseline mean / std.</p>
        <div className="grid">
          <div className="field"><label>Датасет</label>
            <select value={datasetId ?? ""} onChange={(e) => setDatasetId(+e.target.value)}>
              <option value="">—</option>
              {datasets.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </div>
          <div className="field"><label>Метрика</label>
            <select value={metricId ?? ""} onChange={(e) => setMetricId(+e.target.value)} disabled={!availableMetrics.length}>
              <option value="">—</option>
              {availableMetrics.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
            </select>
          </div>
          <div className="field"><label>Начало</label>
            <input type="date" value={preStart} onChange={(e) => setPreStart(e.target.value)} />
          </div>
          <div className="field"><label>Конец</label>
            <input type="date" value={preEnd} onChange={(e) => setPreEnd(e.target.value)} />
          </div>
        </div>
        <button onClick={submit} disabled={loading || datasetId == null || metricId == null} style={{ marginTop: 16 }}>
          {loading ? "Считаю…" : "Загрузить данные"}
        </button>
        {err && <div className="err" style={{ marginTop: 12 }}>{err}</div>}
      </div>

      {calc && (
        <>
          <div className="card">
            <h2>Оценка длительности эксперимента</h2>
            <p className="muted" style={{ marginTop: 0 }}>Двигай MDE / α / β — пересчёт автоматический.</p>

            <div className="kpi-row" style={{ marginTop: 20, marginBottom: 28 }}>
              <div className="kpi">
                <div className="kpi-value">{calc.n_per_group.toLocaleString()}</div>
                <div className="kpi-label">users / group</div>
              </div>
              <div className="kpi">
                <div className="kpi-value">{calc.n_total.toLocaleString()}</div>
                <div className="kpi-label">total users</div>
              </div>
              <div className="kpi">
                <div className={`kpi-value ${daysClass}`}>{calc.days_required.toFixed(1)}</div>
                <div className="kpi-label">days @ {calc.daily_users.toLocaleString()} DAU</div>
              </div>
            </div>

            <div className="grid" style={{ gridTemplateColumns: "2fr 1fr 1fr 1fr" }}>
              <div className="field">
                <label>MDE, % (минимально детектируемый эффект)</label>
                <input type="number" step="0.1" value={mdePct} onChange={(e) => setMdePct(+e.target.value)} style={{ fontSize: 20, fontWeight: 600 }} />
                <input type="range" min={0.1} max={20} step={0.1} value={mdePct} onChange={(e) => setMdePct(+e.target.value)} />
              </div>
              <div className="field"><label>α (FPR)</label>
                <input type="number" step="0.01" value={alpha} onChange={(e) => setAlpha(+e.target.value)} />
              </div>
              <div className="field"><label>β (1 − power)</label>
                <input type="number" step="0.01" value={beta} onChange={(e) => setBeta(+e.target.value)} />
              </div>
              <div className="field"><label>Daily users (override)</label>
                <input type="number" placeholder={`auto: ${calc.daily_users}`} value={dailyUsers} onChange={(e) => setDailyUsers(e.target.value === "" ? "" : +e.target.value)} />
              </div>
            </div>
          </div>

          <div className="card">
            <h2>Pre-period stats</h2>
            <table>
              <tbody>
                <tr><td className="muted">Mean</td><td><b>{calc.mean.toFixed(2)}</b></td></tr>
                <tr><td className="muted">Std</td><td><b>{calc.std.toFixed(2)}</b></td></tr>
                <tr><td className="muted">MDE absolute</td><td><b>{calc.mde_abs.toFixed(2)}</b> ({mdePct}% от mean)</td></tr>
                <tr><td className="muted">Daily users (из данных)</td><td><b>{calc.daily_users.toLocaleString()}</b></td></tr>
              </tbody>
            </table>
          </div>
        </>
      )}
    </>
  );
}
