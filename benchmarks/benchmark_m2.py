"""Retain M2 scatter and correlation-matrix benchmark distributions."""

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

from plotsalot import (
    analyze_ggcorrmat,
    analyze_ggscatterstats,
    render_ggcorrmat,
    render_ggscatterstats,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "benchmarks" / "results" / "m2-baseline.json"
SCATTER_SIZES = (10_000, 100_000, 1_000_000)
MATRIX_VARIABLES = (10, 25, 50)
MATRIX_ROWS = 10_000
REPEATS = 5
T = TypeVar("T")


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


def _summary(samples: list[dict[str, int]]) -> dict[str, Any]:
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


def _measure_phases(
    analyze: Callable[[], T], render: Callable[[T], object]
) -> dict[str, Any]:
    warm = analyze()
    warm_plot = render(warm)
    warm_plot.figure.clear()  # type: ignore[attr-defined]
    analysis_samples = [_measure(analyze, lambda _: None) for _ in range(REPEATS)]
    retained = analyze()
    render_samples = [
        _measure(
            lambda retained=retained: render(retained),
            lambda plot: plot.figure.clear(),  # type: ignore[attr-defined]
        )
        for _ in range(REPEATS)
    ]
    return {
        "analysis": _summary(analysis_samples),
        "render": _summary(render_samples),
    }


def run() -> dict[str, Any]:
    scatter_results: dict[str, Any] = {}
    for size in SCATTER_SIZES:
        rng = np.random.default_rng(20260914 + size)
        x = rng.standard_normal(size)
        data = pl.DataFrame({"x": x, "y": 0.4 * x + rng.standard_normal(size)})
        scatter_results[str(size)] = _measure_phases(
            lambda data=data: analyze_ggscatterstats(data, "x", "y"),
            render_ggscatterstats,
        )

    matrix_results: dict[str, Any] = {}
    for variables in MATRIX_VARIABLES:
        rng = np.random.default_rng(20261914 + variables)
        values = rng.standard_normal((MATRIX_ROWS, variables))
        values[:, 1:] += values[:, :1] * 0.15
        columns = tuple(f"v{index:02d}" for index in range(variables))
        data = pl.DataFrame(values, schema=columns, orient="row")
        phases = _measure_phases(
            lambda data=data, columns=columns: analyze_ggcorrmat(data, columns),
            render_ggcorrmat,
        )
        matrix_results[str(variables)] = {"rows": MATRIX_ROWS, **phases}

    return {
        "schema_version": 1,
        "scope": ["ggscatterstats_pearson", "ggcorrmat_pearson"],
        "measurement": {
            "clock": "time.perf_counter_ns",
            "memory": "tracemalloc incremental Python allocation peak",
            "input_frame_allocation": "outside measured phases",
            "repeats": REPEATS,
            "scatter_seed_rule": "20260914 + row_count",
            "matrix_seed_rule": "20261914 + variable_count",
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
        "scatter_results": scatter_results,
        "matrix_results": matrix_results,
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
