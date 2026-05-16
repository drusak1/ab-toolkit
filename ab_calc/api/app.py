from __future__ import annotations

import shutil
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from ab_calc import __version__
from ab_calc.api.schemas import (
    BayesPosterior,
    DatasetCreatePayload,
    DatasetOut,
    DurationCalcRequest,
    DurationCalcResponse,
    ExperimentOut,
    ExperimentPayload,
    ExperimentRunResponse,
    HistogramData,
    MetricDefOut,
    MetricDefPayload,
    MetricRow,
    MultiTestRequest,
    MultiTestResponse,
    SampleSizeRequest,
    SampleSizeResponse,
    SchemaSuggestionOut,
    SrmResponse,
    TestResultResponse,
    TimelinePoint,
    TimelineRequest,
    TimelineResponse,
    TwoSampleData,
    CupedRequest,
)
from ab_calc.design import mde_abs, mde_rel, sample_size_abs, sample_size_rel
from ab_calc.experiments import (
    DatasetCreate,
    ExperimentCreate,
    MetricDefCreate,
    assign_groups,
    get_registry,
)
from ab_calc.experiments.seed import CACHE_DIR, seed_builtin
from ab_calc.experiments.split import buckets_to_ab
from ab_calc.metrics import evaluate
from ab_calc.multitest import benjamini_hochberg, bonferroni, holm
from ab_calc.sources import detect_schema, get_engine
from ab_calc.stats import bootstrap_diff_test, mann_whitney, posterior_diff, srm_check, ttest, welch_ttest
from ab_calc.variance_reduction import cuped_test, stratified_test


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_builtin(get_registry())
    # Register existing user-uploaded datasets in engine on boot
    for ds in get_registry().list_datasets():
        try:
            get_engine().register(ds.id, ds.name, ds.file_path)
        except Exception as e:
            print(f"[boot] failed to register dataset {ds.name}: {e}")
    yield


app = FastAPI(title="AB Calc API", version=__version__, lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


UPLOAD_DIR = CACHE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# === Health ===
@app.get("/health")
def health():
    return {"status": "ok", "version": __version__}


# === Datasets ===
def _to_dataset_out(ds) -> DatasetOut:
    return DatasetOut(**ds.model_dump())


@app.get("/datasets", response_model=list[DatasetOut])
def api_datasets_list():
    return [_to_dataset_out(d) for d in get_registry().list_datasets()]


@app.get("/datasets/{ds_id}", response_model=DatasetOut)
def api_datasets_get(ds_id: int):
    ds = get_registry().get_dataset(ds_id)
    if not ds:
        raise HTTPException(404, "dataset not found")
    return _to_dataset_out(ds)


@app.get("/datasets/{ds_id}/preview")
def api_datasets_preview(ds_id: int, n: int = 20):
    if not get_engine().is_registered(ds_id):
        raise HTTPException(404, "dataset not registered in engine")
    return get_engine().preview(ds_id, n)


@app.delete("/datasets/{ds_id}")
def api_datasets_delete(ds_id: int):
    ds = get_registry().get_dataset(ds_id)
    if not ds:
        raise HTTPException(404)
    if ds.kind == "builtin":
        raise HTTPException(400, "cannot delete builtin dataset")
    get_registry().delete_dataset(ds_id)
    # remove uploaded file if it's in uploads dir
    p = Path(ds.file_path)
    if str(p).startswith(str(UPLOAD_DIR)) and p.exists():
        p.unlink()
    return {"status": "deleted"}


@app.post("/datasets/detect", response_model=SchemaSuggestionOut)
async def api_datasets_detect(file: UploadFile = File(...)):
    """Probe uploaded file → suggest schema. Does NOT persist."""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in (".csv", ".parquet"):
        raise HTTPException(400, "only .csv or .parquet supported")
    tmp = UPLOAD_DIR / f"_probe_{uuid.uuid4().hex[:8]}{suffix}"
    try:
        with tmp.open("wb") as f:
            shutil.copyfileobj(file.file, f)
        return SchemaSuggestionOut(**detect_schema(tmp).to_dict())
    finally:
        if tmp.exists():
            tmp.unlink()


@app.post("/datasets/upload", response_model=DatasetOut)
async def api_datasets_upload(
    file: UploadFile = File(...),
    name: str = "",
    user_col: str = "",
    date_col: str = "",
    description: str = "",
):
    if not name or not user_col:
        raise HTTPException(400, "name and user_col required")
    if get_registry().get_dataset_by_name(name):
        raise HTTPException(400, f"dataset '{name}' already exists")
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in (".csv", ".parquet"):
        raise HTTPException(400, "only .csv or .parquet supported")
    dest = UPLOAD_DIR / f"{name}_{uuid.uuid4().hex[:6]}{suffix}"
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    schema = detect_schema(dest).to_dict()
    ds = get_registry().create_dataset(DatasetCreate(
        name=name,
        kind=suffix.lstrip("."),
        file_path=str(dest),
        user_col=user_col,
        date_col=date_col or None,
        description=description,
        schema_json=schema,
    ))
    get_engine().register(ds.id, ds.name, ds.file_path)
    return _to_dataset_out(ds)


# === Metrics ===
def _to_metric_out(m) -> MetricDefOut:
    return MetricDefOut(**m.model_dump())


@app.get("/metrics", response_model=list[MetricDefOut])
def api_metrics_list(dataset_id: int | None = None):
    return [_to_metric_out(m) for m in get_registry().list_metrics(dataset_id)]


@app.post("/metrics", response_model=MetricDefOut)
def api_metrics_create(req: MetricDefPayload):
    ds = get_registry().get_dataset(req.dataset_id)
    if not ds:
        raise HTTPException(404, "dataset not found")
    m = get_registry().create_metric(MetricDefCreate(**req.model_dump()))
    return _to_metric_out(m)


@app.delete("/metrics/{m_id}")
def api_metrics_delete(m_id: int):
    if not get_registry().delete_metric(m_id):
        raise HTTPException(404)
    return {"status": "deleted"}


@app.post("/metrics/timeline", response_model=TimelineResponse)
def api_metrics_timeline(req: TimelineRequest):
    """Time-series aggregate. agg metric only (sql metrics don't have a natural timeline)."""
    reg = get_registry()
    ds = reg.get_dataset(req.dataset_id)
    metric = reg.get_metric(req.metric_id)
    if not ds or not metric:
        raise HTTPException(404)
    if metric.kind != "agg":
        raise HTTPException(400, "timeline only supported for agg metrics")
    if not ds.date_col:
        raise HTTPException(400, "dataset has no date column")

    engine = get_engine()
    view = engine.view_for(ds.id)
    date_col = f'"{ds.date_col}"'
    agg = metric.agg.upper()
    if agg == "COUNT":
        expr = "COUNT(*)"
    else:
        expr = f'{agg}("{metric.column}")'
    bucket = {"H": "hour", "D": "day", "W": "week"}[req.freq]
    sql = (
        f"SELECT date_trunc('{bucket}', {date_col}) AS d, {expr} AS v "
        f"FROM {view} WHERE {date_col} >= TIMESTAMP '{req.start_date.isoformat(sep=' ')}' "
        f"AND {date_col} < TIMESTAMP '{req.end_date.isoformat(sep=' ')}' "
        f"GROUP BY 1 ORDER BY 1"
    )
    df = engine.conn.execute(sql).df()
    points = [TimelinePoint(date=str(r["d"]), value=float(r["v"])) for _, r in df.iterrows()]
    return TimelineResponse(points=points)


# === Design ===
@app.post("/design/sample_size", response_model=SampleSizeResponse)
def api_sample_size(req: SampleSizeRequest):
    if req.mode == "relative":
        if req.mean is None:
            raise HTTPException(400, "mean required")
        n = sample_size_rel(req.effect, req.mean, req.std, req.alpha, req.beta)
    else:
        n = sample_size_abs(req.effect, req.std, req.alpha, req.beta)
    return SampleSizeResponse(n_per_group=n, n_total=2 * n)


@app.post("/design/duration", response_model=DurationCalcResponse)
def api_design_duration(req: DurationCalcRequest):
    reg = get_registry()
    ds = reg.get_dataset(req.dataset_id)
    metric = reg.get_metric(req.metric_id)
    if not ds or not metric:
        raise HTTPException(404)
    df = evaluate(metric, ds, req.pre_start, req.pre_end)
    if df.empty:
        raise HTTPException(400, "no data in pre-period")
    values = df["value"].to_numpy()
    mean, std = float(values.mean()), float(values.std(ddof=1))
    if mean <= 0:
        raise HTTPException(400, "mean must be positive for relative MDE")
    n_per = sample_size_rel(req.mde_pct / 100.0, mean, std, req.alpha, req.beta)
    mde_abs_val = mean * (req.mde_pct / 100.0)
    period_days = max(1, (req.pre_end - req.pre_start).days)
    daily_users = req.daily_users or max(1, len(values) // period_days)
    days_required = (2 * n_per) / daily_users
    return DurationCalcResponse(
        mean=mean, std=std, n_per_group=n_per, n_total=2 * n_per,
        daily_users=daily_users, days_required=days_required, mde_abs=mde_abs_val,
    )


# === Stat tests (raw, legacy) ===
@app.post("/test/ttest", response_model=TestResultResponse)
def api_ttest(req: TwoSampleData):
    return TestResultResponse(**ttest(np.array(req.control), np.array(req.treatment), req.alpha).to_dict())


@app.post("/test/welch", response_model=TestResultResponse)
def api_welch(req: TwoSampleData):
    return TestResultResponse(**welch_ttest(np.array(req.control), np.array(req.treatment), req.alpha).to_dict())


@app.post("/test/mann_whitney", response_model=TestResultResponse)
def api_mw(req: TwoSampleData):
    return TestResultResponse(**mann_whitney(np.array(req.control), np.array(req.treatment), req.alpha).to_dict())


@app.post("/test/bootstrap", response_model=TestResultResponse)
def api_bootstrap(req: TwoSampleData):
    return TestResultResponse(**bootstrap_diff_test(np.array(req.control), np.array(req.treatment), alpha=req.alpha).to_dict())


@app.post("/test/cuped", response_model=TestResultResponse)
def api_cuped(req: CupedRequest):
    res = cuped_test(np.array(req.y_control), np.array(req.y_treatment), np.array(req.x_control), np.array(req.x_treatment), req.alpha)
    return TestResultResponse(**res.to_dict())


@app.post("/multitest", response_model=MultiTestResponse)
def api_multitest(req: MultiTestRequest):
    fn = {"bonferroni": bonferroni, "holm": holm, "bh": benjamini_hochberg}[req.method]
    reject = fn(np.array(req.pvalues), req.alpha).tolist()
    return MultiTestResponse(reject=reject, n_significant=int(sum(reject)))


# === Experiments ===
def _to_exp_out(e) -> ExperimentOut:
    return ExperimentOut(**e.model_dump())


@app.get("/experiments", response_model=list[ExperimentOut])
def api_exp_list():
    return [_to_exp_out(e) for e in get_registry().list_experiments()]


@app.post("/experiments", response_model=ExperimentOut)
def api_exp_create(req: ExperimentPayload):
    reg = get_registry()
    if not reg.get_dataset(req.dataset_id):
        raise HTTPException(404, "dataset not found")
    if not reg.get_metric(req.primary_metric_id):
        raise HTTPException(404, "primary metric not found")
    exp = reg.create_experiment(ExperimentCreate(**req.model_dump()))
    return _to_exp_out(exp)


@app.delete("/experiments/{exp_id}")
def api_exp_delete(exp_id: int):
    if not get_registry().delete_experiment(exp_id):
        raise HTTPException(404)
    return {"status": "deleted"}


def _hist(values: np.ndarray, n_bins: int = 50) -> HistogramData:
    counts, edges = np.histogram(values, bins=n_bins)
    return HistogramData(bins=edges.tolist(), counts=counts.tolist())


def _run_one_metric(metric, ds, exp, ab: np.ndarray, user_ids, strata: np.ndarray | None = None):
    df = evaluate(metric, ds, exp.start_date, exp.end_date)
    if df.empty:
        return None
    val_map = dict(zip(df["user_id"].astype(str), df["value"]))
    vals = np.array([val_map.get(u, 0.0) for u in user_ids], dtype=float)
    a, b = vals[ab == 0], vals[ab == 1]
    if len(a) < 2 or len(b) < 2:
        return None

    if exp.stratification and strata is not None:
        res = stratified_test(a, b, strata[ab == 0], strata[ab == 1], alpha=exp.alpha)
    elif exp.cuped:
        period_len = exp.end_date - exp.start_date
        pre_df = evaluate(metric, ds, exp.start_date - period_len, exp.start_date)
        pre_map = dict(zip(pre_df["user_id"].astype(str), pre_df["value"]))
        cov = np.array([pre_map.get(u, 0.0) for u in user_ids], dtype=float)
        res = cuped_test(a, b, cov[ab == 0], cov[ab == 1], alpha=exp.alpha)
    else:
        test_fn = {
            "ttest": ttest, "welch": welch_ttest,
            "mann_whitney": mann_whitney, "bootstrap": bootstrap_diff_test,
        }.get(exp.stat_test, ttest)
        res = test_fn(a, b, alpha=exp.alpha)

    post = posterior_diff(a, b, alpha=exp.alpha)
    mean_a, mean_b = float(a.mean()), float(b.mean())
    abs_lift = mean_b - mean_a
    rel_lift = abs_lift / mean_a if mean_a != 0 else 0.0

    row = MetricRow(
        metric_id=metric.id,
        metric_name=metric.name,
        is_primary=(metric.id == exp.primary_metric_id),
        mean_a=mean_a, mean_b=mean_b, n_a=len(a), n_b=len(b),
        abs_lift=abs_lift, rel_lift=rel_lift,
        pvalue=res.pvalue, ci_low=res.ci_low, ci_high=res.ci_high,
        is_significant=res.is_significant,
        posterior=BayesPosterior(**post),
    )
    return row, a, b


def _summary(primary: MetricRow, srm_ok: bool) -> str:
    if not srm_ok:
        return "⚠ SRM detected. Results not reliable until split is fixed."
    if primary.is_significant:
        direction = "B wins" if primary.abs_lift > 0 else "A wins"
        return (
            f"Ship: {direction} on {primary.metric_name}. "
            f"Lift = {primary.rel_lift * 100:+.2f}% "
            f"(CI [{primary.ci_low:+.2f}, {primary.ci_high:+.2f}], p={primary.pvalue:.4f})."
        )
    return (
        f"No effect on {primary.metric_name}. Lift = {primary.rel_lift * 100:+.2f}% (p={primary.pvalue:.4f})."
    )


@app.get("/experiments/{exp_id}/run", response_model=ExperimentRunResponse)
def api_exp_run(exp_id: int):
    reg = get_registry()
    exp = reg.get_experiment(exp_id)
    if not exp:
        raise HTTPException(404)
    ds = reg.get_dataset(exp.dataset_id)
    if not ds:
        raise HTTPException(400, "dataset gone")
    primary = reg.get_metric(exp.primary_metric_id)
    if not primary:
        raise HTTPException(400, "primary metric gone")

    # Compute user IDs from primary metric → split
    primary_df = evaluate(primary, ds, exp.start_date, exp.end_date)
    if primary_df.empty:
        raise HTTPException(400, "no data for primary metric in period")
    user_ids = primary_df["user_id"].astype(str).tolist()
    buckets = assign_groups(user_ids, exp.salt, exp.n_buckets)
    ab = buckets_to_ab(buckets)

    # Per-user strata (post-stratification variance reduction)
    strata = None
    if exp.stratification and exp.strat_column:
        dim_df = get_engine().user_dimension(
            ds.id, ds.user_col, exp.strat_column, ds.date_col, exp.start_date, exp.end_date
        )
        strat_map = dict(zip(dim_df["user_id"].astype(str), dim_df["stratum"].astype(str)))
        strata = np.array([strat_map.get(u, "_na") for u in user_ids])

    rows = []
    hist_a = hist_b = None
    metric_ids = [exp.primary_metric_id] + list(exp.secondary_metric_ids)
    for mid in metric_ids:
        m = reg.get_metric(mid)
        if not m:
            continue
        out = _run_one_metric(m, ds, exp, ab, user_ids, strata)
        if out is None:
            continue
        row, a, b = out
        rows.append(row)
        if row.is_primary:
            hist_a, hist_b = _hist(a), _hist(b)

    if not rows:
        raise HTTPException(400, "no metric could be computed")

    primary_row = next(r for r in rows if r.is_primary)
    srm = srm_check([(ab == 0).sum(), (ab == 1).sum()])
    return ExperimentRunResponse(
        experiment=_to_exp_out(exp),
        metrics=rows,
        histogram_a=hist_a,
        histogram_b=hist_b,
        srm=SrmResponse(**srm.to_dict()),
        summary=_summary(primary_row, srm.is_healthy),
    )
