# pyright: reportPrivateUsage=false

from __future__ import annotations

import hashlib
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from typing import cast

import numpy as np

from tools.calibrate_m7b import (
    CONFIRMATION_CASES,
    CONFIRMATION_SEED,
    MAPPING_CASES,
    MAPPING_SEED,
    SMOKE_CASES,
    SMOKE_SEED,
    CaseResult,
    _preflight,
    _primary_id,
    _run_case,
    _scenario_seed_words,
    _sealed_digest,
    _standard_errors,
    _stream_id,
    confirmation_scenarios,
    mapping_scenarios,
    summarize_cell,
)


class M7BScenarioTests(unittest.TestCase):
    def test_locked_grid_counts_order_and_fits_match_plan(self) -> None:
        mapping = mapping_scenarios()
        confirmation = confirmation_scenarios()

        self.assertEqual(len(mapping), 38)
        self.assertEqual(
            Counter(item.family for item in mapping),
            {
                "primary": 30,
                "translation": 2,
                "large_study": 2,
                "se_shape": 4,
            },
        )
        self.assertEqual(len({item.scenario_id for item in mapping}), 38)
        self.assertEqual(len(confirmation), 8)
        self.assertEqual(MAPPING_CASES * len(mapping), 76_000)
        self.assertEqual(CONFIRMATION_CASES * len(confirmation), 40_000)
        self.assertEqual(SMOKE_CASES * len(mapping), 760)
        self.assertEqual(
            (SMOKE_SEED, MAPPING_SEED, CONFIRMATION_SEED),
            (2026091530, 2026091531, 2026091532),
        )
        self.assertEqual(
            [(item.k, item.tau) for item in confirmation],
            [
                (10, 0.0),
                (20, 0.0),
                (50, 0.0),
                (100, 0.0),
                (20, 0.025),
                (50, 0.025),
                (20, 0.0625),
                (50, 0.0625),
            ],
        )

    def test_standard_error_grids_retain_endpoints_and_median(self) -> None:
        scenarios = mapping_scenarios()
        for scenario in scenarios:
            errors = _standard_errors(scenario)
            with self.subTest(scenario=scenario.scenario_id):
                self.assertEqual(errors.size, scenario.k)
                self.assertAlmostEqual(float(np.min(errors)), 0.15)
                self.assertAlmostEqual(float(np.median(errors)), 0.25)
                self.assertAlmostEqual(float(np.max(errors)), 0.35)

        log_grids = [
            _standard_errors(item)
            for item in scenarios
            if item.standard_error_grid == "piecewise_log"
        ]
        self.assertEqual(len(log_grids), 2)
        self.assertTrue(
            all(
                all(grid[index] <= grid[index + 1] for index in range(grid.size - 1))
                for grid in log_grids
            )
        )

    def test_streams_are_identity_derived_with_only_declared_pairing(self) -> None:
        scenarios = mapping_scenarios()
        unpaired = [
            item for item in scenarios if item.standard_error_grid != "reversed_linear"
        ]
        stream_words = {
            item.scenario_id: _scenario_seed_words(_stream_id(item))
            for item in unpaired
        }
        self.assertEqual(len(set(stream_words.values())), len(unpaired))

        for scenario in scenarios:
            if scenario.standard_error_grid == "reversed_linear":
                self.assertEqual(_stream_id(scenario), scenario.matched_primary_id)

    def test_reversed_grid_is_an_exact_paired_permutation_audit(self) -> None:
        scenarios = mapping_scenarios()
        primary = next(
            item for item in scenarios if item.scenario_id == _primary_id(20, 0.0)
        )
        reversed_grid = next(
            item
            for item in scenarios
            if item.standard_error_grid == "reversed_linear" and item.k == 20
        )

        original = _run_case((primary, 0, SMOKE_SEED))
        permuted = _run_case((reversed_grid, 0, SMOKE_SEED))

        self.assertEqual(original.failure_code, None)
        self.assertEqual(permuted.failure_code, None)
        self.assertEqual(original.covered, permuted.covered)
        self.assertEqual(original.boundary_fit, permuted.boundary_fit)
        self.assertEqual(original.work_evaluations, permuted.work_evaluations)
        self.assertEqual(original.profile_evaluations, permuted.profile_evaluations)
        self.assertAlmostEqual(
            cast(float, original.interval_width),
            cast(float, permuted.interval_width),
            places=12,
        )
        self.assertAlmostEqual(
            cast(float, original.signed_error),
            cast(float, permuted.signed_error),
            places=12,
        )


class M7BSummaryTests(unittest.TestCase):
    def test_failures_remain_in_coverage_denominator_and_keep_stable_codes(
        self,
    ) -> None:
        scenario = confirmation_scenarios()[0]
        results = [
            CaseResult(True, 1.0, 0.1, 0.1, True, 100, 10, None),
            CaseResult(True, 2.0, 0.2, -0.2, False, 200, 20, None),
            CaseResult(False, 3.0, 0.3, 0.3, False, 300, 30, None),
            CaseResult(False, None, None, None, None, None, None, "fit_failed"),
        ]

        summary = summarize_cell(scenario, 4, results)

        self.assertEqual(summary["successes"], 3)
        self.assertEqual(summary["failures"], 1)
        self.assertEqual(summary["failure_counts"], {"fit_failed": 1})
        self.assertEqual(summary["covered"], 2)
        self.assertEqual(summary["coverage"], 0.5)
        self.assertTrue(summary["coverage_denominator_includes_failures"])
        self.assertEqual(summary["interval_width_median"], 2.0)
        self.assertEqual(summary["boundary_fit_fraction"], 1.0 / 3.0)

    def test_artifact_seal_is_verified_and_tampering_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory) / "mapping.json"
            content = b'{"status":"test"}\n'
            artifact.write_bytes(content)
            digest = hashlib.sha256(content).hexdigest()
            artifact.with_suffix(".json.sha256").write_text(
                f"{digest}  {artifact.name}\n"
            )
            self.assertEqual(_sealed_digest(artifact), digest)

            artifact.write_bytes(b"changed\n")
            with self.assertRaisesRegex(RuntimeError, "seal does not match"):
                _sealed_digest(artifact)

    def test_disposable_smoke_cannot_overwrite_a_retained_path(self) -> None:
        with (
            tempfile.TemporaryDirectory() as directory,
            self.assertRaisesRegex(ValueError, "must stay under .work"),
        ):
            _preflight("smoke", 1, Path(directory) / "retained.json")


if __name__ == "__main__":
    unittest.main()
