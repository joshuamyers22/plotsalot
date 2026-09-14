"""Retain M4 categorical selection, inference, rendering, and grouping baselines."""

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
    analyze_categorical,
    analyze_grouped_ggbarstats,
    render_ggbarstats,
    render_ggpiestats,
)
from plotsalot.categorical_data import select_categorical_table

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "benchmarks" / "results" / "m4-baseline.json"
ROW_COUNTS = (10_000, 100_000, 1_000_000)
LEVEL_COUNTS = (2, 5, 10, 20)
CELL_LEVELS = (2, 5, 10, 20)
WEIGHTED_TOTALS = (20, 1_000_000, 1_000_000_000)
GROUP_COUNTS = (1, 5, 20)
PIE_FACETS = (1, 5, 10, 20)
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


def _raw_frame(rows: int, x_levels: int = 5, y_levels: int = 2) -> pl.DataFrame:
    positions = np.arange(rows, dtype=np.int64)
    return pl.DataFrame(
        {"x": positions % x_levels, "y": (positions // x_levels) % y_levels}
    )


def _count_frame(x_levels: int, y_levels: int, count: int = 10) -> pl.DataFrame:
    x = np.repeat(np.arange(x_levels, dtype=np.int64), y_levels)
    y = np.tile(np.arange(y_levels, dtype=np.int64), x_levels)
    return pl.DataFrame({"x": x, "y": y, "n": [count] * x.size})


def _phases(data: pl.DataFrame, *, counts: str | None = None) -> dict[str, Any]:
    selection = _measure_operation(
        lambda: select_categorical_table(data, "x", "y", counts=counts)
    )
    analysis = _measure_operation(
        lambda: analyze_categorical(data, "x", "y", counts=counts)
    )
    retained = analyze_categorical(data, "x", "y", counts=counts)
    bar = _measure_operation(
        lambda: render_ggbarstats(retained, label="none"),
        lambda plot: plot.figure.clear(),
    )
    pie = _measure_operation(
        lambda: render_ggpiestats(retained, label="none"),
        lambda plot: plot.figure.clear(),
    )
    return {"selection": selection, "analysis": analysis, "bar": bar, "pie": pie}


def _one_way_phases(data: pl.DataFrame) -> dict[str, Any]:
    selection = _measure_operation(
        lambda: select_categorical_table(data, "x", counts="n")
    )
    analysis = _measure_operation(lambda: analyze_categorical(data, "x", counts="n"))
    retained = analyze_categorical(data, "x", counts="n")
    bar = _measure_operation(
        lambda: render_ggbarstats(retained, label="none"),
        lambda plot: plot.figure.clear(),
    )
    pie = _measure_operation(
        lambda: render_ggpiestats(retained, label="none"),
        lambda plot: plot.figure.clear(),
    )
    return {"selection": selection, "analysis": analysis, "bar": bar, "pie": pie}


def _pie_phase(data: pl.DataFrame, *, one_way: bool) -> dict[str, Any]:
    retained = (
        analyze_categorical(data, "x", counts="n")
        if one_way
        else analyze_categorical(data, "x", "y", counts="n")
    )
    return _measure_operation(
        lambda: render_ggpiestats(retained, label="none"),
        lambda plot: plot.figure.clear(),
    )


def run() -> dict[str, Any]:
    row_results = {str(rows): _phases(_raw_frame(rows)) for rows in ROW_COUNTS}
    level_results = {
        str(levels): {
            "pairwise_hypotheses": levels * (levels - 1) // 2,
            **_phases(_count_frame(levels, 2), counts="n"),
        }
        for levels in LEVEL_COUNTS
    }
    cell_results = {
        str(levels * levels): {
            "x_levels": levels,
            "y_levels": levels,
            **_phases(_count_frame(levels, levels), counts="n"),
        }
        for levels in CELL_LEVELS
    }
    weighted_results: dict[str, Any] = {}
    for total in WEIGHTED_TOTALS:
        half = total // 2
        data = pl.DataFrame({"x": ["a", "b"], "n": [half, total - half]})
        weighted_results[str(total)] = _one_way_phases(data)

    grouped_results: dict[str, Any] = {}
    for groups in GROUP_COUNTS:
        data = pl.DataFrame(
            {
                "group": np.repeat(np.arange(groups, dtype=np.int64), 5),
                "x": np.tile(np.arange(5, dtype=np.int64), groups),
                "n": [20] * (groups * 5),
            }
        )
        grouped_results[str(groups)] = {
            "analysis": _measure_operation(
                lambda data=data: analyze_grouped_ggbarstats(
                    data, "x", "group", counts="n"
                )
            )
        }

    pie_results: dict[str, Any] = {}
    for facets in PIE_FACETS:
        if facets == 1:
            data = pl.DataFrame({"x": np.arange(5), "n": [20] * 5})
            pie_results[str(facets)] = _pie_phase(data, one_way=True)
        else:
            pie_results[str(facets)] = _pie_phase(
                _count_frame(5, facets), one_way=False
            )

    return {
        "schema_version": 1,
        "scope": [
            "categorical_selection",
            "categorical_classical_analysis",
            "ggbarstats",
            "ggpiestats",
            "grouped_categorical",
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
        "row_results": row_results,
        "level_results": level_results,
        "cell_results": cell_results,
        "weighted_total_results": weighted_results,
        "grouped_results": grouped_results,
        "pie_facet_results": pie_results,
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
