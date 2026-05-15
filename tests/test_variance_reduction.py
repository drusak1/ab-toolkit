import numpy as np

from ab_calc.stats import welch_ttest
from ab_calc.variance_reduction import (
    cuped_test,
    cuped_theta,
    stratified_split,
    stratified_var,
    trim_outliers,
)


def test_cuped_reduces_variance():
    rng = np.random.default_rng(0)
    n = 5000
    x_c = rng.normal(100, 20, n)
    x_t = rng.normal(100, 20, n)
    y_c = x_c + rng.normal(0, 5, n)
    y_t = x_t + 1.0 + rng.normal(0, 5, n)

    raw = welch_ttest(y_c, y_t)
    cuped = cuped_test(y_c, y_t, x_c, x_t)
    assert cuped.pvalue < raw.pvalue
    assert cuped.method == "cuped"


def test_cuped_theta_zero_var():
    assert cuped_theta(np.array([1, 2, 3]), np.array([5, 5, 5])) == 0.0


def test_stratified_split_balanced():
    strata = np.array([0] * 100 + [1] * 200 + [2] * 50)
    groups = stratified_split(strata, seed=0)
    for s in np.unique(strata):
        mask = strata == s
        diff = abs(groups[mask].sum() - (mask.sum() - groups[mask].sum()))
        assert diff <= 1


def test_stratified_var_positive():
    rng = np.random.default_rng(0)
    v = rng.normal(0, 1, 1000)
    s = rng.integers(0, 5, 1000)
    assert stratified_var(v, s) > 0


def test_trim_outliers_removes_tails():
    x = np.concatenate([np.zeros(98), [1e6, -1e6]])
    trimmed = trim_outliers(x, q=0.02)
    assert 1e6 not in trimmed
    assert -1e6 not in trimmed
