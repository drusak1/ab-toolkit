"""Seed builtin Karpov pizza datasets and example metrics on first start."""
from __future__ import annotations

import os
from pathlib import Path

from ab_calc.data.service import URL_BASE, FILES
from ab_calc.experiments.models import DatasetCreate, MetricDefCreate
from ab_calc.experiments.service import Registry
from ab_calc.sources import detect_schema, get_engine

CACHE_DIR = Path(os.environ.get("AB_CALC_CACHE", Path.home() / ".cache" / "ab_calc"))

BUILTIN_DATASETS = [
    {
        "name": "pizza_sales",
        "filename": FILES["sales"],
        "user_col": "user_id",
        "date_col": "date",
        "description": "Karpov sim_ab pizza orders (one row per order)",
        "metrics": [
            {"name": "Revenue", "agg": "SUM", "column": "price", "description": "Total spend per user"},
            {"name": "Avg order price", "agg": "AVG", "column": "price", "description": "Mean basket size"},
            {"name": "Order count", "agg": "COUNT", "column": None, "description": "Orders per user"},
            {"name": "Pizzas bought", "agg": "SUM", "column": "count_pizza", "description": "Total pizzas per user"},
        ],
    },
    {
        "name": "pizza_web_logs",
        "filename": FILES["web_logs"],
        "user_col": "user_id",
        "date_col": "date",
        "description": "Karpov sim_ab web logs (page hits)",
        "metrics": [
            {"name": "Avg load time", "agg": "AVG", "column": "load_time", "description": "Mean page load ms per user"},
            {"name": "Page hits", "agg": "COUNT", "column": None, "description": "Number of page views per user"},
            {"name": "Max load time", "agg": "MAX", "column": "load_time", "description": "Worst page load per user"},
        ],
    },
]


def _ensure_cached(filename: str) -> Path:
    """Download file to cache if absent."""
    import pandas as pd
    local = CACHE_DIR / filename
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if not local.exists():
        df = pd.read_csv(URL_BASE + filename)
        df.to_csv(local, index=False)
    return local


def seed_builtin(registry: Registry) -> None:
    engine = get_engine()
    for spec in BUILTIN_DATASETS:
        if registry.get_dataset_by_name(spec["name"]):
            ds = registry.get_dataset_by_name(spec["name"])
            engine.register(ds.id, ds.name, ds.file_path)
            continue
        local = _ensure_cached(spec["filename"])
        schema = detect_schema(local).to_dict()
        ds = registry.create_dataset(DatasetCreate(
            name=spec["name"],
            kind="builtin",
            file_path=str(local),
            user_col=spec["user_col"],
            date_col=spec["date_col"],
            description=spec["description"],
            schema_json=schema,
        ))
        engine.register(ds.id, ds.name, ds.file_path)
        for m in spec["metrics"]:
            registry.create_metric(MetricDefCreate(
                name=m["name"],
                dataset_id=ds.id,
                kind="agg",
                agg=m["agg"],
                column=m["column"],
                description=m["description"],
            ))
