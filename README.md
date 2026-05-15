# AB Calc

Pragmatic AB testing toolkit. Python core + FastAPI + React UI. Stats lifted and cleaned up from the Karpov.Courses *Simulator AB* programme.

## Modules

| Module | What it does |
|---|---|
| `ab_calc.design` | Sample size, MDE (absolute/relative) |
| `ab_calc.stats` | t-test, Welch, Mann-Whitney, bootstrap diff (mean/median/quantile) |
| `ab_calc.variance_reduction` | CUPED, stratified split + var, outlier trimming |
| `ab_calc.ratio` | Linearization for ratio metrics (Yandex method) |
| `ab_calc.multitest` | Bonferroni, Holm, Benjamini-Hochberg |
| `ab_calc.simulator` | Monte-Carlo FPR / power on historical data |
| `ab_calc.api` | FastAPI exposing all of the above |

## Install

```bash
cd ab-toolkit
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -q              # 22 tests
python examples/quickstart.py
```

## Run API

```bash
uvicorn ab_calc.api.app:app --reload --port 8000
# Swagger: http://localhost:8000/docs
```

## Run Frontend (Stage 2)

```bash
cd frontend
npm install
npm run dev
```

## Roadmap

### Stage 1 — Python core + FastAPI ✅
- All stats modules, 22 passing tests, FastAPI endpoints, quickstart demo.

### Stage 2 — React UI (in progress)
- Vite + TS + Tailwind. Tabs: Design / Analyse / Simulator / Multitest.
- CSV upload + chart rendering (recharts).

### Stage 3 — Rust hot path (stretch)
- Port bootstrap + Monte-Carlo simulator to Rust via PyO3 (10-100x speedup expected).
- Stats lib stays Python (scipy is hard to beat for one-off t-tests).
- Optional: full Rust rewrite of stats (statrs + ndarray) once API surface stabilises.

## Provenance

Stats methods adapted from `karpov.courses/simulator_ab` notebooks (originally in `~/Desktop/python/old_folders/KK/AB_test/tasks/sim_ab/`). Rewritten as a clean library with type hints, vectorisation, and tests.
