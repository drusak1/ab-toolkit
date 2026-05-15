"""Multiple testing corrections. Return boolean reject mask (True = significant)."""
from __future__ import annotations

import numpy as np


def bonferroni(pvalues: np.ndarray, alpha: float = 0.05) -> np.ndarray:
    p = np.asarray(pvalues, dtype=float)
    return p < alpha / len(p)


def holm(pvalues: np.ndarray, alpha: float = 0.05) -> np.ndarray:
    """Holm-Bonferroni step-down."""
    p = np.asarray(pvalues, dtype=float)
    m = len(p)
    order = np.argsort(p)
    reject = np.zeros(m, dtype=bool)
    for rank, idx in enumerate(order):
        if p[idx] < alpha / (m - rank):
            reject[idx] = True
        else:
            break
    return reject


def benjamini_hochberg(pvalues: np.ndarray, alpha: float = 0.05) -> np.ndarray:
    """BH FDR control."""
    p = np.asarray(pvalues, dtype=float)
    m = len(p)
    order = np.argsort(p)
    thresholds = alpha * (np.arange(1, m + 1)) / m
    sorted_p = p[order]
    below = sorted_p <= thresholds
    if not below.any():
        return np.zeros(m, dtype=bool)
    k = np.max(np.where(below)[0])
    reject = np.zeros(m, dtype=bool)
    reject[order[: k + 1]] = True
    return reject
