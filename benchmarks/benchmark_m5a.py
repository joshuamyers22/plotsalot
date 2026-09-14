"""Retain M5A coefficient selection, adaptation, analysis, and render baselines."""

from __future__ import annotations

import argparse
import gc
import json
import platform
import statistics
import time
import tracemalloc
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

import matplotlib
import numpy as np
import polars as pl
import scipy
import statsmodels
import statsmodels.api as sm

from plotsalot import analyze_ggcoefstats, render_ggcoefstats, select_coefficients

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "benchmarks" / "results" / "m5a-baseline.json"
TERM_COUNTS = (10, 100, 500)
REPEATS = 5
T = TypeVar("T")
DECLARATIONS = {
    "estimate_label": "synthetic coefficient",
    "effect_scale": "linear predictor",
    "effect_direction": "positive is higher",
    "effect_units": "outcome units",
}


def _measure(
    operation: Callable[[], T], cleanup: Callable[[T], None]
) -> dict[str, int]:
    gc.collect()
    tracemalloc.start()
    started = time.perf_counter_ns()
    value = operation()
    elapsed = time.perf_counter_ns() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    cleanup(value)
    return {"elapsed_ns": elapsed, "python_peak_bytes": peak}


def _operation(
    operation: Callable[[], T], cleanup: Callable[[T], None] = lambda _: None
) -> dict[str, Any]:
    cleanup(operation())
    samples = [_measure(operation, cleanup) for _ in range(REPEATS)]
    elapsed = [sample["elapsed_ns"] for sample in samples]
    memory = [sample["python_peak_bytes"] for sample in samples]
    return {
        "samples": samples,
        "elapsed_ns": {
            "min": min(elapsed),
            "median": int(statistics.median(elapsed)),
            "max": max(elapsed),
        },
        "python_peak_bytes": {
            "min": min(memory),
            "median": int(statistics.median(memory)),
            "max": max(memory),
        },
    }


def _frame(count: int) -> pl.DataFrame:
    position = np.arange(count, dtype=np.float64)
    estimate = np.sin(position / 7.0)
    error = 0.1 + (position % 5.0) * 0.01
    return pl.DataFrame(
        {
            "term": [f"term-{index + 1}" for index in range(count)],
            "estimate": estimate,
            "conf_low": estimate - 1.96 * error,
            "conf_high": estimate + 1.96 * error,
            "standard_error": error,
            "statistic_kind": ["z"] * count,
            "statistic": estimate / error,
            "p_value": scipy.stats.norm.sf(np.abs(estimate / error)) * 2.0,
        }
    )


def _analyze(data: object):
    return analyze_ggcoefstats(data, **DECLARATIONS, stats_labels=False)


def _phases(data: pl.DataFrame) -> dict[str, Any]:
    analysis = _analyze(data)
    return {
        "selection": _operation(lambda: select_coefficients(data)),
        "analysis": _operation(lambda: _analyze(data)),
        "render": _operation(
            lambda: render_ggcoefstats(analysis), lambda plot: plot.figure.clear()
        ),
    }


def _fitted_ols() -> object:
    rows = np.arange(100.0)
    design = np.column_stack(
        (np.ones(100), np.sin(rows / 11.0), np.cos(rows / 13.0), rows / 100.0)
    )
    outcome = (
        1.0
        + 0.4 * design[:, 1]
        - 0.2 * design[:, 2]
        + 0.1 * design[:, 3]
        + np.sin(rows) * 0.05
    )
    return sm.OLS(outcome, design).fit(cov_type="HC3", use_t=False)


def run() -> dict[str, Any]:
    table_results = {str(count): _phases(_frame(count)) for count in TERM_COUNTS}
    fitted = _fitted_ols()
    return {
        "schema_version": 1,
        "scope": [
            "coefficient_table_selection",
            "coefficient_analysis",
            "statsmodels_ols_adapter",
            "ggcoefstats_coefficient_render",
        ],
        "measurement": {
            "clock": "time.perf_counter_ns",
            "memory": "tracemalloc incremental Python allocation peak",
            "input_frame_and_model_fit": "outside measured phases",
            "repeats": REPEATS,
        },
        "host": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        },
        "versions": {
            "matplotlib": matplotlib.__version__,
            "numpy": np.__version__,
            "polars": pl.__version__,
            "scipy": scipy.__version__,
            "statsmodels": statsmodels.__version__,
        },
        "table_results": table_results,
        "model_adapter": _operation(lambda: _analyze(fitted)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
