from __future__ import annotations

import os
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine, select

from ab_calc.experiments.models import (
    Dataset,
    DatasetCreate,
    Experiment,
    ExperimentCreate,
    MetricDef,
    MetricDefCreate,
)
from ab_calc.experiments.split import generate_salt

DB_PATH = Path(os.environ.get("AB_CALC_DB", Path.home() / ".cache" / "ab_calc" / "experiments.db"))


class Registry:
    def __init__(self, db_path: Path = DB_PATH):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        SQLModel.metadata.create_all(self.engine)

    # === Dataset ===
    def list_datasets(self) -> list[Dataset]:
        with Session(self.engine) as s:
            return list(s.exec(select(Dataset).order_by(Dataset.created_at.desc())))

    def get_dataset(self, id: int) -> Dataset | None:
        with Session(self.engine) as s:
            return s.get(Dataset, id)

    def get_dataset_by_name(self, name: str) -> Dataset | None:
        with Session(self.engine) as s:
            return s.exec(select(Dataset).where(Dataset.name == name)).first()

    def create_dataset(self, payload: DatasetCreate) -> Dataset:
        with Session(self.engine) as s:
            ds = Dataset(**payload.model_dump())
            s.add(ds); s.commit(); s.refresh(ds)
            return ds

    def delete_dataset(self, id: int) -> bool:
        with Session(self.engine) as s:
            ds = s.get(Dataset, id)
            if not ds:
                return False
            s.delete(ds); s.commit(); return True

    # === MetricDef ===
    def list_metrics(self, dataset_id: int | None = None) -> list[MetricDef]:
        with Session(self.engine) as s:
            q = select(MetricDef)
            if dataset_id is not None:
                q = q.where(MetricDef.dataset_id == dataset_id)
            return list(s.exec(q.order_by(MetricDef.created_at.desc())))

    def get_metric(self, id: int) -> MetricDef | None:
        with Session(self.engine) as s:
            return s.get(MetricDef, id)

    def create_metric(self, payload: MetricDefCreate) -> MetricDef:
        with Session(self.engine) as s:
            m = MetricDef(**payload.model_dump())
            s.add(m); s.commit(); s.refresh(m)
            return m

    def delete_metric(self, id: int) -> bool:
        with Session(self.engine) as s:
            m = s.get(MetricDef, id)
            if not m:
                return False
            s.delete(m); s.commit(); return True

    # === Experiment ===
    def list_experiments(self) -> list[Experiment]:
        with Session(self.engine) as s:
            return list(s.exec(select(Experiment).order_by(Experiment.created_at.desc())))

    def get_experiment(self, id: int) -> Experiment | None:
        with Session(self.engine) as s:
            return s.get(Experiment, id)

    def create_experiment(self, payload: ExperimentCreate) -> Experiment:
        with Session(self.engine) as s:
            exp = Experiment(**payload.model_dump(), salt=generate_salt())
            s.add(exp); s.commit(); s.refresh(exp)
            return exp

    def delete_experiment(self, id: int) -> bool:
        with Session(self.engine) as s:
            exp = s.get(Experiment, id)
            if not exp:
                return False
            s.delete(exp); s.commit(); return True


_singleton: Registry | None = None


def get_registry() -> Registry:
    global _singleton
    if _singleton is None:
        _singleton = Registry()
    return _singleton
