"""Outlier trimming via symmetric quantile cuts."""
from __future__ import annotations

import numpy as np


def trim_outliers(x: np.ndarray, q: float = 0.01) -> np.ndarray:
    """Drop values outside [q, 1-q] quantile range."""
    x = np.asarray(x, dtype=float)
    if not 0 < q < 0.5:
        raise ValueError("q must be in (0, 0.5)")
    lo, hi = np.quantile(x, [q, 1 - q])
    return x[(x >= lo) & (x <= hi)]
