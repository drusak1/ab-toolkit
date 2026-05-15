import numpy as np

from ab_calc.multitest import benjamini_hochberg, bonferroni, holm
from ab_calc.ratio import linearization_test
from ab_calc.simulator import simulate_aa, simulate_power


def test_bonferroni_basic():
    p = np.array([0.001, 0.04, 0.3, 0.8])
    r = bonferroni(p, 0.05)
    assert r[0] and not r[1] and not r[2] and not r[3]


def test_holm_step_down():
    p = np.array([0.001, 0.02, 0.04, 0.5])
    r = holm(p, 0.05)
    assert r[0]
    assert r.sum() >= 1


def test_bh_more_powerful_than_bonferroni():
    p = np.array([0.001, 0.01, 0.02, 0.03, 0.5])
    r_b = bonferroni(p, 0.05)
    r_bh = benjamini_hochberg(p, 0.05)
    assert r_bh.sum() >= r_b.sum()


def test_linearization_runs():
    rng = np.random.default_rng(0)
    a = [rng.exponential(1, rng.integers(1, 10)).tolist() for _ in range(200)]
    b = [rng.exponential(1.2, rng.integers(1, 10)).tolist() for _ in range(200)]
    res = linearization_test(a, b)
    assert res.method == "linearization"
    assert 0 <= res.pvalue <= 1


def test_aa_close_to_alpha():
    rng = np.random.default_rng(0)
    values = rng.normal(0, 1, 10000)
    rate = simulate_aa(values, sample_size=500, n_iter=500, alpha=0.05, seed=0)
    assert 0.02 < rate < 0.08


def test_power_grows_with_effect():
    rng = np.random.default_rng(0)
    values = rng.normal(100, 10, 5000)
    low = simulate_power(values, 500, 0.01, "multiplicative", 300, seed=0)
    high = simulate_power(values, 500, 0.05, "multiplicative", 300, seed=0)
    assert high > low
