import pytest

from ab_calc.design import mde_abs, mde_rel, sample_size_abs, sample_size_rel


def test_sample_size_increases_with_smaller_effect():
    n_big = sample_size_abs(10, 100, 0.05, 0.2)
    n_small = sample_size_abs(5, 100, 0.05, 0.2)
    assert n_small > n_big


def test_sample_size_classic_value():
    # (1.96 + 1.282)^2 * 2 * 200^2 / 20^2 ~= 2102
    n = sample_size_abs(20, 200, 0.05, 0.1)
    assert 2080 <= n <= 2130


def test_mde_inverse_of_sample_size():
    n = sample_size_abs(20, 200, 0.05, 0.2)
    m = mde_abs(n, 200, 0.05, 0.2)
    assert abs(m - 20) / 20 < 0.05


def test_relative_consistency():
    mean, lift = 500, 0.1
    n_rel = sample_size_rel(lift, mean, 100, 0.05, 0.2)
    n_abs = sample_size_abs(mean * lift, 100, 0.05, 0.2)
    assert n_rel == n_abs


def test_invalid_inputs():
    with pytest.raises(ValueError):
        sample_size_abs(-1, 100)
    with pytest.raises(ValueError):
        mde_abs(0, 100)


def test_mde_rel():
    m = mde_rel(10000, 500, 100, 0.05, 0.2)
    assert m > 0
