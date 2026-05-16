"""Auto-detect dataset schema by sampling first N rows."""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from pathlib import Path

import pandas as pd


@dataclass
class SchemaSuggestion:
    user_col: str | None
    date_col: str | None
    value_cols: list[str]   # numeric columns (potential metric values)
    dim_cols: list[str]     # string/categorical columns (potential dimensions for stratification)
    all_cols: list[str]
    dtypes: dict[str, str]

    def to_dict(self) -> dict:
        return asdict(self)


_USER_HINTS = re.compile(r"(?i)\b(user|customer|client|account|visitor)[_-]?id\b|^uid$|^user$")
_DATE_HINTS = re.compile(r"(?i)\b(date|time|created|timestamp|dt|ts|event_time)\b")


def detect_schema(path: Path | str, n_rows: int = 1000) -> SchemaSuggestion:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(path, nrows=n_rows)
    elif suffix == ".parquet":
        df = pd.read_parquet(path).head(n_rows)
    else:
        raise ValueError(f"unsupported extension: {suffix}")

    cols = list(df.columns)
    dtypes = {c: str(df[c].dtype) for c in cols}

    user_col = next((c for c in cols if _USER_HINTS.search(c)), None)
    date_col = next((c for c in cols if _DATE_HINTS.search(c) or "datetime" in dtypes[c]), None)

    if date_col and "datetime" not in dtypes[date_col]:
        try:
            pd.to_datetime(df[date_col].head(50))
        except Exception:
            date_col = None

    value_cols, dim_cols = [], []
    for c in cols:
        if c == user_col or c == date_col:
            continue
        if pd.api.types.is_numeric_dtype(df[c]):
            value_cols.append(c)
        elif pd.api.types.is_datetime64_any_dtype(df[c]):
            continue
        elif df[c].nunique() <= 20:
            # low-cardinality string / category → potential stratum
            dim_cols.append(c)

    return SchemaSuggestion(user_col, date_col, value_cols, dim_cols, cols, dtypes)
