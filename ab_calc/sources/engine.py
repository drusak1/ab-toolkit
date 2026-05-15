"""DuckDB-based query engine: register datasets as views, run metric queries."""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import duckdb
import pandas as pd

_VIEW_NAME_RE = re.compile(r"[^a-zA-Z0-9_]")


def safe_view_name(name: str) -> str:
    """Slugify name → valid SQL identifier."""
    s = _VIEW_NAME_RE.sub("_", name.strip().lower())
    if not s or not s[0].isalpha():
        s = "ds_" + s
    return s[:60]


class DuckEngine:
    def __init__(self):
        self.conn = duckdb.connect(":memory:")
        self._registered: dict[int, str] = {}

    def register(self, dataset_id: int, view_name: str, file_path: str) -> str:
        p = Path(file_path)
        suffix = p.suffix.lower()
        if suffix == ".csv":
            reader = f"read_csv_auto('{file_path}', sample_size=-1)"
        elif suffix == ".parquet":
            reader = f"read_parquet('{file_path}')"
        else:
            raise ValueError(f"unsupported extension: {suffix}")
        view = safe_view_name(view_name)
        self.conn.execute(f"CREATE OR REPLACE VIEW {view} AS SELECT * FROM {reader}")
        self._registered[dataset_id] = view
        return view

    def view_for(self, dataset_id: int) -> str:
        if dataset_id not in self._registered:
            raise KeyError(f"dataset {dataset_id} not registered")
        return self._registered[dataset_id]

    def is_registered(self, dataset_id: int) -> bool:
        return dataset_id in self._registered

    def preview(self, dataset_id: int, n: int = 20) -> list[dict]:
        view = self.view_for(dataset_id)
        return self.conn.execute(f"SELECT * FROM {view} LIMIT {n}").df().to_dict(orient="records")

    def row_count(self, dataset_id: int) -> int:
        view = self.view_for(dataset_id)
        return int(self.conn.execute(f"SELECT COUNT(*) FROM {view}").fetchone()[0])

    def aggregate_metric(
        self,
        dataset_id: int,
        user_col: str,
        date_col: str | None,
        agg: str,
        value_col: str | None,
        start: datetime | None,
        end: datetime | None,
        extra_where: str | None = None,
    ) -> pd.DataFrame:
        """Compute per-user metric value via SQL aggregate."""
        view = self.view_for(dataset_id)
        agg_up = agg.upper()
        if agg_up == "COUNT":
            expr = "COUNT(*)"
        elif value_col is None:
            raise ValueError(f"value_col required for {agg}")
        elif agg_up in ("SUM", "AVG", "MIN", "MAX"):
            expr = f"{agg_up}({_q(value_col)})"
        else:
            raise ValueError(f"unsupported agg: {agg}")

        where_clauses = []
        if date_col and start is not None:
            where_clauses.append(f"{_q(date_col)} >= TIMESTAMP '{start.isoformat(sep=' ')}'")
        if date_col and end is not None:
            where_clauses.append(f"{_q(date_col)} < TIMESTAMP '{end.isoformat(sep=' ')}'")
        if extra_where:
            where_clauses.append(f"({extra_where})")
        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        sql = (
            f"SELECT {_q(user_col)} AS user_id, {expr} AS value "
            f"FROM {view} {where_sql} GROUP BY {_q(user_col)}"
        )
        return self.conn.execute(sql).df()

    def raw_metric(self, sql: str, start: datetime | None, end: datetime | None) -> pd.DataFrame:
        """Run user-provided SQL with {start}/{end} placeholders. Must return columns user_id, value."""
        s = start.isoformat(sep=" ") if start else ""
        e = end.isoformat(sep=" ") if end else ""
        replaced = sql.replace("{start}", f"TIMESTAMP '{s}'").replace("{end}", f"TIMESTAMP '{e}'")
        df = self.conn.execute(replaced).df()
        if not {"user_id", "value"}.issubset(df.columns):
            raise ValueError("raw SQL must return columns: user_id, value")
        return df


def _q(name: str) -> str:
    """Safely quote a column identifier for DuckDB."""
    return '"' + name.replace('"', '""') + '"'


_singleton: DuckEngine | None = None


def get_engine() -> DuckEngine:
    global _singleton
    if _singleton is None:
        _singleton = DuckEngine()
    return _singleton
