import numpy as np

from ab_calc.stats import bootstrap_diff_test, mann_whitney, ttest, welch_ttest


def test_ttest_no_effect():
    rng = np.random.default_rng(0)
    a = rng.normal(0, 1, 1000)
    b = rng.normal(0, 1, 1000)
    res = ttest(a, b)
    assert res.pvalue > 0.05


def test_ttest_with_effect():
    rng = np.random.default_rng(0)
    a = rng.normal(0, 1, 500)
    b = rng.normal(1, 1, 500)
    res = ttest(a, b)
    assert res.pvalue < 0.001
    assert res.effect > 0.5
    assert res.is_significant


def test_welch_unequal_var():
    rng = np.random.default_rng(1)
    a = rng.normal(0, 1, 200)
    b = rng.normal(0.5, 5, 200)
    res = welch_ttest(a, b)
    assert res.method == "welch_ttest"


def test_mann_whitney_runs():
    rng = np.random.default_rng(2)
    a, b = rng.exponential(1, 200), rng.exponential(1.5, 200)
    res = mann_whitney(a, b)
    assert res.pvalue < 0.05


def test_bootstrap_mean_recovers_effect():
    rng = np.random.default_rng(3)
    a = rng.normal(0, 1, 500)
    b = rng.normal(0.5, 1, 500)
    res = bootstrap_diff_test(a, b, stat="mean", n_boot=500, seed=0)
    assert res.pvalue < 0.01
    assert 0.3 < res.effect < 0.7
