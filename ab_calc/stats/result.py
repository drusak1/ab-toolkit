from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class TestResult:
    method: str
    pvalue: float
    effect: float
    ci_low: float
    ci_high: float
    n_control: int
    n_treatment: int

    @property
    def is_significant(self) -> bool:
        return self.pvalue < 0.05

    def to_dict(self) -> dict:
        d = asdict(self)
        d["is_significant"] = self.is_significant
        return d
