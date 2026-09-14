"""Validate retained benchmark artifacts and their required workload grids."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "benchmarks" / "results" / "m0-baseline.json"
M2_RESULT = ROOT / "benchmarks" / "results" / "m2-baseline.json"


def _positive_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise AssertionError(f"{label} must be a positive integer")
    return value


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


def main() -> None:
    verify_benchmark()
    print("benchmark baseline verified")


if __name__ == "__main__":
    main()
