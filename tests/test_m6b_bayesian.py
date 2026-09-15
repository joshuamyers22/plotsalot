from __future__ import annotations

import unittest
from collections.abc import Callable
from dataclasses import replace
from math import isfinite
from typing import cast
from unittest.mock import patch

import numpy as np
import polars as pl

import plotsalot.bayesian as bayesian_engine
from plotsalot import (
    BayesianCategoricalResult,
    BayesianComparisonResult,
    BayesianCorrelationMatrixResult,
    BayesianCorrelationResult,
    BayesianDotPlotResult,
    BayesianOneSampleResult,
    analyze_categorical,
    analyze_ggbetweenstats,
    analyze_ggcorrmat,
    analyze_ggdotplotstats,
    analyze_gghistostats,
    analyze_ggscatterstats,
    analyze_ggwithinstats,
    ggbarstats,
    ggbetweenstats,
    gghistostats,
    ggscatterstats,
    ggwithinstats,
    grouped_ggbarstats,
    grouped_ggbetweenstats,
    grouped_gghistostats,
    render_ggcorrmat,
    render_ggdotplotstats,
    render_gghistostats,
    render_ggscatterstats,
)
from plotsalot.bayesian_result import bounded_bf10_text
from plotsalot.result import IntervalResult, SampleAudit


class BayesianOneSampleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.frame = pl.DataFrame({"value": [1.0, 2.0, 3.0, 4.0, 5.0, None]})

    def test_exact_result_and_render_contract(self) -> None:
        analysis = analyze_gghistostats(
            self.frame,
            "value",
            type="bayes",
            test_value=0.0,
            prior_scale=2.0,
        )
        result = analysis.result
        self.assertIsInstance(result, BayesianOneSampleResult)
        bayesian = result
        assert isinstance(bayesian, BayesianOneSampleResult)
        self.assertEqual(bayesian.schema_version, 3)
        self.assertEqual(bayesian.sample.analyzed_rows, 5)
        self.assertEqual(bayesian.sample.dropped_null_rows, 1)
        self.assertEqual(bayesian.prior.family, "standardized_normal_inverse_gamma")
        self.assertEqual(len(bayesian.evidence.sensitivity), 2)
        self.assertTrue(isfinite(bayesian.evidence.log_bf10))
        self.assertLess(
            bayesian.location.interval.low,
            bayesian.location.median,
        )
        self.assertGreater(
            bayesian.location.interval.high,
            bayesian.location.median,
        )
        plot = render_gghistostats(analysis)
        self.assertIs(plot.result, result)
        self.assertIn(bayesian.evidence.display, plot.annotations.subtitle)
        self.assertIn("equal-tail credible interval", plot.annotations.caption)

    def test_location_scale_equivariance(self) -> None:
        base = gghistostats(
            self.frame,
            "value",
            type="bayes",
            test_value=0.0,
            prior_scale=2.0,
        ).result
        shifted_frame = self.frame.with_columns(
            (pl.col("value") * 10.0 + 7.0).alias("value")
        )
        shifted = gghistostats(
            shifted_frame,
            "value",
            type="bayes",
            test_value=7.0,
            prior_scale=20.0,
        ).result
        assert isinstance(base, BayesianOneSampleResult)
        assert isinstance(shifted, BayesianOneSampleResult)
        self.assertAlmostEqual(
            shifted.location.median,
            10.0 * base.location.median + 7.0,
            places=12,
        )
        self.assertAlmostEqual(shifted.evidence.log_bf10, base.evidence.log_bf10)

    def test_constant_sample_is_supported_by_proper_prior(self) -> None:
        result = gghistostats(
            pl.DataFrame({"value": [2.0, 2.0, 2.0]}),
            "value",
            type="bayes",
            test_value=0.0,
            prior_scale=1.0,
        ).result
        self.assertIsInstance(result, BayesianOneSampleResult)

    def test_invalid_or_unused_options_fail(self) -> None:
        with self.assertRaisesRegex(ValueError, "prior_scale is required"):
            gghistostats(self.frame, "value", type="bayes")
        with self.assertRaisesRegex(ValueError, "two-sided"):
            gghistostats(
                self.frame,
                "value",
                type="bayes",
                prior_scale=1.0,
                alternative="greater",
            )
        with self.assertRaisesRegex(ValueError, "unused"):
            gghistostats(self.frame, "value", prior_scale=1.0)

    def test_result_rejects_evidence_display_mutation(self) -> None:
        result = gghistostats(self.frame, "value", type="bayes", prior_scale=1.0).result
        assert isinstance(result, BayesianOneSampleResult)
        with self.assertRaisesRegex(ValueError, "display"):
            replace(result.evidence, display="BF10 = 999")


class BayesianCorrelationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.frame = pl.DataFrame(
            {
                "x": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, None],
                "y": [1.2, 1.8, 3.4, 3.7, 5.2, 5.7, 9.0],
            }
        )

    def test_quadrature_result_and_render_contract(self) -> None:
        analysis = analyze_ggscatterstats(self.frame, "x", "y", type="bayes")
        result = analysis.result
        self.assertIsInstance(result, BayesianCorrelationResult)
        bayesian = result
        assert isinstance(bayesian, BayesianCorrelationResult)
        self.assertEqual(
            bayesian.computation.algorithm, "adaptive_gauss_kronrod_correlation"
        )
        self.assertGreater(bayesian.computation.evaluations, 0)
        self.assertGreater(bayesian.posterior.median, 0.0)
        self.assertGreater(bayesian.posterior.probability_above_null, 0.5)
        plot = render_ggscatterstats(analysis)
        self.assertIs(plot.result, result)
        self.assertIn(bayesian.evidence.display, plot.annotations.subtitle)

    def test_work_is_reserved_before_quadrature(self) -> None:
        with (
            patch.object(
                bayesian_engine.scipy_integrate,
                "quad",
                wraps=bayesian_engine.scipy_integrate.quad,
            ) as quadrature,
            self.assertRaisesRegex(ValueError, "exceeds"),
        ):
            analyze_ggscatterstats(
                self.frame,
                "x",
                "y",
                type="bayes",
                maximum_bayesian_work=bayesian_engine.CORRELATION_RESERVED_WORK - 1,
            )
        quadrature.assert_not_called()

    def test_tail_quadrature_error_is_blocking(self) -> None:
        original = cast(
            Callable[..., tuple[float, float, dict[str, int]]],
            bayesian_engine.scipy_integrate.quad,
        )
        call_count = 0

        def inject_tail_error(
            *args: object, **kwargs: object
        ) -> tuple[float, float, dict[str, int]]:
            nonlocal call_count
            call_count += 1
            value, error, info = original(*args, **kwargs)
            if call_count == 4:
                error = 1.0
            return value, error, info

        with (
            patch.object(
                bayesian_engine.scipy_integrate,
                "quad",
                side_effect=inject_tail_error,
            ),
            self.assertRaisesRegex(ValueError, "tail quadrature exceeded"),
        ):
            analyze_ggscatterstats(self.frame, "x", "y", type="bayes")

    def test_sign_reversal_is_symmetric(self) -> None:
        positive = ggscatterstats(self.frame, "x", "y", type="bayes").result
        reversed_frame = self.frame.with_columns((-pl.col("y")).alias("y"))
        negative = ggscatterstats(reversed_frame, "x", "y", type="bayes").result
        assert isinstance(positive, BayesianCorrelationResult)
        assert isinstance(negative, BayesianCorrelationResult)
        self.assertAlmostEqual(
            negative.posterior.median, -positive.posterior.median, places=9
        )
        self.assertAlmostEqual(
            negative.evidence.log_bf10, positive.evidence.log_bf10, places=9
        )
        self.assertAlmostEqual(
            negative.posterior.probability_above_null,
            positive.posterior.probability_below_null,
            places=9,
        )

    def test_perfect_and_unused_options_fail(self) -> None:
        with self.assertRaisesRegex(ValueError, "perfect_correlation"):
            ggscatterstats(
                pl.DataFrame({"x": [1.0, 2.0, 3.0, 4.0], "y": [2.0, 4.0, 6.0, 8.0]}),
                "x",
                "y",
                type="bayes",
            )
        with self.assertRaisesRegex(ValueError, "unused"):
            ggscatterstats(
                self.frame,
                "x",
                "y",
                type="bayes",
                random_seed=1,
            )

    def test_complete_pointwise_matrix(self) -> None:
        frame = self.frame.with_columns(
            (pl.col("x") * 0.4 + pl.col("y") * 0.6).alias("z")
        )
        analysis = analyze_ggcorrmat(
            frame,
            ["x", "y", "z"],
            type="bayes",
            p_adjust="none",
        )
        result = analysis.result
        self.assertIsInstance(result, BayesianCorrelationMatrixResult)
        matrix = cast(BayesianCorrelationMatrixResult, result)
        self.assertEqual(len(matrix.cells), 9)
        self.assertEqual(sum(cell.evidence is not None for cell in matrix.cells), 6)
        self.assertEqual(matrix.evidence_scope, "pointwise_no_multiplicity_adjustment")
        plot = render_ggcorrmat(analysis)
        self.assertIs(plot.result, result)
        self.assertIn("numeric BF10", plot.annotations.caption)
        with self.assertRaisesRegex(ValueError, "p_adjust must be 'none'"):
            analyze_ggcorrmat(frame, ["x", "y"], type="bayes")


class BayesianDotPlotTests(unittest.TestCase):
    def test_label_posteriors_and_overall_evidence(self) -> None:
        frame = pl.DataFrame(
            {
                "value": [1.0, 2.0, 3.0, 3.0, 4.0, 5.0, 5.0, 6.0, 7.0],
                "label": ["a", "a", "a", "b", "b", "b", "c", "c", "c"],
            }
        )
        analysis = analyze_ggdotplotstats(
            frame,
            "value",
            "label",
            type="bayes",
            prior_scale=2.0,
        )
        result = analysis.result
        self.assertIsInstance(result, BayesianDotPlotResult)
        dot = cast(BayesianDotPlotResult, result)
        self.assertEqual(len(dot.estimates), 3)
        self.assertEqual(
            [item.value for item in dot.estimates],
            sorted(item.value for item in dot.estimates),
        )
        self.assertTrue(all(item.sample.analyzed_rows == 3 for item in dot.estimates))
        plot = render_ggdotplotstats(analysis)
        self.assertIs(plot.result, result)
        self.assertIn(dot.one_sample.evidence.display, plot.annotations.subtitle)


class BayesianComparisonTests(unittest.TestCase):
    def test_bayesian_child_seed_uses_typed_length_prefixed_identity(self) -> None:
        seed = bayesian_engine.bayesian_child_seed(
            42, "grouped", (("group", "a|group:str:b"), ("level", "c"))
        )
        self.assertEqual(
            seed,
            bayesian_engine.bayesian_child_seed(
                42, "grouped", (("group", "a|group:str:b"), ("level", "c"))
            ),
        )
        self.assertNotEqual(
            seed,
            bayesian_engine.bayesian_child_seed(
                42, "grouped", (("group", "a"), ("level", "b|level:str:c"))
            ),
        )
        self.assertNotEqual(
            bayesian_engine.bayesian_child_seed(42, "grouped", (("group", 1),)),
            bayesian_engine.bayesian_child_seed(42, "grouped", (("group", "1"),)),
        )
        self.assertNotEqual(
            bayesian_engine.bayesian_child_seed(42, "grouped", (("group", True),)),
            bayesian_engine.bayesian_child_seed(42, "grouped", (("group", 1.0),)),
        )
        with self.assertRaisesRegex(TypeError, "finite scalar"):
            bayesian_engine.bayesian_child_seed(
                42, "grouped", (("group", float("nan")),)
            )
        with self.assertRaisesRegex(ValueError, "complete labels"):
            bayesian_engine.bayesian_child_seed(42, "", (("group", "a"),))

    def test_engine_shape_and_nonfinite_qmc_failures_are_blocking(self) -> None:
        values = (np.array([1.0, 2.0, 3.0]), np.array([2.0, 3.0, 4.0]))
        with self.assertRaisesRegex(ValueError, "three rows per level"):
            bayesian_engine.independent_comparison_posterior(
                values,
                ("a",),
                prior_location=0.0,
                prior_scale=1.0,
                credible_level=0.95,
                random_seed=1,
            )
        with self.assertRaisesRegex(ValueError, "three complete blocks"):
            bayesian_engine.repeated_comparison_posterior(
                np.ones((2, 2)),
                ("a", "b"),
                prior_location=0.0,
                prior_scale=1.0,
                credible_level=0.95,
                random_seed=1,
            )
        with self.assertRaisesRegex(ValueError, "identities do not match"):
            bayesian_engine.independent_categorical_posterior(
                np.ones((2, 2)),
                row_identities=("a",),
                column_identities=("x", "y"),
                prior_cell_concentration=1.0,
                credible_level=0.95,
                random_seed=1,
            )
        with (
            patch.object(
                bayesian_engine.scipy_special,
                "ndtri",
                return_value=np.full((4096, 2), np.nan),
            ),
            self.assertRaisesRegex(ValueError, "non-finite draws"),
        ):
            bayesian_engine.independent_comparison_posterior(
                values,
                ("a", "b"),
                prior_location=0.0,
                prior_scale=1.0,
                credible_level=0.95,
                random_seed=1,
            )

    def test_independent_rqmc_result_is_deterministic_and_equivariant(self) -> None:
        frame = pl.DataFrame(
            {
                "group": ["a"] * 5 + ["b"] * 5 + ["c"] * 5,
                "value": [
                    1.0,
                    2.0,
                    2.0,
                    3.0,
                    2.5,
                    3.0,
                    4.0,
                    4.5,
                    5.0,
                    4.0,
                    2.0,
                    3.0,
                    4.0,
                    5.0,
                    6.0,
                ],
            }
        )
        first = ggbetweenstats(
            frame,
            "group",
            "value",
            type="bayes",
            p_adjust="none",
            pairwise_display="all",
            prior_location=0.0,
            prior_scale=2.0,
            random_seed=17,
        ).result
        second = analyze_ggbetweenstats(
            frame,
            "group",
            "value",
            type="bayes",
            p_adjust="none",
            pairwise_display="all",
            prior_location=0.0,
            prior_scale=2.0,
            random_seed=17,
        ).result
        self.assertIsInstance(first, BayesianComparisonResult)
        self.assertEqual(first, second)
        bayesian = cast(BayesianComparisonResult, first)
        self.assertEqual(len(bayesian.pairwise), 3)
        self.assertEqual(bayesian.computation.qmc_replicates, 8)
        self.assertEqual(len(bayesian.computation.qmc_targets), 6)
        self.assertEqual(bayesian.computation.calculated_work, 131_072)
        shifted = frame.with_columns((pl.col("value") * 3.0 + 4.0).alias("value"))
        shifted_result = ggbetweenstats(
            shifted,
            "group",
            "value",
            type="bayes",
            p_adjust="none",
            pairwise_display="all",
            prior_location=4.0,
            prior_scale=6.0,
            random_seed=17,
        ).result
        shifted_bayesian = cast(BayesianComparisonResult, shifted_result)
        self.assertAlmostEqual(
            shifted_bayesian.omnibus.log_bf10, bayesian.omnibus.log_bf10, places=10
        )

    def test_complete_block_and_required_seed(self) -> None:
        frame = pl.DataFrame(
            {
                "subject": [value for value in range(6) for _ in range(3)],
                "condition": ["a", "b", "c"] * 6,
                "value": pl.Series(
                    [
                        1,
                        2,
                        3,
                        2,
                        2.5,
                        4,
                        1.5,
                        3,
                        4,
                        2,
                        3.5,
                        5,
                        1,
                        2.2,
                        3.4,
                        2.1,
                        3.2,
                        4.8,
                    ],
                    dtype=pl.Float64,
                ),
            }
        )
        result = ggwithinstats(
            frame,
            "condition",
            "value",
            subject_id="subject",
            type="bayes",
            p_adjust="none",
            pairwise_display="all",
            prior_location=0.0,
            prior_scale=2.0,
            random_seed=11,
        ).result
        self.assertIsInstance(result, BayesianComparisonResult)
        within = cast(BayesianComparisonResult, result)
        self.assertEqual(within.design, "within")
        self.assertEqual(len(within.pairwise), 3)
        self.assertEqual(len(within.computation.qmc_targets), 6)
        self.assertEqual(within.computation.calculated_work, 163_840)
        with self.assertRaisesRegex(ValueError, "random_seed"):
            analyze_ggwithinstats(
                frame,
                "condition",
                "value",
                subject_id="subject",
                type="bayes",
                p_adjust="none",
                pairwise_display="all",
                prior_location=0.0,
                prior_scale=2.0,
            )


class BayesianCategoricalTests(unittest.TestCase):
    def test_fixed_total_closed_form_and_zero_cell(self) -> None:
        frame = pl.DataFrame({"answer": ["a", "b", "c"], "count": [15, 10, 0]})
        result = ggbarstats(
            frame,
            "answer",
            counts="count",
            type="bayes",
            p_adjust="none",
            pairwise_display="all",
        ).result
        self.assertIsInstance(result, BayesianCategoricalResult)
        bayesian = cast(BayesianCategoricalResult, result)
        self.assertEqual(
            bayesian.computation.algorithm, "closed_form_dirichlet_multinomial"
        )
        self.assertEqual(len(bayesian.cells), 3)
        self.assertTrue(all(item.posterior.median > 0.0 for item in bayesian.cells))

    def test_fixed_rows_rqmc_and_paired_failure(self) -> None:
        frame = pl.DataFrame(
            {
                "group": ["a", "a", "b", "b"],
                "answer": ["yes", "no", "yes", "no"],
                "count": [18, 2, 7, 13],
            }
        )
        analysis = analyze_categorical(
            frame,
            "group",
            "answer",
            counts="count",
            type="bayes",
            p_adjust="none",
            pairwise_display="all",
            random_seed=23,
        )
        self.assertIsInstance(analysis.result, BayesianCategoricalResult)
        bayesian = cast(BayesianCategoricalResult, analysis.result)
        self.assertIsNotNone(bayesian.effect)
        self.assertEqual(len(bayesian.contrasts), 2)
        self.assertEqual(bayesian.computation.qmc_points_per_replicate, 4096)
        self.assertEqual(len(bayesian.computation.qmc_targets), 7)
        self.assertEqual(bayesian.computation.calculated_work, 131_072)
        with self.assertRaisesRegex(ValueError, "paired Bayesian"):
            analyze_categorical(
                frame,
                "group",
                "answer",
                counts="count",
                type="bayes",
                paired=True,
                p_adjust="none",
                pairwise_display="all",
                random_seed=23,
            )


class BayesianResultMutationTests(unittest.TestCase):
    def setUp(self) -> None:
        frame = pl.DataFrame({"value": [1.0, 2.0, 3.0, 4.0]})
        one = gghistostats(frame, "value", type="bayes", prior_scale=2.0).result
        assert isinstance(one, BayesianOneSampleResult)
        self.one = one
        correlation = ggscatterstats(
            pl.DataFrame({"x": [1.0, 2.0, 3.0, 4.0], "y": [1.0, 2.1, 2.8, 4.2]}),
            "x",
            "y",
            type="bayes",
        ).result
        assert isinstance(correlation, BayesianCorrelationResult)
        self.correlation = correlation

    def _invalid(self, constructor: Callable[[], object]) -> None:
        with self.assertRaises((TypeError, ValueError)):
            constructor()

    def test_common_contract_mutations(self) -> None:
        method = self.one.method
        parameter = self.one.prior.parameters[0]
        prior = self.one.prior
        posterior = self.one.location
        evidence = self.one.evidence
        computation = self.one.computation
        mutations = (
            lambda: replace(method, name=""),
            lambda: replace(method, compatibility="copied"),
            lambda: replace(parameter, name=""),
            lambda: replace(parameter, value=float("nan")),
            lambda: replace(prior, proper=False),
            lambda: replace(prior, parameters=(parameter, parameter)),
            lambda: replace(posterior, target=""),
            lambda: replace(posterior, median=float("nan")),
            lambda: replace(
                posterior,
                interval=IntervalResult("wrong", "bayesian_equal_tail", 0.95, 0, 1),
            ),
            lambda: replace(
                posterior,
                interval=IntervalResult(posterior.target, "wrong_method", 0.95, 0, 1),
            ),
            lambda: replace(posterior, median=posterior.interval.high + 1),
            lambda: replace(posterior, probability_above_null=2.0),
            lambda: replace(posterior, probability_at_null=0.2),
            lambda: replace(evidence, null_hypothesis=""),
            lambda: replace(evidence, log_bf10=float("inf")),
            lambda: replace(evidence, prior_model_odds=2.0),
            lambda: replace(evidence, sensitivity=()),
            lambda: replace(computation, algorithm="unknown"),
            lambda: replace(computation, calculated_work=0),
            lambda: replace(computation, maximum_work=0),
            lambda: replace(computation, absolute_tolerance=-1.0),
            lambda: replace(computation, absolute_tolerance=1e-12),
            lambda: replace(computation, root_seed=-1),
            lambda: replace(computation, diagnostics=("",)),
            lambda: replace(computation, replicate_max_relative_se=0.0),
            lambda: replace(
                self.one,
                method=replace(self.one.method, name="other_valid_method"),
            ),
            lambda: replace(
                self.one,
                computation=replace(
                    computation, algorithm="closed_form_dirichlet_multinomial"
                ),
            ),
        )
        for index, mutation in enumerate(mutations):
            with self.subTest(mutation=index):
                self._invalid(mutation)


class BayesianGroupedTests(unittest.TestCase):
    def setUp(self) -> None:
        one = gghistostats(
            pl.DataFrame({"value": [1.0, 2.0, 3.0, 4.0]}),
            "value",
            type="bayes",
            prior_scale=2.0,
        ).result
        assert isinstance(one, BayesianOneSampleResult)
        self.one = one
        correlation = ggscatterstats(
            pl.DataFrame({"x": [1.0, 2.0, 3.0, 4.0], "y": [1.0, 2.1, 2.8, 4.2]}),
            "x",
            "y",
            type="bayes",
        ).result
        assert isinstance(correlation, BayesianCorrelationResult)
        self.correlation = correlation

    def _invalid(self, constructor: Callable[[], object]) -> None:
        with self.assertRaises((TypeError, ValueError)):
            constructor()

    def test_grouped_work_and_seed_provenance(self) -> None:
        histogram = pl.DataFrame(
            {
                "outer": ["x"] * 4 + ["y"] * 4,
                "value": [1.0, 2.0, 3.0, 4.0, 2.0, 3.0, 4.0, 5.0],
            }
        )
        exact = grouped_gghistostats(
            histogram, "value", "outer", type="bayes", prior_scale=2.0
        ).result
        self.assertEqual(exact.calculated_bayesian_work, 24)
        self.assertIsNone(exact.bayesian_root_seed)
        comparison = pl.DataFrame(
            {
                "outer": ["x"] * 8 + ["y"] * 8,
                "group": (["a"] * 4 + ["b"] * 4) * 2,
                "value": [
                    1.0,
                    2.0,
                    2.5,
                    3.0,
                    3.0,
                    4.0,
                    4.5,
                    5.0,
                    2.0,
                    3.0,
                    3.5,
                    4.0,
                    4.0,
                    5.0,
                    5.5,
                    6.0,
                ],
            }
        )
        grouped = grouped_ggbetweenstats(
            comparison,
            "group",
            "value",
            "outer",
            type="bayes",
            p_adjust="none",
            pairwise_display="all",
            prior_location=0.0,
            prior_scale=2.0,
            random_seed=29,
        ).result
        self.assertEqual(grouped.bayesian_root_seed, 29)
        self.assertEqual(grouped.calculated_bayesian_work, 196_608)
        child_seeds = tuple(
            cast(BayesianComparisonResult, item.result).computation.root_seed
            for item in grouped.groups
        )
        self.assertEqual(len(set(child_seeds)), 2)
        with self.assertRaisesRegex(ValueError, "exceeds"):
            grouped_ggbetweenstats(
                comparison,
                "group",
                "value",
                "outer",
                type="bayes",
                p_adjust="none",
                pairwise_display="all",
                prior_location=0.0,
                prior_scale=2.0,
                random_seed=29,
                maximum_bayesian_work=190_000,
            )

    def test_grouped_categorical_work(self) -> None:
        frame = pl.DataFrame(
            {
                "outer": ["x"] * 4 + ["y"] * 4,
                "group": ["a", "a", "b", "b"] * 2,
                "answer": ["yes", "no", "yes", "no"] * 2,
                "count": [8, 2, 3, 7, 6, 4, 4, 6],
            }
        )
        result = grouped_ggbarstats(
            frame,
            "group",
            "outer",
            "answer",
            counts="count",
            type="bayes",
            p_adjust="none",
            pairwise_display="all",
            random_seed=31,
        ).result
        self.assertEqual(result.bayesian_root_seed, 31)
        self.assertEqual(result.calculated_bayesian_work, 262_144)
        self.assertEqual(bounded_bf10_text(20.0), "BF10 > 1e6")
        self.assertEqual(bounded_bf10_text(-20.0), "BF10 < 1e-6")

    def test_one_sample_and_correlation_mutations(self) -> None:
        one = self.one
        correlation = self.correlation
        bad_sample = SampleAudit(2, 2, 0)
        one_mutations = (
            lambda: replace(one, schema_version=2),
            lambda: replace(one, analysis="wrong"),
            lambda: replace(one, column=""),
            lambda: replace(one, sample=bad_sample),
            lambda: replace(one, location=replace(one.location, target="wrong")),
            lambda: replace(one, effect=replace(one.effect, target="wrong")),
            lambda: replace(
                one, effect=replace(one.effect, median=one.effect.median + 1)
            ),
            lambda: replace(one, warnings=("",)),
        )
        correlation_mutations = (
            lambda: replace(correlation, mode="wrong"),
            lambda: replace(correlation, x=""),
            lambda: replace(correlation, y=correlation.x),
            lambda: replace(correlation, sample=bad_sample),
            lambda: replace(correlation, sample_correlation=float("nan")),
            lambda: replace(correlation, sample_correlation=1.0),
            lambda: replace(correlation, computation=one.computation),
            lambda: replace(
                correlation,
                posterior=replace(correlation.posterior, target="wrong"),
            ),
            lambda: replace(correlation, warnings=("",)),
        )
        for index, mutation in enumerate((*one_mutations, *correlation_mutations)):
            with self.subTest(mutation=index):
                self._invalid(mutation)

    def test_qmc_and_family_mutations(self) -> None:
        frame = pl.DataFrame(
            {
                "g": ["a"] * 4 + ["b"] * 4,
                "y": [1.0, 2.0, 2.5, 3.0, 3.0, 4.0, 4.5, 5.0],
            }
        )
        result = ggbetweenstats(
            frame,
            "g",
            "y",
            type="bayes",
            p_adjust="none",
            pairwise_display="all",
            prior_location=0.0,
            prior_scale=2.0,
            random_seed=3,
        ).result
        assert isinstance(result, BayesianComparisonResult)
        result = cast(BayesianComparisonResult, result)
        computation = result.computation
        qmc_target = computation.qmc_targets[0]
        mutations = (
            lambda: replace(computation, qmc_replicates=7),
            lambda: replace(computation, qmc_points_per_replicate=2048),
            lambda: replace(computation, child_seeds=()),
            lambda: replace(
                computation,
                child_seeds=(computation.child_seeds[0],) * 8,
            ),
            lambda: replace(computation, root_seed=None),
            lambda: replace(
                computation, calculated_work=computation.calculated_work + 1
            ),
            lambda: replace(
                computation,
                replicate_max_relative_se=(computation.replicate_max_relative_se or 0.0)
                + 1e-6,
            ),
            lambda: replace(computation, qmc_targets=()),
            lambda: replace(
                computation,
                qmc_targets=(
                    replace(qmc_target, median_relative_se=0.006),
                    *computation.qmc_targets[1:],
                ),
            ),
            lambda: replace(result, analysis="wrong"),
            lambda: replace(
                result, method=replace(result.method, name="other_valid_method")
            ),
            lambda: replace(result, subject_id="unexpected"),
            lambda: replace(result, levels=result.levels[:1]),
            lambda: replace(result, levels=(result.levels[0], result.levels[0])),
            lambda: replace(result, pairwise=()),
            lambda: replace(result, pairwise_display="significant"),
            lambda: replace(result, warnings=("",)),
            lambda: replace(result.levels[0], n_obs=2),
            lambda: replace(result.pairwise[0], right=result.pairwise[0].left),
            lambda: replace(
                result.pairwise[0],
                posterior=replace(result.pairwise[0].posterior, target="wrong"),
            ),
        )
        for index, mutation in enumerate(mutations):
            with self.subTest(mutation=index):
                self._invalid(mutation)

    def test_dot_matrix_and_categorical_mutations(self) -> None:
        dot = analyze_ggdotplotstats(
            pl.DataFrame(
                {
                    "value": [1.0, 2.0, 3.0, 3.0, 4.0, 5.0],
                    "label": ["a", "a", "a", "b", "b", "b"],
                }
            ),
            "value",
            "label",
            type="bayes",
            prior_scale=2.0,
        ).result
        assert isinstance(dot, BayesianDotPlotResult)
        dot = cast(BayesianDotPlotResult, dot)
        matrix = analyze_ggcorrmat(
            pl.DataFrame(
                {
                    "x": [1.0, 2.0, 3.0, 4.0],
                    "y": [1.0, 2.1, 2.8, 4.2],
                }
            ),
            ["x", "y"],
            type="bayes",
            p_adjust="none",
        ).result
        assert isinstance(matrix, BayesianCorrelationMatrixResult)
        matrix = cast(BayesianCorrelationMatrixResult, matrix)
        categorical = analyze_categorical(
            pl.DataFrame(
                {
                    "group": ["a", "a", "b", "b"],
                    "answer": ["yes", "no", "yes", "no"],
                    "count": [8, 2, 3, 7],
                }
            ),
            "group",
            "answer",
            counts="count",
            type="bayes",
            p_adjust="none",
            pairwise_display="all",
            random_seed=4,
        ).result
        assert isinstance(categorical, BayesianCategoricalResult)
        categorical = cast(BayesianCategoricalResult, categorical)
        off_diagonal = matrix.cells[1]
        assert off_diagonal.posterior is not None
        matrix_posterior = off_diagonal.posterior
        mutations = (
            lambda: replace(dot, schema_version=2),
            lambda: replace(dot, x=""),
            lambda: replace(dot, label_column=dot.x),
            lambda: replace(dot, estimates=()),
            lambda: replace(dot, one_sample=replace(dot.one_sample, analysis="wrong")),
            lambda: replace(dot, estimates=(dot.estimates[0], dot.estimates[0])),
            lambda: replace(dot, estimates=tuple(reversed(dot.estimates))),
            lambda: replace(dot, warnings=("",)),
            lambda: replace(dot, method=dot.one_sample.method),
            lambda: replace(dot.estimates[0], label=""),
            lambda: replace(dot.estimates[0], label=float("nan")),
            lambda: replace(dot.estimates[0], sample=SampleAudit(2, 2, 0)),
            lambda: replace(
                dot.estimates[0],
                posterior=replace(dot.estimates[0].posterior, target="wrong"),
            ),
            lambda: replace(dot.estimates[0], warnings=("",)),
            lambda: replace(matrix, schema_version=2),
            lambda: replace(matrix, columns=("x",)),
            lambda: replace(matrix, cells=matrix.cells[:-1]),
            lambda: replace(matrix, cells=tuple(reversed(matrix.cells))),
            lambda: replace(matrix, evidence_scope="wrong"),
            lambda: replace(matrix, calculated_bayesian_work=0),
            lambda: replace(
                matrix,
                method=replace(matrix.method, name="exact_sample_correlation"),
            ),
            lambda: replace(matrix, warnings=("",)),
            lambda: replace(off_diagonal, x=""),
            lambda: replace(off_diagonal, posterior=None),
            lambda: replace(
                off_diagonal,
                posterior=replace(matrix_posterior, target="wrong"),
            ),
            lambda: replace(categorical, analysis="wrong"),
            lambda: replace(categorical, cells=categorical.cells[:-1]),
            lambda: replace(categorical, contrasts=()),
            lambda: replace(categorical, row_totals=(1, 1)),
            lambda: replace(categorical, pairwise_display="significant"),
            lambda: replace(
                categorical,
                prior=replace(categorical.prior, family="different_valid_family"),
            ),
            lambda: replace(categorical, warnings=("",)),
            lambda: replace(categorical.cells[0], observed=-1),
            lambda: replace(categorical.cells[0], displayed_proportion=2.0),
            lambda: replace(
                categorical.cells[0],
                posterior=replace(categorical.cells[0].posterior, target="wrong"),
            ),
            lambda: replace(
                categorical.contrasts[0], right=categorical.contrasts[0].left
            ),
            lambda: replace(
                categorical.contrasts[0],
                posterior=replace(categorical.contrasts[0].posterior, target="wrong"),
            ),
        )
        for index, mutation in enumerate(mutations):
            with self.subTest(mutation=index):
                self._invalid(mutation)


if __name__ == "__main__":
    unittest.main()
