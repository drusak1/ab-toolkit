from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel, Column, JSON


# === Dataset ===
class DatasetBase(SQLModel):
    name: str = Field(index=True, unique=True)
    kind: str = "csv"  # csv | parquet | builtin
    file_path: str
    user_col: str
    date_col: Optional[str] = None
    description: Optional[str] = ""


class Dataset(DatasetBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    schema_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DatasetCreate(DatasetBase):
    schema_json: dict = {}


class DatasetRead(DatasetBase):
    id: int
    schema_json: dict
    created_at: datetime


# === MetricDef ===
class MetricDefBase(SQLModel):
    name: str
    dataset_id: int = Field(foreign_key="dataset.id", index=True)
    kind: str = "agg"  # agg | sql
    agg: Optional[str] = None  # SUM | AVG | COUNT | MIN | MAX
    column: Optional[str] = None
    sql: Optional[str] = None
    description: Optional[str] = ""


class MetricDef(MetricDefBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MetricDefCreate(MetricDefBase):
    pass


class MetricDefRead(MetricDefBase):
    id: int
    created_at: datetime


# === Experiment ===
class ExperimentBase(SQLModel):
    name: str
    dataset_id: int = Field(foreign_key="dataset.id", index=True)
    primary_metric_id: int = Field(foreign_key="metricdef.id")
    start_date: datetime
    end_date: datetime
    alpha: float = 0.05
    beta: float = 0.1
    mde_pct: float = 1.0
    stratification: bool = False
    cuped: bool = False
    n_buckets: int = 10
    stat_test: str = "ttest"


class Experiment(ExperimentBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    salt: str
    secondary_metric_ids: list[int] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ExperimentCreate(ExperimentBase):
    secondary_metric_ids: list[int] = []


class ExperimentRead(ExperimentBase):
    id: int
    salt: str
    secondary_metric_ids: list[int]
    created_at: datetime
