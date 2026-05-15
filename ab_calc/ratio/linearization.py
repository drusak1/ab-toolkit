"""Linearization for ratio metrics (Yandex method).

Input: per-user lists of session-level values. Tests ratio of sums.
"""
from __future__ import annotations

import numpy as np
from scipy import stats

from ab_calc.stats.result import TestResult


def _agg(rows: list) -> tuple[np.ndarray, np.ndarray]:
    x = np.array([np.sum(r) for r in rows], dtype=float)
    y = np.array([len(r) for r in rows], dtype=float)
    return x, y


def linearization_test(control: list, treatment: list, alpha: float = 0.05) -> TestResult:
    """control, treatment: list of lists (per-user session values)."""
    ax, ay = _agg(control)
    bx, by = _agg(treatment)
    coef = ax.sum() / ay.sum() if ay.sum() > 0 else 0.0
    a_lin = ax - coef * ay
    b_lin = bx - coef * by

    pvalue = float(stats.ttest_ind(a_lin, b_lin, equal_var=False).pvalue)
    diff = float(b_lin.mean() - a_lin.mean())
    se = float(np.sqrt(a_lin.var(ddof=1) / len(a_lin) + b_lin.var(ddof=1) / len(b_lin)))
    z = stats.norm.ppf(1 - alpha / 2)
    return TestResult("linearization", pvalue, diff, diff - z * se, diff + z * se, len(control), len(treatment))
