from __future__ import annotations

import json
import unittest
from dataclasses import replace
from math import sqrt
from pathlib import Path
from typing import Any, cast

import numpy as np
import polars as pl
from numpy.testing import assert_allclose

from plotsalot import (
    RobustComparisonResult,
    RobustCorrelationMatrixResult,
    RobustCorrelationResult,
    RobustDotPlotResult,
    RobustOneSampleResult,
    analyze_ggbetweenstats,
    analyze_ggcorrmat,
    analyze_ggdotplotstats,
    analyze_gghistostats,
    analyze_ggscatterstats,
    analyze_ggwithinstats,
    combine_plots,
    extract_stats,
    ggbetweenstats,
    ggcorrmat,
    ggdotplotstats,
    gghistostats,
    ggscatterstats,
    ggwithinstats,
    grouped_ggbetweenstats,
    grouped_ggcorrmat,
    grouped_ggdotplotstats,
    grouped_gghistostats,
    grouped_ggscatterstats,
    grouped_ggwithinstats,
)
from plotsalot.result import IntervalResult, SampleAudit
from plotsalot.robust import (
    bootstrap_winsorized_correlation,
    child_seed,
    trimmed_kernel,
    typed_identity,
)
from plotsalot.robust_result import (
    RobustTestResult,
    TrimmedKernelResult,
)


def _association_frame() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "x": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 100.0, 9.0, 10.0],
            "y": [2.0, 1.0, 4.0, 3.0, 7.0, 8.0, 9.0, -50.0, 10.0, 12.0],
            "z": [10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0],
        }
    )


def _between_frame() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "group": (["a"] * 6) + (["b"] * 6) + (["c"] * 6),
            "value": [
                1.0,
                2.0,
                3.0,
                4.0,
                5.0,
                20.0,
                2.0,
                3.0,
                4.0,
                5.0,
                6.0,
                7.0,
                4.0,
                5.0,
                6.0,
                7.0,
                8.0,
                9.0,
            ],
        }
    )


def _within_frame() -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for subject in range(8):
        for index, condition in enumerate(("a", "b", "c")):
            rows.append(
                {
                    "subject": subject,
                    "condition": condition,
                    "value": float(subject + index + ((subject % 3) * index * 0.2)),
                }
            )
    return pl.DataFrame(rows)


class RobustKernelTests(unittest.TestCase):
    def test_trimmed_kernel_matches_independent_equations(self) -> None:
        values = np.arange(1.0, 11.0)
        kernel, winsorized = trimmed_kernel(values)
        expected_winsorized = np.array(
            [3.0, 3.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 8.0, 8.0]
        )
        self.assertEqual((kernel.n, kernel.g, kernel.h), (10, 2, 6))
        self.assertEqual((kernel.lower_bound, kernel.upper_bound), (3.0, 8.0))
        self.assertEqual(kernel.trimmed_mean, 5.5)
        assert_allclose(winsorized, expected_winsorized, rtol=0.0, atol=0.0)
        expected_variance = (
            sum(
                (value - np.mean(expected_winsorized)) ** 2
                for value in expected_winsorized
            )
            / 9.0
        )
        self.assertAlmostEqual(kernel.winsorized_variance, expected_variance)
        self.assertAlmostEqual(kernel.q, 9.0 * expected_variance / (6.0 * 5.0))

    def test_kernel_rejects_unapproved_or_degenerate_inputs(self) -> None:
        with self.assertRaisesRegex(ValueError, "0.20"):
            trimmed_kernel(np.arange(1.0, 11.0), trim_fraction=0.1)
        with self.assertRaisesRegex(ValueError, "at least five"):
            trimmed_kernel(np.arange(4.0))
        with self.assertRaisesRegex(ValueError, "Winsorized variance"):
            trimmed_kernel(np.ones(8))
        with self.assertRaisesRegex(ValueError, "finite"):
            trimmed_kernel(np.array([1.0, 2.0, 3.0, 4.0, float("nan")]))

    def test_kernel_is_equivariant_and_bounds_controlled_tail_contamination(
        self,
    ) -> None:
        clean = np.arange(1.0, 11.0)
        contaminated = clean.copy()
        contaminated[[0, -1]] = (-1e100, 1e100)
        clean_kernel, _ = trimmed_kernel(clean)
        contaminated_kernel, _ = trimmed_kernel(contaminated)
        self.assertEqual(contaminated_kernel.trimmed_mean, clean_kernel.trimmed_mean)

        shifted, _ = trimmed_kernel(clean + 37.0)
        self.assertAlmostEqual(shifted.trimmed_mean, clean_kernel.trimmed_mean + 37.0)
        for scale in (1e-100, 1e100):
            scaled, _ = trimmed_kernel(clean * scale)
            self.assertAlmostEqual(
                scaled.trimmed_mean / scale,
                clean_kernel.trimmed_mean,
                places=12,
            )
            self.assertAlmostEqual(scaled.q / (scale**2), clean_kernel.q, places=12)

    def test_child_seed_is_typed_stable_and_order_independent_when_canonical(
        self,
    ) -> None:
        first = child_seed(42, "matrix", tuple(sorted(("x", "y"))))
        second = child_seed(42, "matrix", tuple(sorted(("y", "x"))))
        self.assertEqual(first, second)
        self.assertNotEqual(
            child_seed(42, "matrix", (1,)), child_seed(42, "matrix", ("1",))
        )
        self.assertEqual(typed_identity(True), "bool:true")
        self.assertEqual(typed_identity(1.5), "float:0x1.8000000000000p+0")
        with self.assertRaisesRegex(TypeError, "scalar identities"):
            typed_identity(None)

    def test_bootstrap_invalid_replicate_gate_and_type7_integer_position(self) -> None:
        with self.assertRaisesRegex(ValueError, "valid bootstrap replicates"):
            bootstrap_winsorized_correlation(
                np.arange(5, dtype=np.float64),
                np.arange(5, dtype=np.float64),
                conf_level=0.95,
                bootstrap_resamples=999,
                root_seed=1,
                derived_seed=1,
                child_identity="test",
                maximum_resample_work=100_000_000,
            )
        low, high, _ = bootstrap_winsorized_correlation(
            np.arange(8, dtype=np.float64),
            np.arange(8, dtype=np.float64),
            conf_level=1.0 - (2.0 / 998.0),
            bootstrap_resamples=999,
            root_seed=2,
            derived_seed=2,
            child_identity="test",
            maximum_resample_work=100_000_000,
        )
        self.assertAlmostEqual(low, 1.0)
        self.assertAlmostEqual(high, 1.0)


class RobustOneSampleTests(unittest.TestCase):
    def test_histogram_uses_trimmed_location_and_raw_effect(self) -> None:
        frame = pl.DataFrame({"value": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 100.0]})
        analysis = analyze_gghistostats(
            frame, "value", type="robust", test_value=3.0, alternative="greater"
        )
        self.assertIsInstance(analysis.result, RobustOneSampleResult)
        result = cast(RobustOneSampleResult, analysis.result)
        self.assertEqual(result.mode, "robust")
        self.assertEqual(result.estimate.value, 4.0)
        self.assertEqual(result.effect_size.value, 1.0)
        self.assertEqual(result.test.df, result.estimate.kernel.h - 1)
        self.assertLess(result.test.p_value, 0.5)
        self.assertLessEqual(result.interval.low, result.estimate.value)
        self.assertGreaterEqual(result.interval.high, result.estimate.value)
        self.assertEqual(result.to_dict()["schema_version"], 2)

    def test_dot_plot_requires_estimable_robust_label_kernels(self) -> None:
        frame = pl.DataFrame(
            {
                "value": list(map(float, range(1, 7))) + list(map(float, range(3, 9))),
                "label": (["a"] * 6) + (["b"] * 6),
            }
        )
        analysis = analyze_ggdotplotstats(frame, "value", "label", type="robust")
        self.assertIsInstance(analysis.result, RobustDotPlotResult)
        result = cast(RobustDotPlotResult, analysis.result)
        self.assertEqual([item.kernel.h for item in result.estimates], [4, 4])
        bad = frame.filter(~((pl.col("label") == "b") & (pl.col("value") >= 7)))
        with self.assertRaisesRegex(ValueError, "at least 5"):
            analyze_ggdotplotstats(bad, "value", "label", type="robust")


class RobustAssociationTests(unittest.TestCase):
    def test_seeded_scatter_is_exactly_replayable(self) -> None:
        frame = _association_frame()
        first = analyze_ggscatterstats(
            frame,
            "x",
            "y",
            type="robust",
            random_seed=2026,
            bootstrap_resamples=999,
        ).result
        second = analyze_ggscatterstats(
            frame,
            "x",
            "y",
            type="robust",
            random_seed=2026,
            bootstrap_resamples=999,
        ).result
        self.assertIsInstance(first, RobustCorrelationResult)
        self.assertEqual(first.to_dict(), second.to_dict())
        first = cast(RobustCorrelationResult, first)
        xw = frame["x"].to_numpy().astype(np.float64, copy=True)
        yw = frame["y"].to_numpy().astype(np.float64, copy=True)
        xw[xw < 3.0] = 3.0
        xw[xw > 9.0] = 9.0
        yw[yw < 2.0] = 2.0
        yw[yw > 9.0] = 9.0
        expected = float(np.corrcoef(xw, yw)[0, 1])
        self.assertAlmostEqual(first.estimate, expected, places=14)
        self.assertEqual(first.test.df, first.x_kernel.h - 2)
        self.assertEqual(first.resampling.calculated_work, 9_990)
        self.assertEqual(first.resampling.valid_replicates, 999)

    def test_association_validates_seed_replicates_and_work_before_sampling(
        self,
    ) -> None:
        frame = _association_frame()
        with self.assertRaisesRegex(ValueError, "random_seed is required"):
            analyze_ggscatterstats(frame, "x", "y", type="robust")
        with self.assertRaisesRegex(ValueError, "odd integer"):
            analyze_ggscatterstats(
                frame, "x", "y", type="robust", random_seed=1, bootstrap_resamples=1_000
            )
        with self.assertRaisesRegex(ValueError, "exceeds"):
            analyze_ggscatterstats(
                frame,
                "x",
                "y",
                type="robust",
                random_seed=1,
                bootstrap_resamples=999,
                maximum_resample_work=9_989,
            )
        with self.assertRaisesRegex(ValueError, "500000000"):
            analyze_ggscatterstats(
                frame,
                "x",
                "y",
                type="robust",
                random_seed=1,
                bootstrap_resamples=999,
                maximum_resample_work=500_000_001,
            )
        with self.assertRaisesRegex(ValueError, "unused"):
            analyze_ggscatterstats(frame, "x", "y", random_seed=1)

    def test_seed_changes_only_stochastic_interval_and_perfect_case_is_typed(
        self,
    ) -> None:
        frame = _association_frame()
        first = cast(
            RobustCorrelationResult,
            analyze_ggscatterstats(
                frame,
                "x",
                "y",
                type="robust",
                random_seed=1,
                bootstrap_resamples=999,
            ).result,
        )
        second = cast(
            RobustCorrelationResult,
            analyze_ggscatterstats(
                frame,
                "x",
                "y",
                type="robust",
                random_seed=2,
                bootstrap_resamples=999,
            ).result,
        )
        self.assertEqual(first.estimate, second.estimate)
        self.assertNotEqual(first.interval, second.interval)

        perfect_frame = pl.DataFrame(
            {
                "x": list(map(float, range(1, 11))),
                "y": list(map(float, range(2, 21, 2))),
            }
        )
        perfect = cast(
            RobustCorrelationResult,
            analyze_ggscatterstats(
                perfect_frame,
                "x",
                "y",
                type="robust",
                random_seed=3,
                bootstrap_resamples=999,
            ).result,
        )
        self.assertEqual(perfect.estimate, 1.0)
        self.assertIsNone(perfect.test.statistic)
        self.assertEqual(perfect.test.p_value, 0.0)
        self.assertIn("perfect_winsorized_correlation", perfect.warnings)

    def test_matrix_retains_full_holm_family_and_stable_pair_streams(self) -> None:
        frame = _association_frame()
        first = analyze_ggcorrmat(
            frame,
            ("x", "y", "z"),
            type="robust",
            random_seed=77,
            bootstrap_resamples=999,
        ).result
        reordered = analyze_ggcorrmat(
            frame,
            ("z", "y", "x"),
            type="robust",
            random_seed=77,
            bootstrap_resamples=999,
        ).result
        self.assertIsInstance(first, RobustCorrelationMatrixResult)
        first = cast(RobustCorrelationMatrixResult, first)
        reordered = cast(RobustCorrelationMatrixResult, reordered)
        self.assertEqual(len(first.cells), 9)
        first_xy = next(cell for cell in first.cells if (cell.x, cell.y) == ("x", "y"))
        other_xy = next(
            cell for cell in reordered.cells if (cell.x, cell.y) == ("x", "y")
        )
        self.assertEqual(first_xy.resampling, other_xy.resampling)
        self.assertEqual(first.calculated_resample_work, 29_970)
        off_diagonal = [cell for cell in first.cells if cell.x != cell.y]
        self.assertTrue(all(cell.adjusted_p_value is not None for cell in off_diagonal))


class RobustComparisonTests(unittest.TestCase):
    def test_yuen_two_group_formula_and_direction(self) -> None:
        frame = _between_frame().filter(pl.col("group") != "c")
        result = analyze_ggbetweenstats(
            frame, "group", "value", type="robust", alternative="less"
        ).result
        self.assertIsInstance(result, RobustComparisonResult)
        result = cast(RobustComparisonResult, result)
        left, right = (level.kernel for level in result.levels)
        expected = left.trimmed_mean - right.trimmed_mean
        expected_se = sqrt(left.q + right.q)
        expected_df = ((left.q + right.q) ** 2) / (
            (left.q**2 / (left.h - 1)) + (right.q**2 / (right.h - 1))
        )
        self.assertEqual(result.estimate, expected)
        self.assertIsNotNone(result.omnibus.statistic)
        self.assertAlmostEqual(
            cast(float, result.omnibus.statistic), expected / expected_se
        )
        self.assertAlmostEqual(result.omnibus.df2, expected_df)
        self.assertEqual(result.effect_size.value, expected)

    def test_welch_yuen_and_holm_pairwise_family(self) -> None:
        result = analyze_ggbetweenstats(
            _between_frame(), "group", "value", type="robust", pairwise_display="all"
        ).result
        self.assertIsInstance(result, RobustComparisonResult)
        result = cast(RobustComparisonResult, result)
        self.assertEqual(result.omnibus.name, "welch_yuen_anova")
        self.assertEqual(len(result.pairwise), 3)
        self.assertEqual(
            [(item.left, item.right) for item in result.pairwise],
            [("a", "b"), ("a", "c"), ("b", "c")],
        )
        self.assertTrue(
            all(item.adjusted_p_value >= item.test.p_value for item in result.pairwise)
        )
        with self.assertRaisesRegex(ValueError, "omnibus alternatives"):
            analyze_ggbetweenstats(
                _between_frame(), "group", "value", type="robust", alternative="greater"
            )

    def test_repeated_two_condition_uses_subject_differences(self) -> None:
        frame = _within_frame().filter(pl.col("condition") != "c")
        result = analyze_ggwithinstats(
            frame,
            "condition",
            "value",
            subject_id="subject",
            type="robust",
        ).result
        self.assertIsInstance(result, RobustComparisonResult)
        result = cast(RobustComparisonResult, result)
        pivot = frame.pivot(on="condition", index="subject", values="value").sort(
            "subject"
        )
        difference = pivot["a"].to_numpy() - pivot["b"].to_numpy()
        expected = trimmed_kernel(difference)[0]
        self.assertEqual(result.estimate, expected.trimmed_mean)
        self.assertEqual(result.omnibus.df2, expected.h - 1)

    def test_repeated_omnibus_retains_wrs2_epsilon_inputs(self) -> None:
        result = analyze_ggwithinstats(
            _within_frame(),
            "condition",
            "value",
            subject_id="subject",
            type="robust",
            pairwise_display="all",
        ).result
        self.assertIsInstance(result, RobustComparisonResult)
        result = cast(RobustComparisonResult, result)
        self.assertEqual(result.omnibus.name, "winsorized_repeated_anova")
        self.assertIsNotNone(result.correction)
        assert result.correction is not None
        self.assertGreater(result.correction.qc, 0.0)
        self.assertGreater(result.correction.qe, 0.0)
        self.assertGreaterEqual(result.correction.epsilon, 0.5)
        self.assertLessEqual(result.correction.epsilon, 1.0)
        self.assertEqual(len(result.pairwise), 3)


class RobustIntegrationTests(unittest.TestCase):
    def test_extraction_and_composition_preserve_robust_result_identity(self) -> None:
        plot = gghistostats(_association_frame(), "x", type="robust")
        combined = combine_plots([plot])
        self.assertIs(extract_stats(plot), plot.result)
        self.assertIs(combined.result.panels[0].result, plot.result)

    def test_locked_correlation_interval_calibration_passes(self) -> None:
        payload = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "docs"
                / "evidence"
                / "m6a-correlation-calibration.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["status"], "locked_validation")
        self.assertEqual(payload["bit_generator"], "PCG64DXSM")
        self.assertEqual(payload["predeclared_coverage_band"], [0.86, 1.0])
        self.assertEqual(payload["total_resample_work"], 11_988_000)
        self.assertEqual(
            [scenario["generating_pearson_rho"] for scenario in payload["scenarios"]],
            [-0.5, 0.0, 0.5],
        )
        self.assertTrue(
            all(
                scenario["passes_predeclared_coverage_band"]
                for scenario in payload["scenarios"]
            )
        )

    def test_schema_v2_declares_every_robust_top_level_variant(self) -> None:
        schema = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "schemas"
                / "robust-result.schema.json"
            ).read_text(encoding="utf-8")
        )
        definitions = schema["$defs"]
        examples = {
            "oneSample": analyze_gghistostats(
                _association_frame(), "x", type="robust"
            ).result.to_dict(),
            "dotPlot": analyze_ggdotplotstats(
                pl.DataFrame(
                    {
                        "value": list(map(float, range(1, 7))) * 2,
                        "label": (["a"] * 6) + (["b"] * 6),
                    }
                ),
                "value",
                "label",
                type="robust",
            ).result.to_dict(),
            "correlation": analyze_ggscatterstats(
                _association_frame(),
                "x",
                "y",
                type="robust",
                random_seed=8,
                bootstrap_resamples=999,
            ).result.to_dict(),
            "correlationMatrix": analyze_ggcorrmat(
                _association_frame(),
                ("x", "y"),
                type="robust",
                random_seed=8,
                bootstrap_resamples=999,
            ).result.to_dict(),
            "comparison": analyze_ggbetweenstats(
                _between_frame(), "group", "value", type="robust"
            ).result.to_dict(),
        }
        for name, payload in examples.items():
            with self.subTest(name=name):
                self.assertEqual(set(payload), set(definitions[name]["required"]))
                self.assertEqual(payload["schema_version"], 2)
                self.assertEqual(payload["mode"], "robust")

    def test_all_direct_renderers_are_analysis_free_consumers(self) -> None:
        association = _association_frame()
        between = _between_frame()
        within = _within_frame()
        dot = pl.DataFrame(
            {
                "value": list(map(float, range(1, 7))) + list(map(float, range(3, 9))),
                "label": (["a"] * 6) + (["b"] * 6),
            }
        )
        plots = (
            gghistostats(association, "x", type="robust"),
            ggdotplotstats(dot, "value", "label", type="robust"),
            ggscatterstats(
                association,
                "x",
                "y",
                type="robust",
                random_seed=5,
                bootstrap_resamples=999,
            ),
            ggcorrmat(
                association,
                ("x", "y"),
                type="robust",
                random_seed=5,
                bootstrap_resamples=999,
            ),
            ggbetweenstats(between, "group", "value", type="robust"),
            ggwithinstats(
                within,
                "condition",
                "value",
                subject_id="subject",
                type="robust",
            ),
        )
        self.assertTrue(
            all(
                "robust" in plot.result.analysis or "winsorized" in plot.result.analysis
                for plot in plots
            )
        )
        self.assertTrue(all(plot.annotations.subtitle for plot in plots))

    def test_grouped_robust_surfaces_are_atomic_and_retain_root_work(self) -> None:
        base = _association_frame()
        association = pl.concat(
            [
                pl.concat([base, base.with_columns(pl.col("x") + 0.1)]).with_columns(
                    pl.lit("a").alias("outer")
                ),
                pl.concat([base, base.with_columns(pl.col("y") + 0.2)]).with_columns(
                    pl.lit("b").alias("outer")
                ),
            ]
        )
        dot = pl.DataFrame(
            {
                "outer": (["g1"] * 12) + (["g2"] * 12),
                "label": ((["a"] * 6) + (["b"] * 6)) * 2,
                "value": (list(map(float, range(1, 7))) + list(map(float, range(3, 9))))
                * 2,
            }
        )
        between = pl.concat(
            [
                _between_frame().with_columns(pl.lit("g1").alias("outer")),
                _between_frame().with_columns(pl.lit("g2").alias("outer")),
            ]
        )
        within = pl.concat(
            [
                _within_frame().with_columns(pl.lit("g1").alias("outer")),
                _within_frame().with_columns(
                    pl.lit("g2").alias("outer"),
                    (pl.col("subject") + 100).alias("subject"),
                ),
            ]
        )
        plots = (
            grouped_gghistostats(association, "x", "outer", type="robust"),
            grouped_ggdotplotstats(dot, "value", "label", "outer", type="robust"),
            grouped_ggscatterstats(
                association,
                "x",
                "y",
                "outer",
                type="robust",
                random_seed=11,
                bootstrap_resamples=999,
            ),
            grouped_ggcorrmat(
                association,
                ("x", "y"),
                "outer",
                type="robust",
                random_seed=11,
                bootstrap_resamples=999,
            ),
            grouped_ggbetweenstats(between, "group", "value", "outer", type="robust"),
            grouped_ggwithinstats(
                within,
                "condition",
                "value",
                "outer",
                subject_id="subject",
                type="robust",
            ),
        )
        self.assertTrue(all(len(plot.plots) == 2 for plot in plots))
        scatter_result = plots[2].result
        self.assertEqual(scatter_result.resampling_root_seed, 11)
        self.assertEqual(scatter_result.calculated_resample_work, 39_960)
        self.assertIn("resampling", scatter_result.to_dict())

        invalid = association.with_columns(
            pl.when(pl.col("outer") == "b")
            .then(pl.lit(1.0))
            .otherwise(pl.col("x"))
            .alias("x")
        )
        with self.assertRaisesRegex(ValueError, "group 'b' failed|variation"):
            grouped_ggscatterstats(
                invalid,
                "x",
                "y",
                "outer",
                type="robust",
                random_seed=11,
                bootstrap_resamples=999,
            )

    def test_schema_mutation_rejects_wrong_kernel_count(self) -> None:
        result = analyze_gghistostats(
            pl.DataFrame({"x": list(map(float, range(1, 9)))}), "x", type="robust"
        ).result
        result = cast(RobustOneSampleResult, result)
        with self.assertRaisesRegex(ValueError, "effective count"):
            replace(result.estimate.kernel, h=result.estimate.kernel.h + 1)


class RobustContractMutationTests(unittest.TestCase):
    def _invalid(self, target: object, pattern: str, **changes: object) -> None:
        with self.assertRaisesRegex(ValueError, pattern):
            replace(target, **changes)  # type: ignore[arg-type]

    def test_kernel_method_test_effect_and_resampling_invariants(self) -> None:
        one = cast(
            RobustOneSampleResult,
            analyze_gghistostats(
                pl.DataFrame({"x": list(map(float, range(1, 11)))}),
                "x",
                type="robust",
            ).result,
        )
        kernel = one.estimate.kernel
        self._invalid(kernel, "0.20", trim_fraction=0.1)
        self._invalid(kernel, "n/g", n=4)
        self._invalid(kernel, "effective count", h=kernel.h + 1)
        self._invalid(kernel, "finite", trimmed_mean=float("nan"))
        self._invalid(kernel, "ordered", lower_bound=kernel.upper_bound + 1.0)
        self._invalid(kernel, "positive", q=0.0)
        self._invalid(kernel, "inconsistent", q=kernel.q * 2.0)

        self._invalid(one.method, "complete", name="")
        self._invalid(one.method, "adapted", compatibility="equivalent")
        self._invalid(one.estimate, "match", value=one.estimate.value + 1.0)
        self._invalid(one.estimate, "positive", standard_deviation=0.0)
        self._invalid(
            one.estimate,
            "match Winsorized",
            standard_deviation=one.estimate.standard_deviation * 2.0,
        )
        self._invalid(one.effect_size, "complete", name="")
        self._invalid(one.effect_size, "finite", value=float("nan"))
        self._invalid(
            one.effect_size,
            "absence",
            standardized_effect_unavailable="unknown",
        )
        self._invalid(one.test, "identity", name="")
        self._invalid(one.test, "alternative", alternative=cast(Any, "invalid"))
        self._invalid(one.test, "finite", statistic=float("nan"))
        self._invalid(one.test, "numerator", df1=-1.0)
        self._invalid(one.test, "denominator", df2=0.0)
        self._invalid(one.test, "p_value", p_value=2.0)
        self._invalid(one.test, "distribution", reference_distribution="normal")
        f_test = RobustTestResult(
            name="f",
            target="target",
            null_value=None,
            alternative="two-sided",
            statistic=1.0,
            df1=2.0,
            df2=5.0,
            p_value=0.5,
            reference_distribution="f",
        )
        self._invalid(f_test, "requires numerator", df1=None)

        correlation = cast(
            RobustCorrelationResult,
            analyze_ggscatterstats(
                _association_frame(),
                "x",
                "y",
                type="robust",
                random_seed=4,
                bootstrap_resamples=999,
            ).result,
        )
        sampling = correlation.resampling
        self._invalid(sampling, "algorithm", algorithm="other")
        self._invalid(sampling, "RNG", bit_generator="MT19937")
        self._invalid(sampling, "root seed", root_seed=-1)
        self._invalid(sampling, "child seed", child_seed=-1)
        self._invalid(sampling, "reconcile", failed_replicates=1)
        self._invalid(
            sampling,
            "M6A policy",
            valid_replicates=949,
            failed_replicates=50,
        )
        self._invalid(sampling, "exceeds", calculated_work=0)
        self._invalid(
            sampling,
            "ceilings",
            maximum_resample_work=500_000_001,
            hard_maximum_resample_work=500_000_001,
        )
        self._invalid(sampling, "batch", batch_index_limit=999_999)

    def test_one_sample_dot_and_correlation_cross_fields(self) -> None:
        frame = pl.DataFrame({"x": list(map(float, range(1, 11)))})
        one = cast(
            RobustOneSampleResult,
            analyze_gghistostats(frame, "x", type="robust").result,
        )
        self._invalid(one, "schema", schema_version=1)
        self._invalid(one, "identity", analysis="bad")
        self._invalid(one, "sample identity", column="")
        self._invalid(
            one,
            "sample identity",
            sample=SampleAudit(input_rows=11, analyzed_rows=11, dropped_null_rows=0),
        )
        self._invalid(
            one,
            "interval target",
            interval=replace(one.interval, target="population_mean"),
        )
        self._invalid(
            one, "raw effect", effect_size=replace(one.effect_size, value=1.0)
        )
        self._invalid(one, "null value", test=replace(one.test, null_value=None))
        self._invalid(one, "test is inconsistent", test=replace(one.test, df2=99.0))
        self._invalid(
            one,
            "statistic is inconsistent",
            test=replace(one.test, statistic=cast(float, one.test.statistic) + 1.0),
        )
        asymmetric = IntervalResult(
            target=one.interval.target,
            method=one.interval.method,
            level=one.interval.level,
            low=one.interval.low,
            high=one.interval.high + 1.0,
        )
        self._invalid(one, "symmetric", interval=asymmetric)

        dot_frame = pl.DataFrame(
            {
                "x": list(map(float, range(1, 7))) + list(map(float, range(3, 9))),
                "label": (["a"] * 6) + (["b"] * 6),
            }
        )
        dot = cast(
            RobustDotPlotResult,
            analyze_ggdotplotstats(dot_frame, "x", "label", type="robust").result,
        )
        estimate = dot.estimates[0]
        self._invalid(estimate, "non-empty", label="")
        self._invalid(estimate, "match", value=estimate.value + 1.0)
        self._invalid(estimate, "positive", standard_deviation=0.0)
        self._invalid(
            estimate,
            "interval target",
            interval=replace(estimate.interval, target="population_mean"),
        )
        self._invalid(dot, "identity", schema_version=1)
        self._invalid(dot, "requires estimates", estimates=())
        self._invalid(dot, "overall sample", x="other")

        correlation = cast(
            RobustCorrelationResult,
            analyze_ggscatterstats(
                _association_frame(),
                "x",
                "y",
                type="robust",
                random_seed=9,
                bootstrap_resamples=999,
            ).result,
        )
        self._invalid(correlation, "identity", schema_version=1)
        self._invalid(correlation, "columns", y="x")
        self._invalid(correlation, "kernel counts", y_kernel=kernel_for_n(11))
        self._invalid(correlation, "finite", winsorized_covariance=float("nan"))
        self._invalid(correlation, r"within \[-1, 1\]", estimate=2.0)
        self._invalid(
            correlation,
            "interval target",
            interval=replace(correlation.interval, target="other"),
        )
        self._invalid(
            correlation,
            "work is inconsistent",
            resampling=replace(
                correlation.resampling,
                calculated_work=correlation.resampling.calculated_work + 1,
            ),
        )
        self._invalid(correlation, "estimate is inconsistent", estimate=0.0)
        self._invalid(
            correlation,
            "test is inconsistent",
            test=replace(correlation.test, df2=correlation.test.df2 + 1.0),
        )
        outside = IntervalResult(
            target=correlation.interval.target,
            method=correlation.interval.method,
            level=correlation.interval.level,
            low=-2.0,
            high=0.5,
        )
        self._invalid(correlation, "outside", interval=outside)

    def test_matrix_comparison_and_correction_cross_fields(self) -> None:
        matrix = cast(
            RobustCorrelationMatrixResult,
            analyze_ggcorrmat(
                _association_frame(),
                ("x", "y"),
                type="robust",
                random_seed=3,
                bootstrap_resamples=999,
            ).result,
        )
        diagonal = matrix.cells[0]
        off = next(cell for cell in matrix.cells if cell.x != cell.y)
        self._invalid(diagonal, "structural", estimate=0.0)
        self._invalid(off, "complete inference", interval=None)
        self._invalid(off, "kernel count", n_obs=off.n_obs + 1)
        self._invalid(matrix, "identity", analysis="bad")
        self._invalid(matrix, "unique", columns=("x", "x"))
        self._invalid(matrix, "every ordered", cells=matrix.cells[:-1])
        self._invalid(matrix, "adjustment", p_adjust="bonferroni")
        self._invalid(matrix, "significance", sig_level=2.0)
        self._invalid(matrix, "exceeds", maximum_resample_work=1)
        self._invalid(matrix, "total", calculated_resample_work=1)
        mirror = next(
            cell for cell in matrix.cells if (cell.x, cell.y) == (off.y, off.x)
        )
        altered_mirror = replace(mirror, estimate=mirror.estimate / 2.0)
        cells = tuple(
            altered_mirror if (cell.x, cell.y) == (off.y, off.x) else cell
            for cell in matrix.cells
        )
        self._invalid(matrix, "symmetric", cells=cells)

        between = cast(
            RobustComparisonResult,
            analyze_ggbetweenstats(
                _between_frame(), "group", "value", type="robust"
            ).result,
        )
        level = between.levels[0]
        self._invalid(level, "non-empty", level="")
        self._invalid(level, "match", mean=level.mean + 1.0)
        self._invalid(level, "positive", standard_deviation=0.0)
        self._invalid(
            level,
            "inconsistent",
            standard_deviation=level.standard_deviation * 2.0,
        )
        pair = between.pairwise[0]
        self._invalid(pair, "differ", right=pair.left)
        self._invalid(pair, "finite", estimate=float("nan"))
        self._invalid(pair, "positive", standard_error=0.0)
        self._invalid(
            pair, "raw effect", effect_size=replace(pair.effect_size, value=0.0)
        )
        self._invalid(pair, "provenance", difference_kernel=pair.left_kernel)
        changed_estimate = pair.estimate + 1.0
        self._invalid(
            pair,
            "estimate is inconsistent",
            estimate=changed_estimate,
            effect_size=replace(pair.effect_size, value=changed_estimate),
        )
        self._invalid(pair, "standard error", standard_error=pair.standard_error + 1.0)
        self._invalid(
            pair,
            "statistic",
            test=replace(pair.test, statistic=cast(float, pair.test.statistic) + 1.0),
        )
        self._invalid(
            pair,
            "degrees of freedom",
            test=replace(pair.test, df2=pair.test.df2 + 1.0),
        )
        self._invalid(pair, "adjusted", adjusted_p_value=2.0)

        repeated = cast(
            RobustComparisonResult,
            analyze_ggwithinstats(
                _within_frame(),
                "condition",
                "value",
                subject_id="subject",
                type="robust",
            ).result,
        )
        correction = cast(Any, repeated.correction)
        self._invalid(correction, "identity", name="other")
        self._invalid(correction, "finite", covariance_a=float("nan"))
        self._invalid(correction, "invalid", epsilon=0.0)
        self._invalid(correction, "p_value", corrected_p_value=2.0)
        self._invalid(correction, "degrees", corrected_df1=999.0)
        self._invalid(between, "schema", schema_version=1)
        self._invalid(between, "identity", design="within")
        self._invalid(between, "2-20", levels=(between.levels[0],))
        self._invalid(between, "subject", subject_id="subject")
        self._invalid(between, "counts", sample=SampleAudit(19, 19, 0))
        self._invalid(
            between, "primary", estimate=1.0, interval=between.levels[0].interval
        )
        self._invalid(between, "family", pairwise=())
        self._invalid(
            between,
            "significance",
            pairwise=(
                replace(pair, significant=not pair.significant),
                *between.pairwise[1:],
            ),
        )
        self._invalid(
            repeated,
            "correction differ",
            omnibus=replace(repeated.omnibus, df2=repeated.omnibus.df2 + 1.0),
        )


def kernel_for_n(n: int) -> TrimmedKernelResult:
    return trimmed_kernel(np.arange(1.0, float(n + 1)))[0]


if __name__ == "__main__":
    unittest.main()
