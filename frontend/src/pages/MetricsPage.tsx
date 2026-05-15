import { useEffect, useMemo, useState } from "react";
import { api, type Dataset, type MetricDef } from "../api";

const AGGS = ["SUM", "AVG", "COUNT", "MIN", "MAX"] as const;

export default function MetricsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [metrics, setMetrics] = useState<MetricDef[]>([]);
  const [showNew, setShowNew] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const reload = async () => {
    setDatasets(await api.datasets());
    setMetrics(await api.metrics());
  };
  useEffect(() => { reload(); }, []);

  const byDataset = useMemo(() => {
    const map: Record<number, MetricDef[]> = {};
    metrics.forEach((m) => { (map[m.dataset_id] ||= []).push(m); });
    return map;
  }, [metrics]);

  const del = async (id: number) => {
    if (!confirm("Удалить метрику?")) return;
    try { await api.metricDelete(id); reload(); }
    catch (e: any) { setErr(String(e)); }
  };

  return (
    <>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <h1 style={{ margin: 0 }}>Метрики</h1>
        <button onClick={() => setShowNew(true)} disabled={!datasets.length}>+ Новая метрика</button>
      </div>

      {err && <div className="err">{err}</div>}

      {datasets.map((d) => (
        <div className="card" key={d.id}>
          <h2 style={{ display: "flex", alignItems: "center", gap: 8 }}>
            {d.name}
            <span className={`pill ${d.kind === "builtin" ? "pill-primary" : "pill-muted"}`}>{d.kind}</span>
          </h2>
          {!byDataset[d.id] ? (
            <p className="muted">— метрик нет —</p>
          ) : (
            <table>
              <thead>
                <tr><th>Имя</th><th>Kind</th><th>Формула</th><th>Описание</th><th></th></tr>
              </thead>
              <tbody>
                {byDataset[d.id].map((m) => (
                  <tr key={m.id}>
                    <td><b>{m.name}</b></td>
                    <td><span className="pill pill-muted">{m.kind}</span></td>
                    <td>
                      {m.kind === "agg" ? (
                        <code>{m.agg}({m.column ?? "*"})</code>
                      ) : (
                        <code style={{ fontSize: 11 }}>{m.sql?.slice(0, 60)}{(m.sql?.length ?? 0) > 60 ? "…" : ""}</code>
                      )}
                    </td>
                    <td className="muted">{m.description}</td>
                    <td style={{ textAlign: "right" }}>
                      <button className="chip" style={{ color: "#991b1b", borderColor: "#fca5a5" }} onClick={() => del(m.id)}>×</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      ))}

      {showNew && <NewMetricModal datasets={datasets} onClose={() => setShowNew(false)} onDone={() => { setShowNew(false); reload(); }} />}
    </>
  );
}

function NewMetricModal({ datasets, onClose, onDone }: { datasets: Dataset[]; onClose: () => void; onDone: () => void }) {
  const [datasetId, setDatasetId] = useState(datasets[0]?.id ?? 0);
  const [name, setName] = useState("");
  const [kind, setKind] = useState<"agg" | "sql">("agg");
  const [agg, setAgg] = useState<(typeof AGGS)[number]>("SUM");
  const [column, setColumn] = useState("");
  const [sql, setSql] = useState("SELECT user_id, SUM(price) AS value FROM pizza_sales\nWHERE date >= {start} AND date < {end}\nGROUP BY user_id");
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const ds = datasets.find((d) => d.id === datasetId);
  const numericCols = ds?.schema_json.value_cols ?? [];

  const submit = async () => {
    if (!name.trim() || !datasetId) { setErr("name + dataset required"); return; }
    setBusy(true); setErr(null);
    try {
      const body: any = { name: name.trim(), dataset_id: datasetId, kind, description };
      if (kind === "agg") { body.agg = agg; body.column = agg === "COUNT" ? null : column; }
      else { body.sql = sql; }
      await api.metricCreate(body);
      onDone();
    } catch (e: any) { setErr(String(e)); }
    finally { setBusy(false); }
  };

  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)",
      display: "flex", justifyContent: "center", alignItems: "center", zIndex: 100,
    }} onClick={onClose}>
      <div className="card" style={{ width: 640, maxHeight: "85vh", overflowY: "auto", margin: 0 }} onClick={(e) => e.stopPropagation()}>
        <h2>Новая метрика</h2>

        <div className="grid">
          <div className="field"><label>Имя</label>
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Revenue per user" />
          </div>
          <div className="field"><label>Датасет</label>
            <select value={datasetId} onChange={(e) => setDatasetId(+e.target.value)}>
              {datasets.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </div>
          <div className="field"><label>Тип</label>
            <select value={kind} onChange={(e) => setKind(e.target.value as any)}>
              <option value="agg">Aggregate (SUM / AVG / COUNT / …)</option>
              <option value="sql">Raw DuckDB SQL</option>
            </select>
          </div>
        </div>

        {kind === "agg" ? (
          <div className="grid" style={{ marginTop: 12 }}>
            <div className="field"><label>Агрегация</label>
              <select value={agg} onChange={(e) => setAgg(e.target.value as any)}>
                {AGGS.map((a) => <option key={a} value={a}>{a}</option>)}
              </select>
            </div>
            {agg !== "COUNT" && (
              <div className="field"><label>Колонка</label>
                <select value={column} onChange={(e) => setColumn(e.target.value)}>
                  <option value="">—</option>
                  {numericCols.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
            )}
          </div>
        ) : (
          <div className="field" style={{ marginTop: 12 }}>
            <label>SQL (должен вернуть колонки <code>user_id</code> и <code>value</code>; используй <code>{"{start}"}</code> / <code>{"{end}"}</code>)</label>
            <textarea rows={6} value={sql} onChange={(e) => setSql(e.target.value)} style={{ fontFamily: "monospace", fontSize: 13 }} />
          </div>
        )}

        <div className="field" style={{ marginTop: 12 }}>
          <label>Описание</label>
          <input value={description} onChange={(e) => setDescription(e.target.value)} />
        </div>

        {err && <div className="err" style={{ marginTop: 12 }}>{err}</div>}

        <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", marginTop: 20 }}>
          <button className="secondary" onClick={onClose}>Отмена</button>
          <button onClick={submit} disabled={busy}>{busy ? "Сохраняю…" : "Создать"}</button>
        </div>
      </div>
    </div>
  );
}
