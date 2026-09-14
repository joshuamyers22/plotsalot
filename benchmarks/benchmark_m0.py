"""Retain separate M0 analysis and rendering benchmark distributions."""

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

from plotsalot import analyze_gghistostats, render_gghistostats

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "benchmarks" / "results" / "m0-baseline.json"
SIZES = (10_000, 100_000, 1_000_000)
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


def run() -> dict[str, Any]:
    results: dict[str, Any] = {}
    for size in SIZES:
        rng = np.random.default_rng(20260914 + size)
        data = pl.DataFrame({"value": rng.standard_normal(size)})

        # Warm imports/caches outside retained samples.
        warm = analyze_gghistostats(data, "value")
        warm_plot = render_gghistostats(warm)
        warm_plot.figure.clear()

        analysis_samples = [
            _measure(
                lambda data=data: analyze_gghistostats(data, "value"),
                lambda _: None,
            )
            for _ in range(REPEATS)
        ]
        retained_analysis = analyze_gghistostats(data, "value")
        render_samples = [
            _measure(
                lambda analysis=retained_analysis: render_gghistostats(analysis),
                lambda plot: plot.figure.clear(),
            )
            for _ in range(REPEATS)
        ]
        results[str(size)] = {
            "analysis": _summary(analysis_samples),
            "render": _summary(render_samples),
        }

    return {
        "schema_version": 1,
        "scope": "gghistostats_one_sample_parametric",
        "measurement": {
            "clock": "time.perf_counter_ns",
            "memory": "tracemalloc incremental Python allocation peak",
            "repeats": REPEATS,
            "seed_rule": "20260914 + row_count",
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
        "results": results,
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
