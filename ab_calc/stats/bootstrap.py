"""Bootstrap CI and difference tests. Vectorised numpy."""
from __future__ import annotations

import numpy as np
from scipy import stats as scistats

from ab_calc.stats.result import TestResult


def _resample(x: np.ndarray, n_boot: int, rng: np.random.Generator) -> np.ndarray:
    """Returns (n_boot, len(x)) resampled matrix."""
    idx = rng.integers(0, len(x), size=(n_boot, len(x)))
    return x[idx]


def bootstrap_mean_ci(x: np.ndarray, n_boot: int = 2000, alpha: float = 0.05, seed: int | None = None) -> tuple[float, float, float]:
    rng = np.random.default_rng(seed)
    x = np.asarray(x, dtype=float)
    boots = _resample(x, n_boot, rng).mean(axis=1)
    pe = float(x.mean())
    lo, hi = np.quantile(boots, [alpha / 2, 1 - alpha / 2])
    return pe, float(lo), float(hi)


def bootstrap_quantile_ci(x: np.ndarray, q: float, n_boot: int = 2000, alpha: float = 0.05, seed: int | None = None) -> tuple[float, float, float]:
    rng = np.random.default_rng(seed)
    x = np.asarray(x, dtype=float)
    boots = np.quantile(_resample(x, n_boot, rng), q, axis=1)
    pe = float(np.quantile(x, q))
    lo, hi = np.quantile(boots, [alpha / 2, 1 - alpha / 2])
    return pe, float(lo), float(hi)


def bootstrap_diff_test(
    control: np.ndarray,
    treatment: np.ndarray,
    stat: str = "mean",
    q: float = 0.5,
    n_boot: int = 2000,
    alpha: float = 0.05,
    seed: int | None = None,
) -> TestResult:
    """Bootstrap difference test. stat in {mean, median, quantile}.

    pvalue via normal approx on bootstrap distribution of diff.
    """
    rng = np.random.default_rng(seed)
    a, b = np.asarray(control, dtype=float), np.asarray(treatment, dtype=float)

    if stat == "mean":
        f = lambda m: m.mean(axis=1)
    elif stat == "median":
        f = lambda m: np.median(m, axis=1)
    elif stat == "quantile":
        f = lambda m: np.quantile(m, q, axis=1)
    else:
        raise ValueError(f"unknown stat: {stat}")

    boots_a = f(_resample(a, n_boot, rng))
    boots_b = f(_resample(b, n_boot, rng))
    diffs = boots_b - boots_a

    pe = float(f(b[None, :])[0] - f(a[None, :])[0])
    se = float(diffs.std(ddof=1))
    z = pe / se if se > 0 else 0.0
    pvalue = float(2 * (1 - scistats.norm.cdf(abs(z))))
    lo, hi = np.quantile(diffs, [alpha / 2, 1 - alpha / 2])
    return TestResult(f"bootstrap_{stat}", pvalue, pe, float(lo), float(hi), len(a), len(b))
