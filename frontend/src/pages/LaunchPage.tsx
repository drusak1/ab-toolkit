import { useEffect, useMemo, useState } from "react";
import { api, type Dataset, type MetricDef } from "../api";

const TESTS = ["ttest", "welch", "mann_whitney", "bootstrap"] as const;

export default function LaunchPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [metrics, setMetrics] = useState<MetricDef[]>([]);
  const [form, setForm] = useState({
    name: "",
    dataset_id: 0,
    primary_metric_id: 0,
    secondary_metric_ids: [] as number[],
    start_date: "2022-03-21",
    end_date: "2022-03-28",
    alpha: 0.05,
    beta: 0.1,
    mde_pct: 1.0,
    stratification: false,
    strat_column: "",
    cuped: false,
    n_buckets: 10,
    stat_test: "ttest" as (typeof TESTS)[number],
  });
  const [created, setCreated] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.datasets(), api.metrics()]).then(([d, m]) => {
      setDatasets(d); setMetrics(m);
      if (d.length) {
        const did = d[0].id;
        const firstMetric = m.find((mm) => mm.dataset_id === did);
        setForm((f) => ({ ...f, dataset_id: did, primary_metric_id: firstMetric?.id ?? 0 }));
      }
    });
  }, []);

  const availableMetrics = useMemo(
    () => metrics.filter((m) => m.dataset_id === form.dataset_id),
    [metrics, form.dataset_id]
  );

  const dimCols = useMemo(
    () => datasets.find((d) => d.id === form.dataset_id)?.schema_json.dim_cols ?? [],
    [datasets, form.dataset_id]
  );

  const update = (k: string, v: any) => setForm((f) => ({ ...f, [k]: v }));

  const onDatasetChange = (did: number) => {
    const first = metrics.find((m) => m.dataset_id === did);
    setForm((f) => ({
      ...f,
      dataset_id: did,
      primary_metric_id: first?.id ?? 0,
      secondary_metric_ids: [],
    }));
  };

  const toggleSecondary = (mid: number) => {
    setForm((f) => ({
      ...f,
      secondary_metric_ids: f.secondary_metric_ids.includes(mid)
        ? f.secondary_metric_ids.filter((x) => x !== mid)
        : [...f.secondary_metric_ids, mid],
    }));
  };

  const submit = async () => {
    setErr(null);
    if (!form.name.trim()) { setErr("укажи название"); return; }
    if (!form.dataset_id || !form.primary_metric_id) { setErr("выбери датасет и primary metric"); return; }
    try {
      const exp = await api.expCreate({
        ...form,
        strat_column: form.stratification && form.strat_column ? form.strat_column : null,
        start_date: new Date(form.start_date).toISOString(),
        end_date: new Date(form.end_date).toISOString(),
      });
      setCreated(exp);
    } catch (e: any) { setErr(String(e)); }
  };

  return (
    <>
      <h1>Запуск эксперимента</h1>

      <div className="card">
        <div className="grid">
          <div className="field" style={{ gridColumn: "1 / -1" }}>
            <label>Название</label>
            <input value={form.name} onChange={(e) => update("name", e.target.value)} placeholder="e.g. Header redesign A/B" />
          </div>
          <div className="field"><label>Датасет</label>
            <select value={form.dataset_id} onChange={(e) => onDatasetChange(+e.target.value)}>
              {datasets.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </div>
          <div className="field"><label>Primary метрика</label>
            <select value={form.primary_metric_id} onChange={(e) => update("primary_metric_id", +e.target.value)}>
              <option value={0}>—</option>
              {availableMetrics.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
            </select>
          </div>
          <div className="field"><label>Stat test</label>
            <select value={form.stat_test} onChange={(e) => update("stat_test", e.target.value)}>
              {TESTS.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div className="field"><label>Дата начала</label>
            <input type="date" value={form.start_date} onChange={(e) => update("start_date", e.target.value)} />
          </div>
          <div className="field"><label>Дата окончания</label>
            <input type="date" value={form.end_date} onChange={(e) => update("end_date", e.target.value)} />
          </div>
          <div className="field"><label>Стратификация</label>
            <select value={String(form.stratification)} onChange={(e) => update("stratification", e.target.value === "true")}>
              <option value="false">off</option><option value="true">on</option>
            </select>
          </div>
          {form.stratification && (
            <div className="field"><label>Strat column</label>
              <select value={form.strat_column} onChange={(e) => update("strat_column", e.target.value)}>
                <option value="">—</option>
                {dimCols.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          )}
          <div className="field"><label>CUPED</label>
            <select value={String(form.cuped)} onChange={(e) => update("cuped", e.target.value === "true")}>
              <option value="false">off</option><option value="true">on</option>
            </select>
          </div>
          <div className="field"><label>Alpha</label>
            <input type="number" step="0.01" value={form.alpha} onChange={(e) => update("alpha", +e.target.value)} />
          </div>
          <div className="field"><label>Beta</label>
            <input type="number" step="0.01" value={form.beta} onChange={(e) => update("beta", +e.target.value)} />
          </div>
          <div className="field"><label>MDE, %</label>
            <input type="number" step="0.1" value={form.mde_pct} onChange={(e) => update("mde_pct", +e.target.value)} />
          </div>
          <div className="field"><label>Buckets</label>
            <input type="number" value={form.n_buckets} onChange={(e) => update("n_buckets", +e.target.value)} />
          </div>
        </div>

        {availableMetrics.length > 1 && (
          <div style={{ marginTop: 16 }}>
            <label style={{ fontSize: 12, color: "#4b5563", fontWeight: 500 }}>Secondary метрики (отслеживать + отображать в результатах)</label>
            <div className="check-list" style={{ marginTop: 8 }}>
              {availableMetrics.filter((m) => m.id !== form.primary_metric_id).map((m) => (
                <label key={m.id}>
                  <input
                    type="checkbox"
                    checked={form.secondary_metric_ids.includes(m.id)}
                    onChange={() => toggleSecondary(m.id)}
                    style={{ width: "auto", padding: 0 }}
                  />
                  {m.name}
                </label>
              ))}
            </div>
          </div>
        )}

        <button onClick={submit} style={{ marginTop: 20 }}>Создать эксперимент</button>
      </div>

      {err && <div className="err">{err}</div>}

      {created && (
        <div className="banner success">
          <div className="banner-title">✓ Эксперимент сохранён</div>
          <div className="muted" style={{ marginTop: 8 }}>
            ID: <b>{created.id}</b> · соль: <code>{created.salt}</code> · primary metric ID: {created.primary_metric_id}
          </div>
          <p style={{ marginTop: 12, marginBottom: 0 }}>Перейди на <b>Результаты</b> чтобы запустить анализ.</p>
        </div>
      )}
    </>
  );
}
