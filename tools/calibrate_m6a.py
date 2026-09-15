"""Generate the locked M6A Winsorized-correlation interval calibration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from plotsalot.robust import (
    bootstrap_winsorized_correlation,
    child_seed,
    winsorized_correlation,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs" / "evidence" / "m6a-correlation-calibration.json"
SCENARIOS = (-0.5, 0.0, 0.5)
SAMPLE_SIZE = 40
CASES = 100
RESAMPLES = 999
CONF_LEVEL = 0.95
REFERENCE_SIZE = 2_000_000
REFERENCE_SEED = 2026091401
DATA_SEED = 2026091402
BOOTSTRAP_ROOT_SEED = 2026091403
MINIMUM_COVERAGE = 0.86
MAXIMUM_COVERAGE = 1.0


def _draw(rng: np.random.Generator, size: int, rho: float) -> tuple[Any, Any]:
    x = rng.standard_normal(size)
    noise = rng.standard_normal(size)
    y = (rho * x) + (np.sqrt(1.0 - (rho**2)) * noise)
    return x, y


def run() -> dict[str, Any]:
    reference_rng = np.random.Generator(np.random.PCG64DXSM(REFERENCE_SEED))
    data_rng = np.random.Generator(np.random.PCG64DXSM(DATA_SEED))
    results: list[dict[str, Any]] = []
    total_work = 0
    for rho in SCENARIOS:
        if rho == 0.0:
            target = 0.0
        else:
            reference_x, reference_y = _draw(reference_rng, REFERENCE_SIZE, rho)
            target = winsorized_correlation(reference_x, reference_y)[0]
        covered = 0
        widths: list[float] = []
        failed_replicates = 0
        valid_replicates = 0
        for case in range(CASES):
            x, y = _draw(data_rng, SAMPLE_SIZE, rho)
            derived_seed, identity = child_seed(
                BOOTSTRAP_ROOT_SEED,
                "m6a_correlation_calibration",
                (rho, case),
            )
            low, high, resampling = bootstrap_winsorized_correlation(
                x,
                y,
                conf_level=CONF_LEVEL,
                bootstrap_resamples=RESAMPLES,
                root_seed=BOOTSTRAP_ROOT_SEED,
                derived_seed=derived_seed,
                child_identity=identity,
                maximum_resample_work=100_000_000,
            )
            covered += int(low <= target <= high)
            widths.append(high - low)
            failed_replicates += resampling.failed_replicates
            valid_replicates += resampling.valid_replicates
            total_work += resampling.calculated_work
        coverage = covered / CASES
        results.append(
            {
                "generating_pearson_rho": rho,
                "population_winsorized_target": target,
                "covered_cases": covered,
                "coverage": coverage,
                "mean_interval_width": float(np.mean(widths)),
                "minimum_interval_width": min(widths),
                "maximum_interval_width": max(widths),
                "valid_replicates": valid_replicates,
                "failed_replicates": failed_replicates,
                "passes_predeclared_coverage_band": (
                    MINIMUM_COVERAGE <= coverage <= MAXIMUM_COVERAGE
                ),
            }
        )
    return {
        "schema_version": 1,
        "status": "locked_validation",
        "method": "paired_percentile_bootstrap_type7_for_20pct_winsorized_r",
        "interval_level": CONF_LEVEL,
        "sample_size": SAMPLE_SIZE,
        "cases_per_scenario": CASES,
        "bootstrap_resamples": RESAMPLES,
        "population_reference_sample_size": REFERENCE_SIZE,
        "population_reference_seed": REFERENCE_SEED,
        "data_seed": DATA_SEED,
        "bootstrap_root_seed": BOOTSTRAP_ROOT_SEED,
        "bit_generator": "PCG64DXSM",
        "predeclared_coverage_band": [MINIMUM_COVERAGE, MAXIMUM_COVERAGE],
        "total_resample_work": total_work,
        "scenarios": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = run()
    if not all(
        scenario["passes_predeclared_coverage_band"]
        for scenario in payload["scenarios"]
    ):
        raise RuntimeError("M6A correlation interval calibration failed")
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
