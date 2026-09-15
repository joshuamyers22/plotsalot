"""Retain representative M6B exact, quadrature, RQMC, and work baselines."""

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

import numpy as np
import polars as pl
import scipy

from plotsalot import (
    analyze_categorical,
    analyze_ggbetweenstats,
    analyze_gghistostats,
    analyze_ggscatterstats,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "benchmarks" / "results" / "m6b-baseline.json"
REPEATS = 5
T = TypeVar("T")


def _measure(operation: Callable[[], T]) -> dict[str, int]:
    gc.collect()
    tracemalloc.start()
    started = time.perf_counter_ns()
    operation()
    elapsed = time.perf_counter_ns() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {"elapsed_ns": max(1, elapsed), "python_peak_bytes": max(1, peak)}


def _summary(operation: Callable[[], T]) -> dict[str, Any]:
    operation()
    samples = [_measure(operation) for _ in range(REPEATS)]
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


def run() -> dict[str, Any]:
    rng = np.random.default_rng(20260915)
    histogram = pl.DataFrame({"value": rng.normal(0.3, 1.0, 100_000)})
    correlation = pl.DataFrame(
        {
            "x": np.arange(1, 101, dtype=np.float64),
            "y": np.arange(1, 101, dtype=np.float64) * 0.2 + rng.normal(size=100),
        }
    )
    comparison = pl.DataFrame(
        {
            "group": np.repeat(np.arange(10), 20),
            "value": rng.normal(size=200) + np.repeat(np.arange(10), 20) / 10,
        }
    )
    categorical_rng = np.random.default_rng(20260915)
    categorical = pl.DataFrame(
        {
            "row": np.repeat(np.arange(4), 4),
            "column": np.tile(np.arange(4), 4),
            "count": categorical_rng.integers(0, 20, 16),
        }
    )
    resource_grid = {
        str(levels): {
            "rows": levels * 20,
            "levels": levels,
            "calculated_work": 8 * 4096 * (levels + 1),
        }
        for levels in (2, 10, 20)
    }
    return {
        "schema_version": 1,
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
            "numpy": np.__version__,
            "polars": pl.__version__,
            "scipy": scipy.__version__,
        },
        "cases": {
            "closed_form_one_sample_100000": _summary(
                lambda: analyze_gghistostats(
                    histogram, "value", type="bayes", prior_scale=1.0
                )
            ),
            "quadrature_correlation_100": _summary(
                lambda: analyze_ggscatterstats(correlation, "x", "y", type="bayes")
            ),
            "rqmc_comparison_10_by_20": _summary(
                lambda: analyze_ggbetweenstats(
                    comparison,
                    "group",
                    "value",
                    type="bayes",
                    p_adjust="none",
                    pairwise_display="all",
                    prior_location=0.0,
                    prior_scale=1.0,
                    random_seed=20260915,
                )
            ),
            "rqmc_categorical_4_by_4": _summary(
                lambda: analyze_categorical(
                    categorical,
                    "row",
                    "column",
                    counts="count",
                    type="bayes",
                    p_adjust="none",
                    pairwise_display="all",
                    random_seed=4,
                )
            ),
        },
        "resource_grid": resource_grid,
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
