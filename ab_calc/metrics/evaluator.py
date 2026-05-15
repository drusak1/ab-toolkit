"""Evaluate a MetricDef against a Dataset → per-user values."""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from ab_calc.experiments.models import Dataset, MetricDef
from ab_calc.sources import get_engine


def evaluate(metric: MetricDef, dataset: Dataset, start: datetime, end: datetime) -> pd.DataFrame:
    """Returns DataFrame with columns [user_id, value]."""
    engine = get_engine()
    if metric.kind == "agg":
        if not metric.agg:
            raise ValueError("agg metric requires `agg` field")
        return engine.aggregate_metric(
            dataset_id=dataset.id,
            user_col=dataset.user_col,
            date_col=dataset.date_col,
            agg=metric.agg,
            value_col=metric.column,
            start=start,
            end=end,
        )
    if metric.kind == "sql":
        if not metric.sql:
            raise ValueError("sql metric requires `sql` field")
        return engine.raw_metric(metric.sql, start, end)
    raise ValueError(f"unknown metric kind: {metric.kind}")
