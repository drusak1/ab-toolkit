from __future__ import annotations

import numpy as np
from scipy import stats

from ab_calc.stats.result import TestResult


def _mean_diff_ci(a: np.ndarray, b: np.ndarray, alpha: float, equal_var: bool) -> tuple[float, float, float]:
    diff = float(b.mean() - a.mean())
    var_a = a.var(ddof=1) / len(a)
    var_b = b.var(ddof=1) / len(b)
    se = float(np.sqrt(var_a + var_b))
    if equal_var:
        df = len(a) + len(b) - 2
    else:
        df = (var_a + var_b) ** 2 / (var_a ** 2 / (len(a) - 1) + var_b ** 2 / (len(b) - 1))
    t = stats.t.ppf(1 - alpha / 2, df)
    return diff, diff - t * se, diff + t * se


def ttest(control: np.ndarray, treatment: np.ndarray, alpha: float = 0.05) -> TestResult:
    """Student's t-test (equal variances)."""
    a, b = np.asarray(control, dtype=float), np.asarray(treatment, dtype=float)
    pvalue = float(stats.ttest_ind(a, b, equal_var=True).pvalue)
    diff, lo, hi = _mean_diff_ci(a, b, alpha, equal_var=True)
    return TestResult("ttest", pvalue, diff, lo, hi, len(a), len(b))


def welch_ttest(control: np.ndarray, treatment: np.ndarray, alpha: float = 0.05) -> TestResult:
    """Welch's t-test (unequal variances)."""
    a, b = np.asarray(control, dtype=float), np.asarray(treatment, dtype=float)
    pvalue = float(stats.ttest_ind(a, b, equal_var=False).pvalue)
    diff, lo, hi = _mean_diff_ci(a, b, alpha, equal_var=False)
    return TestResult("welch_ttest", pvalue, diff, lo, hi, len(a), len(b))
