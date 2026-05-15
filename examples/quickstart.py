"""End-to-end demo: design → simulate → analyse → multi-test."""
import numpy as np

from ab_calc.design import sample_size_rel
from ab_calc.multitest import holm
from ab_calc.simulator import simulate_aa, simulate_power
from ab_calc.stats import ttest
from ab_calc.variance_reduction import cuped_test

rng = np.random.default_rng(42)

print("=== 1. Design ===")
historical = rng.lognormal(5, 1, 50000)
mean, std = float(historical.mean()), float(historical.std())
n = sample_size_rel(rel_effect=0.03, mean=mean, std=std, alpha=0.05, beta=0.2)
print(f"mean={mean:.1f}  std={std:.1f}  n_per_group={n}  n_total={2 * n}")

print("\n=== 2. A/A validation ===")
fpr = simulate_aa(historical, sample_size=n, n_iter=500, seed=0)
print(f"empirical FPR (should ~0.05): {fpr:.3f}")

print("\n=== 3. Power check ===")
power = simulate_power(historical, sample_size=n, effect=0.03, n_iter=500, seed=0)
print(f"empirical power (should ~0.80): {power:.3f}")

print("\n=== 4. Run a single experiment ===")
control = rng.choice(historical, size=n, replace=False)
treatment = rng.choice(historical, size=n, replace=False) * 1.03
res = ttest(control, treatment)
print(f"t-test: pvalue={res.pvalue:.4f}  effect={res.effect:.2f}  CI=[{res.ci_low:.2f},{res.ci_high:.2f}]  sig={res.is_significant}")

print("\n=== 5. CUPED with pre-period covariate ===")
x_c = rng.choice(historical, n)
x_t = rng.choice(historical, n)
y_c = 0.6 * x_c + rng.normal(0, 50, n)
y_t = 0.6 * x_t + rng.normal(0, 50, n) + 5
raw = ttest(y_c, y_t)
cup = cuped_test(y_c, y_t, x_c, x_t)
print(f"raw t-test pvalue: {raw.pvalue:.4f}")
print(f"CUPED pvalue:      {cup.pvalue:.4f}  (variance reduction)")

print("\n=== 6. Multiple tests ===")
pvalues = [0.001, 0.012, 0.03, 0.12, 0.4]
reject = holm(np.array(pvalues), 0.05)
for p, r in zip(pvalues, reject):
    print(f"  p={p:.3f} -> {'SIG' if r else '-'}")
