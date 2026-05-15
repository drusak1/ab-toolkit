const BASE = "/api";

async function call<T>(path: string, method: string, body?: object): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!r.ok) throw new Error((await r.text()) || `${r.status}`);
  return r.json();
}

async function upload<T>(path: string, file: File, params: Record<string, string>): Promise<T> {
  const qs = new URLSearchParams(params).toString();
  const fd = new FormData();
  fd.append("file", file);
  const r = await fetch(`${BASE}${path}${qs ? "?" + qs : ""}`, { method: "POST", body: fd });
  if (!r.ok) throw new Error((await r.text()) || `${r.status}`);
  return r.json();
}

export type Dataset = {
  id: number;
  name: string;
  kind: string;
  file_path: string;
  user_col: string;
  date_col: string | null;
  description: string;
  schema_json: {
    user_col: string | null;
    date_col: string | null;
    value_cols: string[];
    dim_cols: string[];
    all_cols: string[];
    dtypes: Record<string, string>;
  };
  created_at: string;
};

export type SchemaSuggestion = Dataset["schema_json"];

export type MetricDef = {
  id: number;
  name: string;
  dataset_id: number;
  kind: "agg" | "sql";
  agg: string | null;
  column: string | null;
  sql: string | null;
  description: string;
  created_at: string;
};

export type Experiment = {
  id: number;
  name: string;
  dataset_id: number;
  primary_metric_id: number;
  secondary_metric_ids: number[];
  start_date: string;
  end_date: string;
  alpha: number;
  beta: number;
  mde_pct: number;
  stratification: boolean;
  cuped: boolean;
  n_buckets: number;
  stat_test: string;
  salt: string;
  created_at: string;
};

export type DurationCalc = {
  mean: number; std: number;
  n_per_group: number; n_total: number;
  daily_users: number; days_required: number;
  mde_abs: number;
};

export type Histogram = { bins: number[]; counts: number[] };

export type BayesPosterior = {
  mean: number; std: number;
  ci_low: number; ci_high: number;
  chance_to_win: number;
  density_x: number[]; density_y: number[];
};

export type MetricRow = {
  metric_id: number;
  metric_name: string;
  is_primary: boolean;
  mean_a: number; mean_b: number;
  n_a: number; n_b: number;
  abs_lift: number; rel_lift: number;
  pvalue: number; ci_low: number; ci_high: number;
  is_significant: boolean;
  posterior: BayesPosterior;
};

export type SrmResult = {
  pvalue: number; chi2: number;
  observed: number[]; expected: number[];
  is_healthy: boolean;
};

export type ExpRun = {
  experiment: Experiment;
  metrics: MetricRow[];
  histogram_a: Histogram;
  histogram_b: Histogram;
  srm: SrmResult;
  summary: string;
};

export type TimelinePoint = { date: string; value: number };

export const api = {
  health: () => call<{ status: string; version: string }>("/health", "GET"),
  // Datasets
  datasets: () => call<Dataset[]>("/datasets", "GET"),
  dataset: (id: number) => call<Dataset>(`/datasets/${id}`, "GET"),
  datasetPreview: (id: number, n = 20) => call<any[]>(`/datasets/${id}/preview?n=${n}`, "GET"),
  datasetDelete: (id: number) => call<{ status: string }>(`/datasets/${id}`, "DELETE"),
  datasetDetect: (file: File) => upload<SchemaSuggestion>("/datasets/detect", file, {}),
  datasetUpload: (file: File, params: { name: string; user_col: string; date_col: string; description: string }) =>
    upload<Dataset>("/datasets/upload", file, params),
  // Metrics
  metrics: (datasetId?: number) =>
    call<MetricDef[]>(`/metrics${datasetId != null ? `?dataset_id=${datasetId}` : ""}`, "GET"),
  metricCreate: (b: object) => call<MetricDef>("/metrics", "POST", b),
  metricDelete: (id: number) => call<{ status: string }>(`/metrics/${id}`, "DELETE"),
  metricsTimeline: (b: object) => call<{ points: TimelinePoint[] }>("/metrics/timeline", "POST", b),
  // Design
  duration: (b: object) => call<DurationCalc>("/design/duration", "POST", b),
  // Experiments
  expList: () => call<Experiment[]>("/experiments", "GET"),
  expCreate: (b: object) => call<Experiment>("/experiments", "POST", b),
  expDelete: (id: number) => call<{ status: string }>(`/experiments/${id}`, "DELETE"),
  expRun: (id: number) => call<ExpRun>(`/experiments/${id}/run`, "GET"),
};
