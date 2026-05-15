"""CUPED — Controlled Experiments Using Pre-Experiment Data."""
from __future__ import annotations

import numpy as np
from scipy import stats

from ab_calc.stats.result import TestResult


def cuped_theta(y_all: np.ndarray, x_all: np.ndarray) -> float:
    """Estimate theta = cov(y, x) / var(x) on pooled control+treatment."""
    y, x = np.asarray(y_all, dtype=float), np.asarray(x_all, dtype=float)
    var_x = x.var()
    if var_x == 0:
        return 0.0
    return float(np.cov(x, y)[0, 1] / var_x)


def cuped_test(
    y_control: np.ndarray,
    y_treatment: np.ndarray,
    x_control: np.ndarray,
    x_treatment: np.ndarray,
    alpha: float = 0.05,
) -> TestResult:
    """CUPED-adjusted t-test. x = pre-experiment covariate."""
    yc, yt = np.asarray(y_control, dtype=float), np.asarray(y_treatment, dtype=float)
    xc, xt = np.asarray(x_control, dtype=float), np.asarray(x_treatment, dtype=float)

    theta = cuped_theta(np.concatenate([yc, yt]), np.concatenate([xc, xt]))
    yc_adj = yc - theta * xc
    yt_adj = yt - theta * xt

    pvalue = float(stats.ttest_ind(yc_adj, yt_adj, equal_var=False).pvalue)
    diff = float(yt_adj.mean() - yc_adj.mean())
    se = float(np.sqrt(yc_adj.var(ddof=1) / len(yc_adj) + yt_adj.var(ddof=1) / len(yt_adj)))
    z = stats.norm.ppf(1 - alpha / 2)
    return TestResult("cuped", pvalue, diff, diff - z * se, diff + z * se, len(yc), len(yt))
