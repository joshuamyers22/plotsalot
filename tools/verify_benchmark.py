"""Validate retained benchmark artifacts and their required workload grids."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "benchmarks" / "results" / "m0-baseline.json"
M2_RESULT = ROOT / "benchmarks" / "results" / "m2-baseline.json"
M3_RESULT = ROOT / "benchmarks" / "results" / "m3-baseline.json"
M4_RESULT = ROOT / "benchmarks" / "results" / "m4-baseline.json"
M5A_RESULT = ROOT / "benchmarks" / "results" / "m5a-baseline.json"
M5B_RESULT = ROOT / "benchmarks" / "results" / "m5b-baseline.json"
M6A_RESULT = ROOT / "benchmarks" / "results" / "m6a-baseline.json"


def _positive_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise AssertionError(f"{label} must be a positive integer")
    return value


def _verify_summary(summary: object, label: str) -> None:
    if not isinstance(summary, dict):
        raise AssertionError(f"{label}: missing benchmark summary")
    samples = summary.get("samples")
    if not isinstance(samples, list) or len(samples) != 5:
        raise AssertionError(f"{label}: expected five samples")
    for index, sample in enumerate(samples):
        if not isinstance(sample, dict):
            raise AssertionError(f"{label}.{index}: invalid sample")
        _positive_int(sample.get("elapsed_ns"), f"{label}.{index}.time")
        _positive_int(sample.get("python_peak_bytes"), f"{label}.{index}.memory")


def verify_benchmark() -> None:
    """Verify the retained benchmark schema, phase split, and sample grid."""

    payload = json.loads(RESULT.read_text())
    if payload.get("schema_version") != 1:
        raise AssertionError("unsupported benchmark schema")
    if payload.get("measurement", {}).get("repeats") != 5:
        raise AssertionError("M0 baseline must retain five samples")

    expected_sizes = {"10000", "100000", "1000000"}
    results = payload.get("results")
    if not isinstance(results, dict) or set(results) != expected_sizes:
        raise AssertionError("benchmark row-count grid does not match M0")
    for size, phases in results.items():
        if not isinstance(phases, dict) or set(phases) != {"analysis", "render"}:
            raise AssertionError(f"{size}: missing separate benchmark phases")
        for phase, summary in phases.items():
            samples = summary.get("samples")
            if not isinstance(samples, list) or len(samples) != 5:
                raise AssertionError(f"{size}.{phase}: expected five samples")
            for index, sample in enumerate(samples):
                _positive_int(sample.get("elapsed_ns"), f"{size}.{phase}.{index}.time")
                _positive_int(
                    sample.get("python_peak_bytes"),
                    f"{size}.{phase}.{index}.memory",
                )

    m2 = json.loads(M2_RESULT.read_text())
    if m2.get("schema_version") != 1:
        raise AssertionError("unsupported M2 benchmark schema")
    measurement = m2.get("measurement", {})
    if measurement.get("repeats") != 5:
        raise AssertionError("M2 baseline must retain five samples")
    if measurement.get("input_frame_allocation") != "outside measured phases":
        raise AssertionError("M2 input allocation boundary must be explicit")

    grids = (
        ("scatter_results", {"10000", "100000", "1000000"}),
        ("matrix_results", {"10", "25", "50"}),
    )
    for grid_name, expected_keys in grids:
        grid = m2.get(grid_name)
        if not isinstance(grid, dict) or set(grid) != expected_keys:
            raise AssertionError(f"{grid_name}: workload grid does not match M2")
        for size, phases in grid.items():
            if not isinstance(phases, dict):
                raise AssertionError(f"{grid_name}.{size}: invalid phase mapping")
            if grid_name == "matrix_results" and phases.get("rows") != 10_000:
                raise AssertionError(f"{grid_name}.{size}: expected 10,000 rows")
            for phase in ("analysis", "render"):
                summary = phases.get(phase)
                if not isinstance(summary, dict):
                    raise AssertionError(f"{grid_name}.{size}.{phase}: missing")
                samples = summary.get("samples")
                if not isinstance(samples, list) or len(samples) != 5:
                    raise AssertionError(
                        f"{grid_name}.{size}.{phase}: expected five samples"
                    )
                for index, sample in enumerate(samples):
                    _positive_int(
                        sample.get("elapsed_ns"),
                        f"{grid_name}.{size}.{phase}.{index}.time",
                    )
                    _positive_int(
                        sample.get("python_peak_bytes"),
                        f"{grid_name}.{size}.{phase}.{index}.memory",
                    )

    m3 = json.loads(M3_RESULT.read_text())
    if m3.get("schema_version") != 1:
        raise AssertionError("unsupported M3 benchmark schema")
    measurement = m3.get("measurement", {})
    if measurement.get("repeats") != 5:
        raise AssertionError("M3 baseline must retain five samples")
    if measurement.get("input_frame_allocation") != "outside measured phases":
        raise AssertionError("M3 input allocation boundary must be explicit")

    comparison_grids = (
        ("between_row_results", {"10000", "100000", "1000000"}),
        ("between_level_results", {"2", "5", "10", "20"}),
        ("within_subject_results", {"100", "1000", "10000"}),
        ("within_condition_results", {"2", "5", "10"}),
    )
    for grid_name, expected_keys in comparison_grids:
        grid = m3.get(grid_name)
        if not isinstance(grid, dict) or set(grid) != expected_keys:
            raise AssertionError(f"{grid_name}: workload grid does not match M3")
        for size, phases in grid.items():
            if not isinstance(phases, dict):
                raise AssertionError(f"{grid_name}.{size}: invalid phase mapping")
            for phase in ("selection", "analysis", "render"):
                _verify_summary(phases.get(phase), f"{grid_name}.{size}.{phase}")

    incomplete = m3.get("within_incomplete_result")
    if not isinstance(incomplete, dict) or incomplete.get("incomplete_subjects") != 1:
        raise AssertionError("M3 incomplete-block workload is missing")
    for phase in ("selection", "analysis", "render"):
        _verify_summary(incomplete.get(phase), f"within_incomplete_result.{phase}")

    composition = m3.get("composition_results")
    if not isinstance(composition, dict) or set(composition) != {
        "1",
        "4",
        "10",
        "20",
    }:
        raise AssertionError("composition_results: workload grid does not match M3")
    for panels, phases in composition.items():
        if not isinstance(phases, dict):
            raise AssertionError(f"composition_results.{panels}: invalid mapping")
        _verify_summary(phases.get("compose"), f"composition_results.{panels}.compose")

    m4 = json.loads(M4_RESULT.read_text())
    if m4.get("schema_version") != 1:
        raise AssertionError("unsupported M4 benchmark schema")
    measurement = m4.get("measurement", {})
    if measurement.get("repeats") != 5:
        raise AssertionError("M4 baseline must retain five samples")
    if measurement.get("input_frame_allocation") != "outside measured phases":
        raise AssertionError("M4 input allocation boundary must be explicit")

    categorical_grids = (
        (
            "row_results",
            {"10000", "100000", "1000000"},
            ("selection", "analysis", "bar", "pie"),
        ),
        (
            "level_results",
            {"2", "5", "10", "20"},
            ("selection", "analysis", "bar", "pie"),
        ),
        (
            "cell_results",
            {"4", "25", "100", "400"},
            ("selection", "analysis", "bar", "pie"),
        ),
        (
            "weighted_total_results",
            {"20", "1000000", "1000000000"},
            ("selection", "analysis", "bar", "pie"),
        ),
        ("grouped_results", {"1", "5", "20"}, ("analysis",)),
        ("pie_facet_results", {"1", "5", "10", "20"}, ("value",)),
    )
    for grid_name, expected_keys, phases in categorical_grids:
        grid = m4.get(grid_name)
        if not isinstance(grid, dict) or set(grid) != expected_keys:
            raise AssertionError(f"{grid_name}: workload grid does not match M4")
        for size, values in grid.items():
            if grid_name == "pie_facet_results":
                _verify_summary(values, f"{grid_name}.{size}.pie")
                continue
            if not isinstance(values, dict):
                raise AssertionError(f"{grid_name}.{size}: invalid phase mapping")
            for phase in phases:
                _verify_summary(values.get(phase), f"{grid_name}.{size}.{phase}")

    m5a = json.loads(M5A_RESULT.read_text())
    if m5a.get("schema_version") != 1:
        raise AssertionError("unsupported M5A benchmark schema")
    measurement = m5a.get("measurement", {})
    if measurement.get("repeats") != 5:
        raise AssertionError("M5A baseline must retain five samples")
    if measurement.get("input_frame_and_model_fit") != "outside measured phases":
        raise AssertionError("M5A input/model-fit boundary must be explicit")
    table_results = m5a.get("table_results")
    if not isinstance(table_results, dict) or set(table_results) != {
        "10",
        "100",
        "500",
    }:
        raise AssertionError("M5A coefficient-count grid does not match its contract")
    for count, phases in table_results.items():
        if not isinstance(phases, dict):
            raise AssertionError(f"M5A {count}: invalid phases")
        for phase in ("selection", "analysis", "render"):
            _verify_summary(phases.get(phase), f"M5A.{count}.{phase}")
    _verify_summary(m5a.get("model_adapter"), "M5A.model_adapter")

    m5b = json.loads(M5B_RESULT.read_text())
    if m5b.get("schema_version") != 1:
        raise AssertionError("unsupported M5B benchmark schema")
    measurement = m5b.get("measurement", {})
    if measurement.get("repeats") != 5:
        raise AssertionError("M5B baseline must retain five samples")
    if measurement.get("input_frame_allocation") != "outside measured phases":
        raise AssertionError("M5B input allocation boundary must be explicit")
    study_results = m5b.get("study_results")
    if not isinstance(study_results, dict) or set(study_results) != {
        "3",
        "10",
        "100",
        "500",
    }:
        raise AssertionError("M5B study-count grid does not match its contract")
    expected_cases = {
        "equal_variance_zero_heterogeneity",
        "equal_variance_positive_heterogeneity",
        "unequal_variance_zero_heterogeneity",
        "unequal_variance_positive_heterogeneity",
    }
    for studies, cases in study_results.items():
        if not isinstance(cases, dict) or set(cases) != expected_cases:
            raise AssertionError(f"M5B {studies}: workload cases are incomplete")
        for case, phases in cases.items():
            if not isinstance(phases, dict):
                raise AssertionError(f"M5B {studies}.{case}: invalid phases")
            for phase in ("selection", "analysis", "render"):
                _verify_summary(phases.get(phase), f"M5B.{studies}.{case}.{phase}")

    m6a = json.loads(M6A_RESULT.read_text())
    if m6a.get("schema_version") != 1:
        raise AssertionError("unsupported M6A benchmark schema")
    measurement = m6a.get("measurement", {})
    if measurement.get("repeats") != 5:
        raise AssertionError("M6A baseline must retain five samples")
    if measurement.get("input_frame_allocation") != "outside measured phases":
        raise AssertionError("M6A input allocation boundary must be explicit")

    histogram = m6a.get("histogram_results")
    if not isinstance(histogram, dict) or set(histogram) != {
        "10000",
        "100000",
        "1000000",
    }:
        raise AssertionError("M6A robust univariate row grid is incomplete")
    for rows, phases in histogram.items():
        if not isinstance(phases, dict):
            raise AssertionError(f"M6A histogram {rows}: invalid phases")
        for phase in ("analysis", "render"):
            _verify_summary(phases.get(phase), f"M6A.histogram.{rows}.{phase}")

    resampling = m6a.get("representative_resampling")
    if not isinstance(resampling, dict):
        raise AssertionError("M6A representative resampling baseline is absent")
    if resampling.get("calculated_work") != 999_000:
        raise AssertionError("M6A representative resampling work differs")
    for phase in ("resampling_analysis", "render"):
        _verify_summary(resampling.get(phase), f"M6A.resampling.{phase}")

    comparisons = m6a.get("comparison_results")
    if not isinstance(comparisons, dict) or set(comparisons) != {
        "between_20_levels",
        "within_100_by_10",
    }:
        raise AssertionError("M6A comparison workload grid is incomplete")
    for case, phases in comparisons.items():
        if not isinstance(phases, dict):
            raise AssertionError(f"M6A comparison {case}: invalid phases")
        for phase in ("analysis", "render"):
            _verify_summary(phases.get(phase), f"M6A.comparison.{case}.{phase}")

    resource = m6a.get("resource_grid")
    if not isinstance(resource, dict):
        raise AssertionError("M6A resource grid is absent")
    scatter = resource.get("scatter")
    matrix = resource.get("matrix")
    if not isinstance(scatter, dict) or set(scatter) != {
        "10000",
        "100000",
        "1000000",
    }:
        raise AssertionError("M6A scatter resource grid is incomplete")
    if not isinstance(matrix, dict) or set(matrix) != {"10", "25", "50"}:
        raise AssertionError("M6A matrix resource grid is incomplete")
    if scatter["10000"].get("default_ceiling_accepts") is not True:
        raise AssertionError("M6A 10K scatter should fit the default work ceiling")
    if scatter["1000000"].get("hard_ceiling_accepts") is not False:
        raise AssertionError("M6A 1M scatter should fail the hard work ceiling")
    if matrix["10"].get("hard_ceiling_accepts") is not True:
        raise AssertionError("M6A 10-variable matrix should fit the hard ceiling")
    if matrix["25"].get("hard_ceiling_accepts") is not False:
        raise AssertionError("M6A 25-variable matrix should fail the hard ceiling")


def main() -> None:
    verify_benchmark()
    print("benchmark baseline verified")


if __name__ == "__main__":
    main()
