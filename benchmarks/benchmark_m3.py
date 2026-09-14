"""Retain M3 comparison and composition benchmark distributions."""

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
    analyze_ggbetweenstats,
    analyze_ggwithinstats,
    combine_plots,
    ggbetweenstats,
    render_ggbetweenstats,
    render_ggwithinstats,
)
from plotsalot.comparison_data import (
    select_comparison_sample,
    select_repeated_sample,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "benchmarks" / "results" / "m3-baseline.json"
BETWEEN_ROWS = (10_000, 100_000, 1_000_000)
BETWEEN_LEVELS = (2, 5, 10, 20)
BETWEEN_LEVEL_ROWS = 10_000
WITHIN_SUBJECTS = (100, 1_000, 10_000)
WITHIN_SUBJECT_CONDITIONS = 5
WITHIN_CONDITIONS = (2, 5, 10)
WITHIN_CONDITION_SUBJECTS = 1_000
COMPOSITION_PANELS = (1, 4, 10, 20)
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


def _measure_comparison(
    select: Callable[[], object],
    analyze: Callable[[], T],
    render: Callable[[T], object],
) -> dict[str, Any]:
    warm = analyze()
    warm_plot = render(warm)
    warm_plot.figure.clear()  # type: ignore[attr-defined]
    selection = _measure_operation(select)
    analysis = _measure_operation(analyze)
    retained = analyze()
    rendering = _measure_operation(
        lambda retained=retained: render(retained),
        lambda plot: plot.figure.clear(),  # type: ignore[attr-defined]
    )
    return {"selection": selection, "analysis": analysis, "render": rendering}


def _between_frame(rows: int, levels: int, seed: int) -> pl.DataFrame:
    rng = np.random.default_rng(seed)
    group = np.arange(rows, dtype=np.int64) % levels
    value = rng.standard_normal(rows) * (1.0 + group * 0.03) + group * 0.08
    return pl.DataFrame({"group": group, "value": value})


def _within_frame(subjects: int, conditions: int, seed: int) -> pl.DataFrame:
    rng = np.random.default_rng(seed)
    subject = np.repeat(np.arange(subjects, dtype=np.int64), conditions)
    condition = np.tile(np.arange(conditions, dtype=np.int64), subjects)
    subject_effect = np.repeat(rng.standard_normal(subjects), conditions)
    value = subject_effect + condition * 0.08 + rng.standard_normal(subject.size)
    return pl.DataFrame({"subject": subject, "condition": condition, "value": value})


def _between_phases(data: pl.DataFrame, levels: int) -> dict[str, Any]:
    return _measure_comparison(
        lambda: select_comparison_sample(data, "group", "value", maximum_levels=levels),
        lambda: analyze_ggbetweenstats(
            data,
            "group",
            "value",
            maximum_levels=levels,
            maximum_rendered_observations=data.height,
        ),
        render_ggbetweenstats,
    )


def _within_phases(data: pl.DataFrame, conditions: int) -> dict[str, Any]:
    return _measure_comparison(
        lambda: select_repeated_sample(
            data,
            "condition",
            "value",
            "subject",
            maximum_levels=conditions,
        ),
        lambda: analyze_ggwithinstats(
            data,
            "condition",
            "value",
            subject_id="subject",
            maximum_levels=conditions,
            maximum_rendered_observations=data.height,
            maximum_subject_paths=max(data.height, 10_000),
        ),
        render_ggwithinstats,
    )


def run() -> dict[str, Any]:
    between_rows: dict[str, Any] = {}
    for rows in BETWEEN_ROWS:
        data = _between_frame(rows, 5, 20260914 + rows)
        between_rows[str(rows)] = {"levels": 5, **_between_phases(data, 5)}

    between_levels: dict[str, Any] = {}
    for levels in BETWEEN_LEVELS:
        data = _between_frame(BETWEEN_LEVEL_ROWS, levels, 20261914 + levels)
        between_levels[str(levels)] = {
            "rows": BETWEEN_LEVEL_ROWS,
            "pairwise_hypotheses": levels * (levels - 1) // 2 if levels > 2 else 0,
            **_between_phases(data, levels),
        }

    within_subjects: dict[str, Any] = {}
    for subjects in WITHIN_SUBJECTS:
        data = _within_frame(
            subjects,
            WITHIN_SUBJECT_CONDITIONS,
            20262914 + subjects,
        )
        within_subjects[str(subjects)] = {
            "conditions": WITHIN_SUBJECT_CONDITIONS,
            **_within_phases(data, WITHIN_SUBJECT_CONDITIONS),
        }

    within_conditions: dict[str, Any] = {}
    for conditions in WITHIN_CONDITIONS:
        data = _within_frame(
            WITHIN_CONDITION_SUBJECTS,
            conditions,
            20263914 + conditions,
        )
        within_conditions[str(conditions)] = {
            "subjects": WITHIN_CONDITION_SUBJECTS,
            "pairwise_hypotheses": (
                conditions * (conditions - 1) // 2 if conditions > 2 else 0
            ),
            **_within_phases(data, conditions),
        }

    incomplete = _within_frame(1_001, 5, 20264914).slice(0, 5_004)
    incomplete_result = {
        "subjects": 1_001,
        "conditions": 5,
        "incomplete_subjects": 1,
        **_within_phases(incomplete, 5),
    }

    source = ggbetweenstats(_between_frame(100, 2, 20265914), "group", "value")
    composition: dict[str, Any] = {}
    try:
        for panels in COMPOSITION_PANELS:
            composition[str(panels)] = {
                "compose": _measure_operation(
                    lambda panels=panels: combine_plots(
                        [source] * panels, maximum_panels=panels
                    ),
                    lambda plot: plot.figure.clear(),  # type: ignore[attr-defined]
                )
            }
    finally:
        source.figure.clear()

    return {
        "schema_version": 1,
        "scope": [
            "ggbetweenstats_welch",
            "ggwithinstats_parametric_complete_block",
            "combine_plots",
        ],
        "measurement": {
            "clock": "time.perf_counter_ns",
            "memory": "tracemalloc incremental Python allocation peak",
            "input_frame_allocation": "outside measured phases",
            "selection_phase": "data-boundary work only",
            "analysis_phase": "end-to-end selection plus inference",
            "render_phase": "retained analysis to semantic figure",
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
        "between_row_results": between_rows,
        "between_level_results": between_levels,
        "within_subject_results": within_subjects,
        "within_condition_results": within_conditions,
        "within_incomplete_result": incomplete_result,
        "composition_results": composition,
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
