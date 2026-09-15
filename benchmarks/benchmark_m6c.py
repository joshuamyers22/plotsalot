"""Retain M6C coefficient/meta analysis, rendering, and work baselines."""

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

from plotsalot import analyze_ggcoefstats, render_ggcoefstats

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "benchmarks" / "results" / "m6c-baseline.json"
COEFFICIENT_COUNTS = (10, 100, 500)
ROBUST_META_COUNTS = (10, 100, 500)
BAYESIAN_META_COUNTS = (3, 10, 100, 500)
REPEATS = 5
T = TypeVar("T")

COEFFICIENT_DECLARATIONS = {
    "estimate_label": "synthetic coefficient",
    "effect_scale": "linear predictor",
    "effect_direction": "positive is higher",
    "effect_units": "outcome units",
    "stats_labels": False,
}
META_DECLARATIONS = {
    "meta_analytic_effect": True,
    "estimand": "synthetic population effect",
    "effect_scale": "mean difference",
    "effect_direction": "positive favors treatment",
    "effect_units": "points",
    "stats_labels": False,
}


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


def _coefficient_frame(count: int, *, posterior: bool) -> pl.DataFrame:
    position = np.arange(count, dtype=np.float64)
    point = np.sin(position / 11.0)
    error = 0.1 + (position % 5.0) * 0.01
    common: dict[str, object] = {
        "term": [f"term-{index + 1}" for index in range(count)]
    }
    if posterior:
        probability = 1.0 / (1.0 + np.exp(-point / error))
        common.update(
            {
                "posterior_median": point,
                "credible_low": point - 1.96 * error,
                "credible_high": point + 1.96 * error,
                "probability_above_null": probability,
                "probability_below_null": 1.0 - probability,
                "probability_at_null": np.zeros(count),
            }
        )
    else:
        common.update(
            {
                "estimate": point,
                "conf_low": point - 1.96 * error,
                "conf_high": point + 1.96 * error,
            }
        )
    return pl.DataFrame(common)


def _reported_analysis(data: pl.DataFrame, *, posterior: bool):
    if posterior:
        return analyze_ggcoefstats(
            data,
            type="bayes",
            posterior_model="synthetic normal model",
            likelihood="Gaussian likelihood",
            prior_description="proper normal priors",
            computation_method="deterministic benchmark summary",
            **COEFFICIENT_DECLARATIONS,
        )
    return analyze_ggcoefstats(
        data,
        type="robust",
        robust_method="synthetic M-estimator",
        robust_tuning="fixed tuning",
        interval_method="reported sandwich interval",
        **COEFFICIENT_DECLARATIONS,
    )


def _meta_frame(studies: int) -> pl.DataFrame:
    position = np.arange(studies, dtype=np.float64)
    return pl.DataFrame(
        {
            "term": [f"study-{index + 1}" for index in range(studies)],
            "estimate": 0.2 + 0.12 * np.sin(position / 3.0),
            "standard_error": 0.15 + 0.1 * (position + 1.0) / studies,
        }
    )


def _meta_analysis(data: pl.DataFrame, *, mode: str):
    options: dict[str, Any] = {**META_DECLARATIONS, "type": mode}
    if mode == "bayes":
        options.update(prior_mean_scale=1.0, prior_tau_scale=0.5)
    return analyze_ggcoefstats(data, **options)


def _reported_grid() -> dict[str, Any]:
    results: dict[str, Any] = {}
    for count in COEFFICIENT_COUNTS:
        cases: dict[str, Any] = {}
        for name, posterior in (("robust", False), ("posterior", True)):
            data = _coefficient_frame(count, posterior=posterior)
            retained = _reported_analysis(data, posterior=posterior)
            cases[name] = {
                "analysis": _summary(
                    lambda data=data, posterior=posterior: _reported_analysis(
                        data, posterior=posterior
                    )
                ),
                "render": _summary(
                    lambda retained=retained: render_ggcoefstats(retained),
                    lambda plot: plot.figure.clear(),
                ),
            }
        results[str(count)] = cases
    return results


def _meta_grid(counts: tuple[int, ...], *, mode: str) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for count in counts:
        data = _meta_frame(count)
        retained = _meta_analysis(data, mode=mode)
        results[str(count)] = {
            "analysis": _summary(
                lambda data=data, mode=mode: _meta_analysis(data, mode=mode)
            ),
            "render": _summary(
                lambda retained=retained: render_ggcoefstats(retained),
                lambda plot: plot.figure.clear(),
            ),
            "actual_work": retained.result.work.actual_work,
            "reserved_work": retained.result.work.reserved_work,
        }
    return results


def run() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "scope": [
            "reported_robust_and_posterior_coefficient_analysis_render",
            "student_t4_meta_analysis_render",
            "proper_prior_normal_normal_meta_analysis_render",
            "m6c_work_accounting",
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
        "coefficient_results": _reported_grid(),
        "robust_meta_results": _meta_grid(ROBUST_META_COUNTS, mode="robust"),
        "bayesian_meta_results": _meta_grid(BAYESIAN_META_COUNTS, mode="bayes"),
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
