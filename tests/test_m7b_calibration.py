# pyright: reportPrivateUsage=false

from __future__ import annotations

import hashlib
import json
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

ROOT = Path(__file__).resolve().parents[1]


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


class M7BMappingEvidenceTests(unittest.TestCase):
    def test_locked_mapping_artifact_retains_every_cell_and_failure(self) -> None:
        artifact = ROOT / "docs" / "evidence" / "m7b-robust-meta-mapping.json"
        payload = json.loads(artifact.read_text())

        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["plan_version"], 1)
        self.assertEqual(payload["run"], "mapping")
        self.assertEqual(payload["status"], "completed_with_reaffirmation_blocker")
        self.assertEqual(payload["decision_disposition"], "not_decided")
        self.assertEqual(
            payload["source_commit"], "d272aea402b77144d2ce2ef9cdaf52743e53916f"
        )
        self.assertTrue(payload["source_tree_clean"])
        self.assertEqual(payload["seed_root"], MAPPING_SEED)
        self.assertEqual(payload["cases_per_cell"], MAPPING_CASES)
        self.assertEqual(payload["scenario_count"], 38)
        self.assertEqual(payload["total_fits"], 76_000)
        self.assertEqual(len(payload["cells"]), 38)
        self.assertFalse(any(cell["undercoverage"] for cell in payload["cells"]))

        failed = [cell for cell in payload["cells"] if cell["failures"]]
        self.assertEqual(len(failed), 1)
        self.assertEqual(
            failed[0]["scenario"]["scenario_id"],
            "primary-k010-tau-0p0250-mu-0p0000-linear",
        )
        self.assertEqual(
            failed[0]["failure_counts"], {"robust_meta_ambiguous_optimum": 1}
        )
        self.assertEqual(sum(cell["failures"] for cell in payload["cells"]), 1)
        self.assertEqual(
            {
                cell["scenario"]["scenario_id"]
                for cell in payload["cells"]
                if cell["conservative"]
            },
            {
                "primary-k010-tau-0p0000-mu-0p0000-linear",
                "primary-k010-tau-0p0250-mu-0p0000-linear",
                "primary-k030-tau-0p0000-mu-0p0000-linear",
                "primary-k030-tau-0p0250-mu-0p0000-linear",
                "translation-k050-tau-0p0625-mu-0p3000-linear",
            },
        )

        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        sealed_digest, sealed_name = (
            artifact.with_suffix(".json.sha256").read_text().split()
        )
        self.assertEqual(sealed_digest, digest)
        self.assertEqual(sealed_name, artifact.name)
        self.assertLessEqual(artifact.stat().st_size, 5 * 1024 * 1024)


class M7BConfirmationEvidenceTests(unittest.TestCase):
    def test_locked_confirmation_is_chained_complete_and_unchanged(self) -> None:
        mapping = ROOT / "docs" / "evidence" / "m7b-robust-meta-mapping.json"
        artifact = ROOT / "docs" / "evidence" / "m7b-robust-meta-confirmation.json"
        payload = json.loads(artifact.read_text())

        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["plan_version"], 1)
        self.assertEqual(payload["run"], "confirmation")
        self.assertEqual(payload["status"], "completed_pending_independent_review")
        self.assertEqual(payload["decision_disposition"], "not_decided")
        self.assertEqual(
            payload["source_commit"],
            "f951d101d18edcf147030a4ca080b2221ce32481",
        )
        self.assertTrue(payload["source_tree_clean"])
        self.assertEqual(payload["seed_root"], CONFIRMATION_SEED)
        self.assertEqual(payload["cases_per_cell"], CONFIRMATION_CASES)
        self.assertEqual(payload["scenario_count"], 8)
        self.assertEqual(payload["total_fits"], 40_000)
        self.assertEqual(len(payload["cells"]), 8)
        self.assertEqual(sum(cell["failures"] for cell in payload["cells"]), 0)
        self.assertFalse(any(cell["undercoverage"] for cell in payload["cells"]))
        self.assertEqual(
            {
                cell["scenario"]["scenario_id"]
                for cell in payload["cells"]
                if cell["conservative"]
            },
            {
                "primary-k010-tau-0p0000-mu-0p0000-linear",
                "primary-k020-tau-0p0000-mu-0p0000-linear",
                "primary-k050-tau-0p0000-mu-0p0000-linear",
                "primary-k020-tau-0p0250-mu-0p0000-linear",
            },
        )

        mapping_digest = hashlib.sha256(mapping.read_bytes()).hexdigest()
        self.assertEqual(payload["mapping_artifact_sha256"], mapping_digest)
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        sealed_digest, sealed_name = (
            artifact.with_suffix(".json.sha256").read_text().split()
        )
        self.assertEqual(sealed_digest, digest)
        self.assertEqual(sealed_name, artifact.name)
        self.assertLessEqual(artifact.stat().st_size, 5 * 1024 * 1024)


if __name__ == "__main__":
    unittest.main()
