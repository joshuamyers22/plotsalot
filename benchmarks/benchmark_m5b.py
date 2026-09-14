"""Retain M5B study selection, meta-analysis, and rendering baselines."""

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

from plotsalot import analyze_ggcoefstats, render_ggcoefstats, select_study_effects

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "benchmarks" / "results" / "m5b-baseline.json"
STUDY_COUNTS = (3, 10, 100, 500)
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


def _measure_operation(
    operation: Callable[[], T], cleanup: Callable[[T], None] = lambda _: None
) -> dict[str, Any]:
    cleanup(operation())
    return _summary([_measure(operation, cleanup) for _ in range(REPEATS)])


def _frame(
    studies: int, *, unequal_variance: bool, heterogeneity: bool
) -> pl.DataFrame:
    positions = np.arange(studies, dtype=np.float64)
    estimates = (
        0.2 + 0.8 * np.where(positions % 2.0 == 0.0, -1.0, 1.0)
        if heterogeneity
        else np.full(studies, 0.2)
    )
    standard_errors = (
        0.1 + 0.3 * (positions + 1.0) / studies
        if unequal_variance
        else np.full(studies, 0.2)
    )
    return pl.DataFrame(
        {
            "term": [f"study-{index + 1}" for index in range(studies)],
            "estimate": estimates,
            "standard_error": standard_errors,
        }
    )


def _analyze(data: pl.DataFrame):
    return analyze_ggcoefstats(
        data,
        meta_analytic_effect=True,
        estimand="mean synthetic treatment effect",
        effect_scale="mean difference",
        effect_direction="positive favors treatment",
        effect_units="points",
        stats_labels=False,
    )


def _phases(data: pl.DataFrame) -> dict[str, Any]:
    selection = _measure_operation(lambda: select_study_effects(data))
    analysis = _measure_operation(lambda: _analyze(data))
    retained = _analyze(data)
    render = _measure_operation(
        lambda: render_ggcoefstats(retained),
        lambda plot: plot.figure.clear(),
    )
    return {"selection": selection, "analysis": analysis, "render": render}


def run() -> dict[str, Any]:
    results: dict[str, Any] = {}
    for studies in STUDY_COUNTS:
        cases: dict[str, Any] = {}
        for variance_name, unequal_variance in (("equal", False), ("unequal", True)):
            for heterogeneity_name, heterogeneity in (
                ("zero", False),
                ("positive", True),
            ):
                case = f"{variance_name}_variance_{heterogeneity_name}_heterogeneity"
                cases[case] = _phases(
                    _frame(
                        studies,
                        unequal_variance=unequal_variance,
                        heterogeneity=heterogeneity,
                    )
                )
        results[str(studies)] = cases
    return {
        "schema_version": 1,
        "scope": [
            "study_effect_selection",
            "reml_modified_hartung_knapp_meta_analysis",
            "ggcoefstats_meta_render",
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
            "statsmodels": statsmodels.__version__,
        },
        "study_results": results,
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
