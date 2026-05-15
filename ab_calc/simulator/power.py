"""Monte-Carlo power / FPR by non-overlapping shuffle-split of historical data."""
from __future__ import annotations

import numpy as np
from scipy import stats


def _split_indices(rng: np.random.Generator, n_total: int, sample_size: int) -> tuple[np.ndarray, np.ndarray]:
    """Shuffle indices, take first 2*sample_size, split in half. Guarantees no overlap.

    If 2*sample_size > n_total, clamps sample_size to n_total // 2.
    """
    eff = min(sample_size, n_total // 2)
    idx = rng.permutation(n_total)[: 2 * eff]
    return idx[:eff], idx[eff:]


def simulate_aa(values: np.ndarray, sample_size: int, n_iter: int = 1000, alpha: float = 0.05, seed: int | None = None) -> float:
    """Type-I error estimate via non-overlapping A/A split."""
    rng = np.random.default_rng(seed)
    v = np.asarray(values, dtype=float)
    rejects = 0
    for _ in range(n_iter):
        ai, bi = _split_indices(rng, len(v), sample_size)
        p = stats.ttest_ind(v[ai], v[bi], equal_var=False).pvalue
        rejects += int(p < alpha)
    return rejects / n_iter


def simulate_power(
    values: np.ndarray,
    sample_size: int,
    effect: float,
    mode: str = "multiplicative",
    n_iter: int = 1000,
    alpha: float = 0.05,
    seed: int | None = None,
) -> float:
    """Power estimate via non-overlapping A/B split with injected effect."""
    rng = np.random.default_rng(seed)
    v = np.asarray(values, dtype=float)
    mean_ = float(v.mean())
    rejects = 0
    for _ in range(n_iter):
        ai, bi = _split_indices(rng, len(v), sample_size)
        a, b = v[ai], v[bi].copy()
        if mode == "additive":
            b = b + mean_ * effect
        elif mode == "multiplicative":
            b = b * (1 + effect)
        else:
            raise ValueError(f"unknown mode: {mode}")
        p = stats.ttest_ind(a, b, equal_var=False).pvalue
        rejects += int(p < alpha)
    return rejects / n_iter
