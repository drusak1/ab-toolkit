"""Stratified split, stratified variance, post-stratification test."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from ab_calc.stats.result import TestResult


def stratified_split(strata: np.ndarray, seed: int | None = None) -> np.ndarray:
    """Balanced 50/50 split inside each stratum. Returns array of {0, 1}."""
    rng = np.random.default_rng(seed)
    strata = np.asarray(strata)
    groups = np.zeros(len(strata), dtype=int)
    for s in np.unique(strata):
        idx = np.where(strata == s)[0]
        rng.shuffle(idx)
        cut = len(idx) // 2
        groups[idx[cut:]] = 1
    return groups


def stratified_var(values: np.ndarray, strata: np.ndarray) -> float:
    """Population variance under stratified sampling: sum_k w_k * var_k."""
    df = pd.DataFrame({"v": values, "s": strata})
    var_per_strat = df.groupby("s")["v"].var(ddof=1)
    weights = df["s"].value_counts(normalize=True)
    return float((var_per_strat * weights).dropna().sum())


def stratified_test(
    control: np.ndarray,
    treatment: np.ndarray,
    strata_control: np.ndarray,
    strata_treatment: np.ndarray,
    alpha: float = 0.05,
) -> TestResult:
    """Post-stratification difference-in-means test.

    Weighted estimate: sum_k w_k * (mean_B_k - mean_A_k),
    w_k = pooled stratum share. Variance is the weighted sum of
    within-stratum SE^2. Lower variance than naive t-test when the
    metric correlates with the stratum.
    """
    a = pd.DataFrame({"v": np.asarray(control, dtype=float), "s": np.asarray(strata_control)})
    b = pd.DataFrame({"v": np.asarray(treatment, dtype=float), "s": np.asarray(strata_treatment)})
    total = len(a) + len(b)

    est, var = 0.0, 0.0
    for s in pd.unique(pd.concat([a["s"], b["s"]])):
        ak = a.loc[a["s"] == s, "v"].to_numpy()
        bk = b.loc[b["s"] == s, "v"].to_numpy()
        if len(ak) < 2 or len(bk) < 2:
            continue
        w = (len(ak) + len(bk)) / total
        diff_k = bk.mean() - ak.mean()
        se2_k = ak.var(ddof=1) / len(ak) + bk.var(ddof=1) / len(bk)
        est += w * diff_k
        var += (w ** 2) * se2_k

    se = float(np.sqrt(var))
    z = est / se if se > 0 else 0.0
    pvalue = float(2 * (1 - stats.norm.cdf(abs(z))))
    crit = stats.norm.ppf(1 - alpha / 2)
    return TestResult(
        "stratified", pvalue, float(est),
        float(est - crit * se), float(est + crit * se),
        len(a), len(b),
    )
