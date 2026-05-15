"""Metric registry. Each metric: function (DataService, start, end) -> DataFrame[user_id, value]."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable

import pandas as pd

from ab_calc.data import DataService


@dataclass
class Metric:
    key: str
    label: str
    description: str
    fn: Callable[[DataService, datetime, datetime], pd.DataFrame]


def _ts(d) -> pd.Timestamp:
    return pd.Timestamp(d)


def _revenue_all(ds: DataService, start: datetime, end: datetime) -> pd.DataFrame:
    s, e = _ts(start), _ts(end)
    df = ds.sales
    df = df[(df["date"] >= s) & (df["date"] < e)]
    return df.groupby("user_id", as_index=False)["price"].sum().rename(columns={"price": "value"})


def _revenue_web(ds: DataService, start: datetime, end: datetime) -> pd.DataFrame:
    """Revenue per user, restricted to users with web activity in the period."""
    s, e = _ts(start), _ts(end)
    web = ds.web_logs
    web_users = web[(web["date"] >= s) & (web["date"] < e)]["user_id"].unique()
    df = _revenue_all(ds, start, end)
    return df[df["user_id"].isin(web_users)].reset_index(drop=True)


def _response_time(ds: DataService, start: datetime, end: datetime) -> pd.DataFrame:
    s, e = _ts(start), _ts(end)
    df = ds.web_logs
    df = df[(df["date"] >= s) & (df["date"] < e)]
    return df.groupby("user_id", as_index=False)["load_time"].mean().rename(columns={"load_time": "value"})


METRICS: dict[str, Metric] = {
    "revenue_web": Metric("revenue_web", "Revenue (web users)", "Sum of price per user, web-active users only", _revenue_web),
    "revenue_all": Metric("revenue_all", "Revenue (all users)", "Sum of price per user", _revenue_all),
    "response_time": Metric("response_time", "Response time", "Mean page load_time per user", _response_time),
}


def list_metrics() -> list[dict]:
    return [{"key": m.key, "label": m.label, "description": m.description} for m in METRICS.values()]


def compute_user_metric(ds: DataService, key: str, start: datetime, end: datetime) -> pd.DataFrame:
    if key not in METRICS:
        raise KeyError(f"unknown metric: {key}")
    return METRICS[key].fn(ds, start, end)


def compute_timeline(ds: DataService, key: str, start: datetime, end: datetime, freq: str = "D") -> pd.DataFrame:
    """Aggregate metric over time. Returns DataFrame[date, value].

    revenue_* → daily sum of price (across users).
    response_time → daily mean of load_time.
    freq: pandas offset alias ('D', 'H', 'W').
    """
    s, e = _ts(start), _ts(end)
    if key in ("revenue_all", "revenue_web"):
        df = ds.sales.copy()
        df = df[(df["date"] >= s) & (df["date"] < e)]
        if key == "revenue_web":
            web = ds.web_logs
            users = set(web[(web["date"] >= s) & (web["date"] < e)]["user_id"].unique())
            df = df[df["user_id"].isin(users)]
        ts = df.set_index("date").resample(freq)["price"].sum().reset_index()
        ts = ts.rename(columns={"price": "value"})
    elif key == "response_time":
        df = ds.web_logs.copy()
        df = df[(df["date"] >= s) & (df["date"] < e)]
        ts = df.set_index("date").resample(freq)["load_time"].mean().reset_index()
        ts = ts.rename(columns={"load_time": "value"})
    else:
        raise KeyError(f"unknown metric: {key}")
    ts["date"] = ts["date"].dt.strftime("%Y-%m-%d %H:%M")
    return ts
