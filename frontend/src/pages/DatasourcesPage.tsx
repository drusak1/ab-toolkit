import { useEffect, useState } from "react";
import { api, type Dataset, type SchemaSuggestion } from "../api";

export default function DatasourcesPage() {
  const [list, setList] = useState<Dataset[]>([]);
  const [showUpload, setShowUpload] = useState(false);
  const [previewOf, setPreviewOf] = useState<number | null>(null);
  const [previewRows, setPreviewRows] = useState<any[]>([]);
  const [err, setErr] = useState<string | null>(null);

  const reload = () => api.datasets().then(setList);
  useEffect(() => { reload(); }, []);

  useEffect(() => {
    if (previewOf == null) { setPreviewRows([]); return; }
    api.datasetPreview(previewOf, 10).then(setPreviewRows).catch((e) => setErr(String(e)));
  }, [previewOf]);

  const del = async (id: number) => {
    if (!confirm("Удалить датасет? (метрики и эксперименты, использующие его, сломаются)")) return;
    try { await api.datasetDelete(id); reload(); }
    catch (e: any) { setErr(String(e)); }
  };

  return (
    <>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <h1 style={{ margin: 0 }}>Источники</h1>
        <button onClick={() => setShowUpload(true)}>+ Загрузить датасет</button>
      </div>

      {err && <div className="err">{err}</div>}

      <div className="card">
        <table>
          <thead>
            <tr><th>Имя</th><th>Kind</th><th>user_col</th><th>date_col</th><th>Колонки</th><th></th></tr>
          </thead>
          <tbody>
            {list.map((d) => (
              <tr key={d.id}>
                <td>
                  <b>{d.name}</b>
                  <div className="muted" style={{ fontSize: 12 }}>{d.description}</div>
                </td>
                <td>
                  <span className={`pill ${d.kind === "builtin" ? "pill-primary" : "pill-muted"}`}>{d.kind}</span>
                </td>
                <td><code>{d.user_col}</code></td>
                <td><code>{d.date_col ?? "—"}</code></td>
                <td className="muted">{d.schema_json.all_cols.length} cols</td>
                <td style={{ textAlign: "right" }}>
                  <button className="chip" onClick={() => setPreviewOf(previewOf === d.id ? null : d.id)}>
                    {previewOf === d.id ? "Скрыть" : "Preview"}
                  </button>
                  {d.kind !== "builtin" && (
                    <button className="chip" style={{ marginLeft: 6, color: "#991b1b", borderColor: "#fca5a5" }} onClick={() => del(d.id)}>×</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {previewOf != null && !!previewRows.length && (
        <div className="card" style={{ overflowX: "auto" }}>
          <h2>Preview: {list.find((d) => d.id === previewOf)?.name}</h2>
          <table>
            <thead><tr>{Object.keys(previewRows[0]).map((c) => <th key={c}>{c}</th>)}</tr></thead>
            <tbody>
              {previewRows.map((r, i) => (
                <tr key={i}>{Object.keys(r).map((c) => <td key={c}>{String(r[c])}</td>)}</tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showUpload && <UploadModal onClose={() => setShowUpload(false)} onDone={() => { setShowUpload(false); reload(); }} />}
    </>
  );
}

function UploadModal({ onClose, onDone }: { onClose: () => void; onDone: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [schema, setSchema] = useState<SchemaSuggestion | null>(null);
  const [name, setName] = useState("");
  const [userCol, setUserCol] = useState("");
  const [dateCol, setDateCol] = useState("");
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const pick = async (f: File) => {
    setFile(f); setErr(null); setBusy(true);
    try {
      const s = await api.datasetDetect(f);
      setSchema(s);
      if (s.user_col) setUserCol(s.user_col);
      if (s.date_col) setDateCol(s.date_col);
      if (!name) setName(f.name.replace(/\.(csv|parquet)$/i, "").slice(0, 40));
    } catch (e: any) { setErr(String(e)); }
    finally { setBusy(false); }
  };

  const submit = async () => {
    if (!file || !name.trim() || !userCol) { setErr("file + name + user_col required"); return; }
    setBusy(true); setErr(null);
    try {
      await api.datasetUpload(file, { name: name.trim(), user_col: userCol, date_col: dateCol, description });
      onDone();
    } catch (e: any) { setErr(String(e)); }
    finally { setBusy(false); }
  };

  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)",
      display: "flex", justifyContent: "center", alignItems: "center", zIndex: 100,
    }} onClick={onClose}>
      <div className="card" style={{ width: 560, maxHeight: "85vh", overflowY: "auto", margin: 0 }} onClick={(e) => e.stopPropagation()}>
        <h2>Загрузка датасета (CSV / Parquet)</h2>
        <input type="file" accept=".csv,.parquet" onChange={(e) => e.target.files?.[0] && pick(e.target.files[0])} />

        {err && <div className="err" style={{ marginTop: 12 }}>{err}</div>}

        {schema && (
          <>
            <div className="muted" style={{ marginTop: 12, fontSize: 13 }}>
              Найдено колонок: <b>{schema.all_cols.length}</b> · numeric: {schema.value_cols.length} · dims: {schema.dim_cols.length}
            </div>
            <div className="grid" style={{ marginTop: 12 }}>
              <div className="field"><label>Имя датасета</label>
                <input value={name} onChange={(e) => setName(e.target.value)} />
              </div>
              <div className="field"><label>user_col</label>
                <select value={userCol} onChange={(e) => setUserCol(e.target.value)}>
                  <option value="">—</option>
                  {schema.all_cols.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div className="field"><label>date_col (опционально)</label>
                <select value={dateCol} onChange={(e) => setDateCol(e.target.value)}>
                  <option value="">—</option>
                  {schema.all_cols.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
            </div>
            <div className="field" style={{ marginTop: 12 }}>
              <label>Описание</label>
              <input value={description} onChange={(e) => setDescription(e.target.value)} />
            </div>
          </>
        )}

        <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", marginTop: 20 }}>
          <button className="secondary" onClick={onClose}>Отмена</button>
          <button onClick={submit} disabled={!schema || busy}>{busy ? "Загружаю…" : "Загрузить"}</button>
        </div>
      </div>
    </div>
  );
}
