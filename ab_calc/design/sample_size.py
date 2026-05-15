"""Sample size and MDE for two-sample mean comparison (normal approx)."""
from __future__ import annotations

import numpy as np
from scipy import stats


def _z(alpha: float, beta: float) -> tuple[float, float]:
    t_alpha = stats.norm.ppf(1 - alpha / 2)
    t_beta = stats.norm.ppf(1 - beta)
    return t_alpha, t_beta


def sample_size_abs(effect: float, std: float, alpha: float = 0.05, beta: float = 0.2) -> int:
    """Per-group sample size for absolute effect on mean.

    effect: minimum detectable absolute difference in means.
    std: pooled standard deviation.
    """
    if effect <= 0 or std <= 0:
        raise ValueError("effect and std must be positive")
    t_alpha, t_beta = _z(alpha, beta)
    n = (t_alpha + t_beta) ** 2 * (2 * std ** 2) / (effect ** 2)
    return int(np.ceil(n))


def sample_size_rel(rel_effect: float, mean: float, std: float, alpha: float = 0.05, beta: float = 0.2) -> int:
    """Per-group sample size for relative effect (lift %)."""
    return sample_size_abs(rel_effect * mean, std, alpha, beta)


def mde_abs(n: int, std: float, alpha: float = 0.05, beta: float = 0.2) -> float:
    """Minimum detectable absolute effect at given per-group n."""
    if n <= 0 or std <= 0:
        raise ValueError("n and std must be positive")
    t_alpha, t_beta = _z(alpha, beta)
    return (t_alpha + t_beta) * np.sqrt(2 * std ** 2) / np.sqrt(n)


def mde_rel(n: int, mean: float, std: float, alpha: float = 0.05, beta: float = 0.2) -> float:
    """Minimum detectable relative effect (lift fraction)."""
    return mde_abs(n, std, alpha, beta) / mean
