"""Retain M6A robust analysis, resampling, rendering, and budget baselines."""

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
from typing import Any, TypeVar, cast

import matplotlib
import numpy as np
import polars as pl
import scipy

from plotsalot import (
    RobustCorrelationResult,
    analyze_ggbetweenstats,
    analyze_gghistostats,
    analyze_ggscatterstats,
    analyze_ggwithinstats,
    render_ggbetweenstats,
    render_gghistostats,
    render_ggscatterstats,
    render_ggwithinstats,
)
from plotsalot.robust import HARD_MAX_RESAMPLE_WORK

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "benchmarks" / "results" / "m6a-baseline.json"
ROW_COUNTS = (10_000, 100_000, 1_000_000)
MATRIX_VARIABLE_COUNTS = (10, 25, 50)
REPEATS = 5
T = TypeVar("T")


def _measure(
    operation: Callable[[], T], cleanup: Callable[[T], None] = lambda _: None
) -> dict[str, int]:
    gc.collect()
    tracemalloc.start()
    started = time.perf_counter_ns()
    value = operation()
    elapsed = time.perf_counter_ns() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    cleanup(value)
    return {
        "elapsed_ns": max(1, elapsed),
        "python_peak_bytes": max(1, peak),
    }


def _summary(
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


def _histogram_results() -> dict[str, Any]:
    results: dict[str, Any] = {}
    for rows in ROW_COUNTS:
        rng = np.random.default_rng(20260914 + rows)
        values = rng.standard_t(5, rows)
        values[::997] *= 100.0
        data = pl.DataFrame({"value": values})
        analysis = analyze_gghistostats(data, "value", type="robust")
        results[str(rows)] = {
            "analysis": _summary(
                lambda data=data: analyze_gghistostats(data, "value", type="robust")
            ),
            "render": _summary(
                lambda analysis=analysis: render_gghistostats(analysis),
                lambda plot: plot.figure.clear(),
            ),
        }
    return results


def _resampling_result() -> dict[str, Any]:
    rows = 1_000
    rng = np.random.default_rng(20260914)
    x = rng.standard_t(5, rows)
    y = 0.35 * x + rng.standard_t(5, rows)
    data = pl.DataFrame({"x": x, "y": y})
    analysis = analyze_ggscatterstats(
        data,
        "x",
        "y",
        type="robust",
        random_seed=20260914,
        bootstrap_resamples=999,
    )
    result = cast(RobustCorrelationResult, analysis.result)
    return {
        "rows": rows,
        "resamples": 999,
        "calculated_work": result.resampling.calculated_work,
        "resampling_analysis": _summary(
            lambda: analyze_ggscatterstats(
                data,
                "x",
                "y",
                type="robust",
                random_seed=20260914,
                bootstrap_resamples=999,
            )
        ),
        "render": _summary(
            lambda: render_ggscatterstats(analysis),
            lambda plot: plot.figure.clear(),
        ),
    }


def _comparison_results() -> dict[str, Any]:
    rng = np.random.default_rng(20260914)
    between = pl.DataFrame(
        {
            "group": np.repeat(np.arange(20), 100),
            "value": rng.standard_t(5, 2_000) + np.repeat(np.arange(20), 100) / 20,
        }
    )
    between_analysis = analyze_ggbetweenstats(between, "group", "value", type="robust")
    subjects = np.repeat(np.arange(100), 10)
    conditions = np.tile(np.arange(10), 100)
    within = pl.DataFrame(
        {
            "subject": subjects,
            "condition": conditions,
            "value": rng.standard_t(5, 1_000) + conditions / 10,
        }
    )
    within_analysis = analyze_ggwithinstats(
        within,
        "condition",
        "value",
        subject_id="subject",
        type="robust",
    )
    return {
        "between_20_levels": {
            "rows": between.height,
            "analysis": _summary(
                lambda: analyze_ggbetweenstats(between, "group", "value", type="robust")
            ),
            "render": _summary(
                lambda: render_ggbetweenstats(between_analysis),
                lambda plot: plot.figure.clear(),
            ),
        },
        "within_100_by_10": {
            "rows": within.height,
            "analysis": _summary(
                lambda: analyze_ggwithinstats(
                    within,
                    "condition",
                    "value",
                    subject_id="subject",
                    type="robust",
                )
            ),
            "render": _summary(
                lambda: render_ggwithinstats(within_analysis),
                lambda plot: plot.figure.clear(),
            ),
        },
    }


def _resource_grid() -> dict[str, Any]:
    scatter: dict[str, Any] = {}
    for rows in ROW_COUNTS:
        work = rows * 999
        scatter[str(rows)] = {
            "rows": rows,
            "resamples": 999,
            "calculated_work": work,
            "default_ceiling_accepts": work <= 100_000_000,
            "hard_ceiling_accepts": work <= HARD_MAX_RESAMPLE_WORK,
        }
    matrix: dict[str, Any] = {}
    for variables in MATRIX_VARIABLE_COUNTS:
        pairs = variables * (variables - 1) // 2
        work = 10_000 * 999 * pairs
        matrix[str(variables)] = {
            "rows": 10_000,
            "variables": variables,
            "pairs": pairs,
            "resamples": 999,
            "calculated_work": work,
            "default_ceiling_accepts": work <= 100_000_000,
            "hard_ceiling_accepts": work <= HARD_MAX_RESAMPLE_WORK,
        }
    return {"scatter": scatter, "matrix": matrix}


def run() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "scope": [
            "m6a_fixed_trim_analysis",
            "m6a_paired_percentile_bootstrap",
            "m6a_comparison_analysis",
            "m6a_semantic_rendering",
            "m6a_resource_preflight",
        ],
        "measurement": {
            "clock": "time.perf_counter_ns",
            "memory": "tracemalloc incremental Python allocation peak",
            "input_frame_allocation": "outside measured phases",
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
        },
        "histogram_results": _histogram_results(),
        "representative_resampling": _resampling_result(),
        "comparison_results": _comparison_results(),
        "resource_grid": _resource_grid(),
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
