"""Load and cache sim_ab datasets from Karpov public S3."""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import pandas as pd

URL_BASE = "https://raw.githubusercontent.com/ab-courses/simulator-ab-datasets/main/2022-04-01/"
FILES = {
    "sales": "2022-04-01T12_df_sales.csv",
    "sales_detail": "2022-04-01T12_df_sales_detail.csv",
    "web_logs": "2022-04-01T12_df_web_logs.csv",
}

CACHE_DIR = Path(os.environ.get("AB_CALC_CACHE", Path.home() / ".cache" / "ab_calc"))


class DataService:
    def __init__(self, cache_dir: Path = CACHE_DIR):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._frames: dict[str, pd.DataFrame] = {}

    def _load(self, name: str) -> pd.DataFrame:
        local = self.cache_dir / FILES[name]
        if not local.exists():
            df = pd.read_csv(URL_BASE + FILES[name])
            df.to_csv(local, index=False)
        else:
            df = pd.read_csv(local)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
        return df

    def get(self, name: str) -> pd.DataFrame:
        if name not in FILES:
            raise KeyError(f"unknown table: {name}")
        if name not in self._frames:
            self._frames[name] = self._load(name)
        return self._frames[name]

    @property
    def sales(self) -> pd.DataFrame:
        return self.get("sales")

    @property
    def sales_detail(self) -> pd.DataFrame:
        return self.get("sales_detail")

    @property
    def web_logs(self) -> pd.DataFrame:
        return self.get("web_logs")

    def info(self) -> dict:
        out = {}
        for name in FILES:
            df = self.get(name)
            out[name] = {
                "rows": len(df),
                "columns": list(df.columns),
                "date_min": str(df["date"].min()) if "date" in df.columns else None,
                "date_max": str(df["date"].max()) if "date" in df.columns else None,
                "users": int(df["user_id"].nunique()) if "user_id" in df.columns else None,
            }
        return out

    def logs(self, table: str, date: datetime, user_id: str | None = None, limit: int = 100) -> list[dict]:
        df = self.get(table)
        mask = df["date"] >= pd.Timestamp(date)
        if user_id:
            mask &= df["user_id"] == user_id
        out = df[mask].head(limit).copy()
        if "date" in out.columns:
            out["date"] = out["date"].astype(str)
        return out.to_dict(orient="records")


_singleton: DataService | None = None


def get_data() -> DataService:
    global _singleton
    if _singleton is None:
        _singleton = DataService()
    return _singleton
