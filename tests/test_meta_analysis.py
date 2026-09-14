from __future__ import annotations

import math
import unittest
from dataclasses import replace

import polars as pl

from plotsalot import analyze_ggcoefstats


def _frame(estimates: list[float], errors: list[float]) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "term": [f"study-{index + 1}" for index in range(len(estimates))],
            "estimate": estimates,
            "standard_error": errors,
        }
    )


def _analyze(estimates: list[float], errors: list[float]):
    return analyze_ggcoefstats(
        _frame(estimates, errors),
        meta_analytic_effect=True,
        estimand="mean treatment effect",
        effect_scale="mean difference",
        effect_direction="positive favors treatment",
        effect_units="points",
    )


def _independent_reml_likelihood(
    estimates: list[float], errors: list[float], *, upper: float = 5.0
) -> float:
    """Golden-section REML reference using the likelihood, not the score solver."""

    variances = [error * error for error in errors]

    def objective(tau_squared: float) -> float:
        weights = [1.0 / (variance + tau_squared) for variance in variances]
        total = sum(weights)
        mean = (
            sum(
                weight * value for weight, value in zip(weights, estimates, strict=True)
            )
            / total
        )
        return 0.5 * (
            sum(math.log(variance + tau_squared) for variance in variances)
            + math.log(total)
            + sum(
                weight * (value - mean) ** 2
                for weight, value in zip(weights, estimates, strict=True)
            )
        )

    ratio = (math.sqrt(5.0) - 1.0) / 2.0
    low, high = 0.0, upper
    left = high - ratio * (high - low)
    right = low + ratio * (high - low)
    for _ in range(200):
        if objective(left) < objective(right):
            high, right = right, left
            left = high - ratio * (high - low)
        else:
            low, left = left, right
            right = low + ratio * (high - low)
    candidate = (low + high) / 2.0
    return 0.0 if objective(0.0) <= objective(candidate) else candidate


class MetaAnalysisTests(unittest.TestCase):
    def test_equal_variance_case_has_analytic_reml_and_hk_results(self) -> None:
        result = _analyze([0.0, 1.0, 2.0, 3.0, 4.0], [0.5] * 5).result
        meta = result.meta_analysis

        self.assertAlmostEqual(meta.heterogeneity.tau_squared, 2.25, places=10)
        self.assertAlmostEqual(meta.pooled.estimate, 2.0, places=12)
        self.assertAlmostEqual(meta.pooled.q_hk, 1.0, places=12)
        self.assertAlmostEqual(meta.pooled.q_star, 1.0, places=12)
        self.assertAlmostEqual(meta.pooled.adjusted_variance, 0.5, places=12)
        self.assertAlmostEqual(meta.heterogeneity.q, 40.0, places=12)
        self.assertAlmostEqual(meta.heterogeneity.i_squared, 0.9, places=12)
        self.assertFalse(meta.convergence.boundary)
        self.assertIsNotNone(meta.prediction.interval)
        self.assertAlmostEqual(
            sum(term.normalized_weight for term in result.terms), 1.0
        )
        self.assertAlmostEqual(
            sum(term.weighted_contribution for term in result.terms), 2.0
        )

    def test_unequal_variance_reml_matches_independent_likelihood_optimization(
        self,
    ) -> None:
        estimates = [0.1, 0.5, 1.2, -0.2, 1.8]
        errors = [0.1, 0.2, 0.25, 0.15, 0.3]

        result = _analyze(estimates, errors).result
        independent = _independent_reml_likelihood(estimates, errors)

        self.assertAlmostEqual(
            result.meta_analysis.heterogeneity.tau_squared,
            independent,
            places=7,
        )
        self.assertAlmostEqual(
            result.meta_analysis.heterogeneity.tau_squared,
            0.5987435085712893,
            places=10,
        )
        self.assertAlmostEqual(
            result.meta_analysis.pooled.estimate, 0.6493463818155951, places=11
        )
        self.assertTrue(result.meta_analysis.convergence.converged)
        self.assertFalse(result.meta_analysis.convergence.boundary)

    def test_reml_bracket_expansion_is_retained(self) -> None:
        result = _analyze(
            [-8.384213933306778, -4.165757655832687, 7.8848438485567165],
            [0.002402898347348834, 0.014298763677961509, 0.0006962608039510888],
        ).result

        self.assertEqual(result.meta_analysis.convergence.bracket_expansions, 1)
        self.assertGreater(result.meta_analysis.convergence.bracket_high, 1.0)

    def test_zero_boundary_and_prediction_rules_are_explicit(self) -> None:
        five = _analyze([0.1, 0.2, 0.3, 0.4, 0.5], [0.2] * 5).result
        three = _analyze([1.0, 1.0, 1.0], [0.2] * 3).result

        self.assertEqual(five.meta_analysis.heterogeneity.tau_squared, 0.0)
        self.assertTrue(five.meta_analysis.convergence.boundary)
        prediction = five.meta_analysis.prediction.interval
        if prediction is None:
            self.fail("five-study result must retain a prediction interval")
        self.assertEqual(
            (prediction.low, prediction.high),
            (
                five.meta_analysis.pooled.interval.low,
                five.meta_analysis.pooled.interval.high,
            ),
        )
        self.assertIsNone(three.meta_analysis.prediction.interval)
        self.assertEqual(
            three.meta_analysis.prediction.absence_reason,
            "fewer_than_five_studies",
        )
        self.assertIn("fewer than five studies", three.warnings[0])
        self.assertFalse(any(term.inference.df is not None for term in three.terms))

    def test_scale_equivariance_and_named_study_order(self) -> None:
        estimates = [0.1, 0.5, 1.2, -0.2, 1.8]
        errors = [0.1, 0.2, 0.25, 0.15, 0.3]
        base = _analyze(estimates, errors).result
        scaled = _analyze(
            [value * 100.0 for value in estimates],
            [value * 100.0 for value in errors],
        ).result

        self.assertAlmostEqual(
            scaled.meta_analysis.pooled.estimate,
            base.meta_analysis.pooled.estimate * 100.0,
            places=9,
        )
        self.assertAlmostEqual(
            scaled.meta_analysis.heterogeneity.tau_squared,
            base.meta_analysis.heterogeneity.tau_squared * 10_000.0,
            places=7,
        )
        self.assertEqual(scaled.source_order, base.source_order)
        for original, transformed in zip(base.terms, scaled.terms, strict=True):
            self.assertAlmostEqual(
                original.normalized_weight, transformed.normalized_weight, places=12
            )

    def test_meta_options_and_resources_fail_explicitly(self) -> None:
        data = _frame([0.0, 1.0, 2.0], [0.5] * 3)

        def call(**kwargs: object):
            options: dict[str, object] = {
                "meta_analytic_effect": True,
                "estimand": "effect",
                "effect_scale": "difference",
                "effect_direction": "positive is higher",
                "effect_units": "points",
            }
            options.update(kwargs)
            return analyze_ggcoefstats(data, **options)  # type: ignore[arg-type]

        cases = (
            lambda: analyze_ggcoefstats(data),
            lambda: call(estimand=""),
            lambda: call(estimand=1),
            lambda: call(dependence="clustered"),
            lambda: call(null_value=float("nan")),
            lambda: call(null_value=True),
            lambda: call(conf_level=1.0),
            lambda: call(stats_labels=1),
            lambda: call(maximum_rendered_points=2),
            lambda: call(maximum_labels=2),
            lambda: call(maximum_labels=0),
            lambda: call(maximum_labels=1_001),
            lambda: call(maximum_rendered_points=1_001),
            lambda: analyze_ggcoefstats(
                _frame([0.0, 1.0, 2.0], [1e-300, 1e-300, 1e-300]),
                meta_analytic_effect=True,
                estimand="effect",
                effect_scale="difference",
                effect_direction="positive is higher",
                effect_units="points",
            ),
        )
        for operation in cases:
            with (
                self.subTest(operation=operation),
                self.assertRaises((TypeError, ValueError)),
            ):
                operation()

    def test_analysis_record_rejects_each_table_result_mismatch(self) -> None:
        analysis = _analyze([0.0, 1.0, 2.0], [0.5] * 3)
        cases = (
            lambda: type(analysis)(
                replace(analysis.table, terms=("other", "study-2", "study-3")),
                analysis.result,
            ),
            lambda: type(analysis)(
                replace(
                    analysis.table,
                    estimates=analysis.table.estimates + [1.0, 0.0, 0.0],
                ),
                analysis.result,
            ),
            lambda: type(analysis)(
                replace(
                    analysis.table,
                    standard_errors=analysis.table.standard_errors * 2.0,
                ),
                analysis.result,
            ),
        )
        for operation in cases:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()


if __name__ == "__main__":
    unittest.main()
