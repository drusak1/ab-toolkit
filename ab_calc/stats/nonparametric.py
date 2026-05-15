from __future__ import annotations

import numpy as np
from scipy import stats

from ab_calc.stats.result import TestResult


def mann_whitney(control: np.ndarray, treatment: np.ndarray, alpha: float = 0.05) -> TestResult:
    """Mann-Whitney U test. Effect = median diff. CI omitted (returns NaN)."""
    a, b = np.asarray(control, dtype=float), np.asarray(treatment, dtype=float)
    pvalue = float(stats.mannwhitneyu(a, b, alternative="two-sided").pvalue)
    effect = float(np.median(b) - np.median(a))
    return TestResult("mann_whitney", pvalue, effect, float("nan"), float("nan"), len(a), len(b))
