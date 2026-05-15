import { useEffect, useState } from "react";
import { api, type Dataset, type Experiment, type MetricDef } from "../api";

export default function HomePage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [metrics, setMetrics] = useState<MetricDef[]>([]);
  const [exps, setExps] = useState<Experiment[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.datasets(), api.metrics(), api.expList()])
      .then(([d, m, e]) => { setDatasets(d); setMetrics(m); setExps(e); })
      .catch((er) => setErr(String(er)));
  }, []);

  return (
    <>
      <h1>Главная</h1>
      <div className="card">
        <p className="muted" style={{ margin: 0 }}>
          AB Calc — обобщённая платформа AB-тестов. Загружай CSV/Parquet, определяй метрики (агрегации или DuckDB SQL),
          запускай эксперименты, читай результаты. Pizza dataset из Karpov sim_ab подключён как preset.
        </p>
      </div>

      {err && <div className="err">{err}</div>}

      <div className="split-summary">
        <div className="card">
          <h2>📦 Источники</h2>
          <div style={{ fontSize: 36, fontWeight: 700, color: "var(--accent)" }}>{datasets.length}</div>
          <p className="muted" style={{ marginBottom: 0 }}>зарегистрированных датасетов</p>
        </div>
        <div className="card">
          <h2>📊 Метрики</h2>
          <div style={{ fontSize: 36, fontWeight: 700, color: "var(--accent)" }}>{metrics.length}</div>
          <p className="muted" style={{ marginBottom: 0 }}>определений метрик</p>
        </div>
      </div>

      <div className="card">
        <h2>🚀 Последние эксперименты</h2>
        {exps.length === 0 ? (
          <p className="muted">Эксперименты не создавались. Перейди на <b>Запуск</b>.</p>
        ) : (
          <table>
            <thead><tr><th>Имя</th><th>Dataset</th><th>Period</th><th>Test</th><th>Создан</th></tr></thead>
            <tbody>
              {exps.slice(0, 8).map((e) => {
                const ds = datasets.find((d) => d.id === e.dataset_id);
                return (
                  <tr key={e.id}>
                    <td><b>{e.name}</b></td>
                    <td>{ds?.name ?? `#${e.dataset_id}`}</td>
                    <td className="muted">{e.start_date.slice(0,10)} → {e.end_date.slice(0,10)}</td>
                    <td><span className="pill pill-muted">{e.stat_test}{e.cuped ? " +CUPED" : ""}</span></td>
                    <td className="muted">{e.created_at.slice(0,16).replace("T", " ")}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      <div className="card">
        <h2>Воркфлоу</h2>
        <ol style={{ margin: 0, paddingLeft: 20 }}>
          <li><b>Источники</b> → загрузи CSV/Parquet (или используй preset)</li>
          <li><b>Метрики</b> → определи метрики на датасете (агрегация или SQL)</li>
          <li><b>Дизайн</b> → подбери MDE / α / β / длительность по pre-period</li>
          <li><b>Запуск</b> → создай эксперимент с primary + secondary метриками, сгенерируется соль</li>
          <li><b>Результаты</b> → запусти анализ: SRM check, Bayes posterior, forest plot, гистограммы A/B</li>
        </ol>
      </div>
    </>
  );
}
