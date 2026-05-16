from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# === Design / sample size ===
class SampleSizeRequest(BaseModel):
    mode: Literal["absolute", "relative"] = "absolute"
    effect: float = Field(..., gt=0)
    std: float = Field(..., gt=0)
    mean: float | None = None
    alpha: float = 0.05
    beta: float = 0.2


class SampleSizeResponse(BaseModel):
    n_per_group: int
    n_total: int


class DurationCalcRequest(BaseModel):
    dataset_id: int
    metric_id: int
    pre_start: datetime
    pre_end: datetime
    mde_pct: float = 1.0
    alpha: float = 0.05
    beta: float = 0.1
    daily_users: int | None = None


class DurationCalcResponse(BaseModel):
    mean: float
    std: float
    n_per_group: int
    n_total: int
    daily_users: int
    days_required: float
    mde_abs: float


# === Datasets ===
class DatasetCreatePayload(BaseModel):
    name: str
    user_col: str
    date_col: str | None = None
    description: str = ""


class DatasetOut(BaseModel):
    id: int
    name: str
    kind: str
    file_path: str
    user_col: str
    date_col: str | None
    description: str
    schema_json: dict
    created_at: datetime


class SchemaSuggestionOut(BaseModel):
    user_col: str | None
    date_col: str | None
    value_cols: list[str]
    dim_cols: list[str]
    all_cols: list[str]
    dtypes: dict[str, str]


# === Metric defs ===
class MetricDefPayload(BaseModel):
    name: str
    dataset_id: int
    kind: Literal["agg", "sql"] = "agg"
    agg: Literal["SUM", "AVG", "COUNT", "MIN", "MAX"] | None = None
    column: str | None = None
    sql: str | None = None
    description: str = ""


class MetricDefOut(BaseModel):
    id: int
    name: str
    dataset_id: int
    kind: str
    agg: str | None
    column: str | None
    sql: str | None
    description: str
    created_at: datetime


# === Experiment ===
class ExperimentPayload(BaseModel):
    name: str
    dataset_id: int
    primary_metric_id: int
    secondary_metric_ids: list[int] = []
    start_date: datetime
    end_date: datetime
    alpha: float = 0.05
    beta: float = 0.1
    mde_pct: float = 1.0
    stratification: bool = False
    strat_column: str | None = None
    cuped: bool = False
    n_buckets: int = 10
    stat_test: Literal["ttest", "welch", "mann_whitney", "bootstrap"] = "ttest"


class ExperimentOut(BaseModel):
    id: int
    name: str
    dataset_id: int
    primary_metric_id: int
    secondary_metric_ids: list[int]
    start_date: datetime
    end_date: datetime
    alpha: float
    beta: float
    mde_pct: float
    stratification: bool
    strat_column: str | None
    cuped: bool
    n_buckets: int
    stat_test: str
    salt: str
    created_at: datetime


# === Stat tests / multitest / sim (legacy) ===
class TwoSampleData(BaseModel):
    control: list[float]
    treatment: list[float]
    alpha: float = 0.05


class CupedRequest(BaseModel):
    y_control: list[float]
    y_treatment: list[float]
    x_control: list[float]
    x_treatment: list[float]
    alpha: float = 0.05


class TestResultResponse(BaseModel):
    method: str
    pvalue: float
    effect: float
    ci_low: float
    ci_high: float
    n_control: int
    n_treatment: int
    is_significant: bool


class MultiTestRequest(BaseModel):
    pvalues: list[float]
    alpha: float = 0.05
    method: Literal["bonferroni", "holm", "bh"] = "holm"


class MultiTestResponse(BaseModel):
    reject: list[bool]
    n_significant: int


# === Histograms / SRM / Bayes (shared) ===
class HistogramData(BaseModel):
    bins: list[float]
    counts: list[int]


class SrmResponse(BaseModel):
    pvalue: float
    chi2: float
    observed: list[int]
    expected: list[float]
    is_healthy: bool


class BayesPosterior(BaseModel):
    mean: float
    std: float
    ci_low: float
    ci_high: float
    chance_to_win: float
    density_x: list[float]
    density_y: list[float]


class MetricRow(BaseModel):
    metric_id: int
    metric_name: str
    is_primary: bool
    mean_a: float
    mean_b: float
    n_a: int
    n_b: int
    abs_lift: float
    rel_lift: float
    pvalue: float
    ci_low: float
    ci_high: float
    is_significant: bool
    posterior: BayesPosterior


class ExperimentRunResponse(BaseModel):
    experiment: ExperimentOut
    metrics: list[MetricRow]
    histogram_a: HistogramData
    histogram_b: HistogramData
    srm: SrmResponse
    summary: str


class TimelineRequest(BaseModel):
    dataset_id: int
    metric_id: int
    start_date: datetime
    end_date: datetime
    freq: Literal["H", "D", "W"] = "D"


class TimelinePoint(BaseModel):
    date: str
    value: float


class TimelineResponse(BaseModel):
    points: list[TimelinePoint]
