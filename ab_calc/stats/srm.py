"""Sample Ratio Mismatch (SRM) check via chi-square goodness of fit."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats


@dataclass
class SrmResult:
    pvalue: float
    chi2: float
    observed: list[int]
    expected: list[float]
    is_healthy: bool

    def to_dict(self) -> dict:
        return {
            "pvalue": self.pvalue,
            "chi2": self.chi2,
            "observed": self.observed,
            "expected": self.expected,
            "is_healthy": self.is_healthy,
        }


def srm_check(counts: list[int] | np.ndarray, expected_ratios: list[float] | None = None, alpha: float = 0.001) -> SrmResult:
    """Test if observed group sizes match expected ratios. Alpha=0.001 default (industry standard)."""
    obs = np.asarray(counts, dtype=float)
    total = obs.sum()
    if expected_ratios is None:
        expected_ratios = [1.0 / len(obs)] * len(obs)
    exp = np.asarray(expected_ratios, dtype=float) * total
    chi2 = float(((obs - exp) ** 2 / exp).sum())
    pvalue = float(1 - stats.chi2.cdf(chi2, df=len(obs) - 1))
    return SrmResult(pvalue, chi2, obs.astype(int).tolist(), exp.tolist(), pvalue >= alpha)
