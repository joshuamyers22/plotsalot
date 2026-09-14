"""Validate the retained M0 benchmark artifact and required workload grid."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "benchmarks" / "results" / "m0-baseline.json"


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


def main() -> None:
    verify_benchmark()
    print("benchmark baseline verified")


if __name__ == "__main__":
    main()
