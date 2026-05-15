"""Bayesian posterior for mean diff under normal approx (no prior, large-sample)."""
from __future__ import annotations

import numpy as np
from scipy import stats


def posterior_diff(control: np.ndarray, treatment: np.ndarray, alpha: float = 0.05) -> dict:
    """Posterior of (mu_B - mu_A) under uninformative prior + large-sample normal approx.

    Returns: mean, std, ci_low, ci_high (credible), chance_to_win, density_x, density_y.
    """
    a, b = np.asarray(control, dtype=float), np.asarray(treatment, dtype=float)
    mu = float(b.mean() - a.mean())
    se = float(np.sqrt(b.var(ddof=1) / len(b) + a.var(ddof=1) / len(a)))
    z = stats.norm.ppf(1 - alpha / 2)
    ci_low, ci_high = mu - z * se, mu + z * se
    chance = float(1 - stats.norm.cdf(0, loc=mu, scale=se))

    # Density curve: 100 points across ±4 SE
    if se > 0:
        xs = np.linspace(mu - 4 * se, mu + 4 * se, 100)
        ys = stats.norm.pdf(xs, loc=mu, scale=se)
    else:
        xs = np.array([mu])
        ys = np.array([1.0])
    return {
        "mean": mu,
        "std": se,
        "ci_low": float(ci_low),
        "ci_high": float(ci_high),
        "chance_to_win": chance,
        "density_x": xs.tolist(),
        "density_y": ys.tolist(),
    }
