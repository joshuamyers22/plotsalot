from __future__ import annotations

import json
import unittest
from dataclasses import replace
from importlib import import_module
from math import lgamma, log, pi
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import patch

import numpy as np
import polars as pl

from plotsalot import (
    BayesianMetaAnalysis,
    BayesianMetaResult,
    CoefficientAnalysis,
    M6CMetaError,
    RobustMetaAnalysis,
    analyze_ggcoefstats,
    render_ggcoefstats,
)

COMMON: dict[str, Any] = {
    "meta_analytic_effect": True,
    "estimand": "population treatment effect",
    "effect_scale": "mean difference",
    "effect_direction": "positive favors treatment",
    "effect_units": "points",
}
ROOT = Path(__file__).resolve().parents[1]


def frame(estimates: list[float], errors: list[float]) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "term": [f"study-{index + 1}" for index in range(len(estimates))],
            "estimate": estimates,
            "standard_error": errors,
        }
    )


ROBUST_ESTIMATES = [0.1, 0.3, 0.2, 0.5, 0.4, 0.0, 0.6, 0.35, 0.25, 3.0]
ROBUST_ERRORS = [0.2, 0.25, 0.2, 0.3, 0.22, 0.18, 0.28, 0.2, 0.24, 0.3]
BAYES_ESTIMATES = [0.2, 0.4, 0.1]
BAYES_ERRORS = [0.2, 0.25, 0.3]


def robust(**changes: object) -> RobustMetaAnalysis:
    options: dict[str, Any] = {**COMMON, "type": "robust"}
    options.update(changes)
    return cast(
        RobustMetaAnalysis,
        analyze_ggcoefstats(frame(ROBUST_ESTIMATES, ROBUST_ERRORS), **options),
    )


def bayes(**changes: object) -> BayesianMetaAnalysis:
    options: dict[str, Any] = {
        **COMMON,
        "type": "bayes",
        "prior_mean_scale": 1.0,
        "prior_tau_scale": 0.5,
    }
    options.update(changes)
    return cast(
        BayesianMetaAnalysis,
        analyze_ggcoefstats(frame(BAYES_ESTIMATES, BAYES_ERRORS), **options),
    )


def student_t4_log_likelihood(
    estimates: np.ndarray[Any, np.dtype[np.float64]],
    errors: np.ndarray[Any, np.dtype[np.float64]],
    mu: float,
    tau_squared: float,
) -> float:
    d = errors * errors + tau_squared
    squared = (estimates - mu) ** 2
    constant = lgamma(2.5) - lgamma(2.0) - 0.5 * log(4.0 * pi)
    return float(
        np.sum(constant - 0.5 * np.log(d) - 2.5 * np.log1p(squared / (4.0 * d)))
    )


def golden_profile(
    estimates: np.ndarray[Any, np.dtype[np.float64]],
    errors: np.ndarray[Any, np.dtype[np.float64]],
    mu: float,
) -> float:
    ratio = (5.0**0.5 - 1.0) / 2.0
    low, high = 0.0, 25.0
    left = high - ratio * (high - low)
    right = low + ratio * (high - low)
    for _ in range(250):
        if student_t4_log_likelihood(
            estimates, errors, mu, left
        ) > student_t4_log_likelihood(estimates, errors, mu, right):
            high, right = right, left
            left = high - ratio * (high - low)
        else:
            low, left = left, right
            right = low + ratio * (high - low)
    candidate = (low + high) / 2.0
    zero = student_t4_log_likelihood(estimates, errors, mu, 0.0)
    fitted = student_t4_log_likelihood(estimates, errors, mu, candidate)
    return max(zero, fitted)


def independent_log_bf10(
    estimates: np.ndarray[Any, np.dtype[np.float64]],
    errors: np.ndarray[Any, np.dtype[np.float64]],
    mean_scale: float,
    tau_scale: float,
) -> float:
    x = np.linspace(0.0, 1.0 - 1e-8, 200_001)
    tau = tau_scale * x / (1.0 - x)
    d = errors[None, :] ** 2 + tau[:, None] ** 2
    centered = estimates[None, :]
    base = -0.5 * (estimates.size * log(2.0 * pi) + np.sum(np.log(d), axis=1))
    h0 = base - 0.5 * np.sum(centered * centered / d, axis=1)
    precision = 1.0 / (mean_scale * mean_scale) + np.sum(1.0 / d, axis=1)
    b = np.sum(centered / d, axis=1)
    c = np.sum(centered * centered / d, axis=1)
    h1 = (
        base - log(mean_scale) - 0.5 * np.log(precision) - 0.5 * (c - b * b / precision)
    )
    common = (
        0.5 * log(2.0 / pi)
        - log(tau_scale)
        - 0.5 * (tau / tau_scale) ** 2
        + log(tau_scale)
        - 2.0 * np.log1p(-x)
    )

    def integrate_log(values: np.ndarray[Any, np.dtype[np.float64]]) -> float:
        peak = float(np.max(values))
        return peak + log(float(np.trapezoid(np.exp(values - peak), x)))

    return integrate_log(h1 + common) - integrate_log(h0 + common)


class RobustMetaPass2Tests(unittest.TestCase):
    def test_hand_fixture_matches_likelihood_scores_and_profile_endpoints(self) -> None:
        result = robust().result
        pooled = result.meta_analysis.pooled
        self.assertAlmostEqual(pooled.estimate, 0.2751322305316832, places=10)
        self.assertEqual(pooled.tau_squared, 0.0)
        self.assertAlmostEqual(pooled.statistic, 9.11416675244368, places=8)
        self.assertAlmostEqual(pooled.p_value, 0.002536374634204719, places=10)
        y = np.asarray(ROBUST_ESTIMATES)
        errors = np.asarray(ROBUST_ERRORS)
        best = student_t4_log_likelihood(y, errors, pooled.estimate, pooled.tau_squared)
        for endpoint in (pooled.interval.low, pooled.interval.high):
            likelihood_ratio = 2.0 * (best - golden_profile(y, errors, endpoint))
            self.assertAlmostEqual(likelihood_ratio, 3.841458820694124, places=6)
        d = errors * errors + pooled.tau_squared
        residual = y - pooled.estimate
        lambdas = 5.0 / (4.0 + residual * residual / d)
        mu_score = float(np.sum(lambdas * residual / d))
        tau_score = float(0.5 * np.sum((lambdas * residual * residual - d) / (d * d)))
        self.assertLess(abs(mu_score), 1e-8)
        self.assertLessEqual(tau_score, 1e-8)

    def test_positive_heterogeneity_and_study_count_grid(self) -> None:
        for k in (20, 50, 500):
            index = np.arange(k, dtype=np.float64)
            estimates = 0.25 + 0.4 * np.sin(1.7 * index)
            errors = np.linspace(0.15, 0.35, k)
            analysis = cast(
                RobustMetaAnalysis,
                analyze_ggcoefstats(
                    frame(estimates.tolist(), errors.tolist()),
                    type="robust",
                    stats_labels=False,
                    **COMMON,
                ),
            )
            with self.subTest(k=k):
                self.assertGreater(analysis.result.meta_analysis.pooled.tau_squared, 0)
                self.assertEqual(analysis.result.retained_rows, k)
                self.assertEqual(analysis.result.warnings, ())

    def test_influence_records_downweight_displaced_study_without_deletion(
        self,
    ) -> None:
        result = robust().result
        outlier = result.studies[-1]
        self.assertEqual(outlier.identity.term, "study-10")
        self.assertEqual(
            result.source_order, tuple(item.identity.term for item in result.studies)
        )
        self.assertLess(
            outlier.latent_precision,
            min(item.latent_precision for item in result.studies[:-1]),
        )
        distances = np.asarray([0.0, 1.0, 2.0, 5.0])
        theoretical = 5.0 / (4.0 + distances * distances)
        self.assertTrue(
            all(
                right < left
                for left, right in zip(
                    theoretical.tolist(), theoretical[1:].tolist(), strict=False
                )
            )
        )
        clean_values = [*ROBUST_ESTIMATES[:-1], 0.3]
        clean = cast(
            RobustMetaAnalysis,
            analyze_ggcoefstats(
                frame(clean_values, ROBUST_ERRORS), type="robust", **COMMON
            ),
        ).result.meta_analysis.pooled.estimate
        classical_clean = cast(
            CoefficientAnalysis,
            analyze_ggcoefstats(frame(clean_values, ROBUST_ERRORS), **COMMON),
        ).result.meta_analysis.pooled.estimate
        classical_outlier = cast(
            CoefficientAnalysis,
            analyze_ggcoefstats(frame(ROBUST_ESTIMATES, ROBUST_ERRORS), **COMMON),
        ).result.meta_analysis.pooled.estimate
        self.assertLess(
            abs(result.meta_analysis.pooled.estimate - clean),
            abs(classical_outlier - classical_clean),
        )

    def test_affine_equivariance_permutation_warnings_and_absences(self) -> None:
        base = robust().result
        shifted_scaled = cast(
            RobustMetaAnalysis,
            analyze_ggcoefstats(
                frame(
                    [10.0 + 100.0 * value for value in ROBUST_ESTIMATES],
                    [100.0 * value for value in ROBUST_ERRORS],
                ),
                type="robust",
                null_value=10.0,
                **COMMON,
            ),
        ).result
        self.assertAlmostEqual(
            shifted_scaled.meta_analysis.pooled.estimate,
            10.0 + 100.0 * base.meta_analysis.pooled.estimate,
            places=7,
        )
        self.assertAlmostEqual(
            shifted_scaled.meta_analysis.pooled.tau_squared,
            10_000.0 * base.meta_analysis.pooled.tau_squared,
            places=7,
        )
        permutation = list(reversed(range(10)))
        permuted = cast(
            RobustMetaAnalysis,
            analyze_ggcoefstats(
                frame(
                    [ROBUST_ESTIMATES[index] for index in permutation],
                    [ROBUST_ERRORS[index] for index in permutation],
                ),
                type="robust",
                **COMMON,
            ),
        ).result
        self.assertAlmostEqual(
            permuted.meta_analysis.pooled.estimate,
            base.meta_analysis.pooled.estimate,
            places=10,
        )
        self.assertEqual(base.warnings, ("few_studies_robust_profile_likelihood",))
        self.assertEqual(
            base.meta_analysis.pooled.heterogeneity_absence_reason,
            "not_defined_for_student_t4_working_model",
        )
        self.assertEqual(
            base.meta_analysis.pooled.prediction_absence_reason,
            "robust_meta_prediction_method_not_approved",
        )

    def test_floor_resource_and_mode_failures_are_coded_and_atomic(self) -> None:
        with self.assertRaises(M6CMetaError) as floor:
            analyze_ggcoefstats(
                frame(ROBUST_ESTIMATES[:9], ROBUST_ERRORS[:9]),
                type="robust",
                **COMMON,
            )
        self.assertEqual(
            floor.exception.code, "robust_meta_requires_at_least_10_studies"
        )
        with self.assertRaises(M6CMetaError) as work:
            robust(maximum_work=19_999_999)
        self.assertEqual(work.exception.code, "m6c_meta_work_preflight_failed")
        for maximum in (0, 500_000_001):
            with (
                self.subTest(maximum=maximum),
                self.assertRaises(M6CMetaError) as invalid,
            ):
                robust(maximum_work=maximum)
            self.assertEqual(invalid.exception.code, "m6c_meta_invalid_maximum_work")
        for change in (
            {"credible_level": 0.9},
            {"prior_mean_scale": 1.0},
            {"only_significant": True},
            {"conf_level": 0.7},
            {"maximum_labels": 9},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                robust(**change)

    def test_result_mutations_and_analysis_pairing_fail(self) -> None:
        analysis = robust()
        result = analysis.result
        mutations: tuple[dict[str, object], ...] = (
            {"schema_version": cast(Any, 3)},
            {"mode": cast(Any, "bayes")},
            {"source_order": tuple(reversed(result.source_order))},
            {"retained_rows": 9},
            {"conf_level": 0.7},
            {"only_significant": True},
            {"warnings": ()},
            {"work": replace(result.work, maximum_work=result.work.maximum_work + 1)},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                replace(result, **cast(Any, mutation))
        changed_table = replace(
            analysis.table, estimates=analysis.table.estimates + np.ones(10)
        )
        with self.assertRaises(ValueError):
            RobustMetaAnalysis(changed_table, result)
        with self.assertRaises(ValueError):
            RobustMetaAnalysis(
                replace(analysis.table, terms=tuple(reversed(analysis.table.terms))),
                result,
            )
        with self.assertRaisesRegex(NotImplementedError, "pass 3"):
            render_ggcoefstats(analysis)

    def test_component_invariants_and_schema_round_trip(self) -> None:
        result = robust().result
        start = result.convergence.starts[0]
        start_mutations = (
            {"start": cast(Any, "unknown")},
            {"converged": cast(Any, 1)},
            {"cycles": -1},
            {"scaled_mu": float("nan")},
            {"scaled_tau_squared": -1.0},
            {"successive_cycles": 2},
            {"boundary": not start.boundary},
        )
        for mutation in start_mutations:
            with self.subTest(start=mutation), self.assertRaises(ValueError):
                replace(start, **cast(Any, mutation))
        with self.assertRaises(ValueError):
            replace(result.limits, maximum_studies=0)
        with self.assertRaises(ValueError):
            replace(result.work, actual_work=result.work.reserved_work + 1)
        with self.assertRaises(ValueError):
            replace(result.studies[0].identity, term="")
        with self.assertRaises(ValueError):
            replace(result.convergence, algorithm=cast(Any, "other"))
        with self.assertRaises(ValueError):
            replace(result.convergence, scale=0.0)
        with self.assertRaises(ValueError):
            replace(result.studies[0], standard_error=0.0)
        with self.assertRaises(ValueError):
            replace(result.studies[0], weighted_contribution=0.0)
        with self.assertRaises(ValueError):
            replace(result.meta_analysis.pooled, method=cast(Any, "other"))
        with self.assertRaises(ValueError):
            replace(result.meta_analysis.pooled, tau=1.0)
        with self.assertRaises(ValueError):
            replace(result.meta_analysis, estimand="")
        with self.assertRaises(ValueError):
            replace(result.meta_analysis, dependence=cast(Any, "dependent"))
        changed_study = replace(
            result.studies[0],
            normalized_share=result.studies[0].normalized_share + 0.01,
            weighted_contribution=(result.studies[0].normalized_share + 0.01)
            * result.studies[0].estimate,
        )
        with self.assertRaises(ValueError):
            replace(result, studies=(changed_study, *result.studies[1:]))
        changed_pooled = replace(result.meta_analysis.pooled, estimate=0.28)
        with self.assertRaises(ValueError):
            replace(
                result,
                meta_analysis=replace(result.meta_analysis, pooled=changed_pooled),
            )
        with self.assertRaises(ValueError):
            replace(result, limits=replace(result.limits, maximum_studies=9))
        payload = result.to_dict()
        json.dumps(payload, allow_nan=False)
        schema = json.loads(
            (ROOT / "schemas" / "coefficient-result.schema.json").read_text()
        )
        self.assertEqual(
            set(payload), set(schema["$defs"]["robust_meta_result"]["required"])
        )

    def test_profile_convergence_and_work_faults_are_atomic(self) -> None:
        meter_class = cast(
            Any, import_module("plotsalot.coefficient_meta_analysis")
        )._WorkMeter
        meter = meter_class(1)
        meter.bump()
        with self.assertRaises(M6CMetaError) as exhausted:
            meter.bump()
        self.assertEqual(exhausted.exception.code, "m6c_meta_work_exhausted")
        with (
            patch(
                "plotsalot.coefficient_meta_analysis._brent_root_details",
                return_value=(0.0, SimpleNamespace(converged=False, iterations=0)),
            ),
            self.assertRaises(M6CMetaError) as root,
        ):
            robust()
        self.assertEqual(root.exception.code, "robust_meta_profile_root_failed")


class BayesianMetaPass2Tests(unittest.TestCase):
    def test_direct_quadrature_reference_and_complete_primary_targets(self) -> None:
        result = bayes().result
        primary = result.primary
        independent = independent_log_bf10(
            np.asarray(BAYES_ESTIMATES), np.asarray(BAYES_ERRORS), 1.0, 0.5
        )
        self.assertAlmostEqual(primary.evidence.log_bf10, independent, places=5)
        self.assertAlmostEqual(
            primary.quadrature.h0_log_marginal - primary.quadrature.h1_log_marginal,
            -primary.evidence.log_bf10,
            places=12,
        )
        self.assertAlmostEqual(primary.evidence.log_bf10, -0.7914751790171222, places=9)
        self.assertAlmostEqual(
            primary.population_mean.median, 0.23085025374446558, places=8
        )
        self.assertAlmostEqual(primary.tau.median, 0.16980613318915114, places=8)
        self.assertAlmostEqual(
            primary.true_effect_prediction.median, 0.23205443213866866, places=7
        )
        self.assertEqual(primary.population_mean.probability_at_null, 0.0)
        self.assertEqual(primary.tau.probability_above_null, 1.0)
        self.assertEqual(result.warnings, ("few_studies_prior_sensitive",))
        self.assertLessEqual(primary.quadrature.h1_relative_error, 1e-10)
        self.assertLessEqual(primary.quadrature.h0_relative_error, 1e-10)

    def test_required_prior_record_and_four_sensitivity_fits(self) -> None:
        result = bayes().result
        self.assertEqual(
            tuple(item.label for item in result.sensitivities),
            (
                "mean_scale_half",
                "mean_scale_double",
                "tau_scale_half",
                "tau_scale_double",
            ),
        )
        self.assertEqual(
            tuple(
                (item.prior.mean_scale, item.prior.tau_scale)
                for item in result.sensitivities
            ),
            ((0.5, 0.5), (2.0, 0.5), (1.0, 0.25), (1.0, 1.0)),
        )
        prior = result.primary.prior
        self.assertAlmostEqual(prior.tau_prior_median, 0.33724487509804085)
        self.assertAlmostEqual(prior.tau_prior_95_quantile, 0.979981992270027)
        self.assertAlmostEqual(
            prior.prior_predictive_effect_standard_deviation, 5**0.5 / 2
        )
        self.assertEqual(
            result.work.actual_work,
            sum(
                fit.quadrature.evaluations
                for fit in (result.primary, *result.sensitivities)
            ),
        )

    def test_scale_translation_and_permutation_invariance(self) -> None:
        base = bayes().result
        transformed = cast(
            BayesianMetaAnalysis,
            analyze_ggcoefstats(
                frame(
                    [10.0 + 100.0 * value for value in BAYES_ESTIMATES],
                    [100.0 * value for value in BAYES_ERRORS],
                ),
                type="bayes",
                null_value=10.0,
                prior_mean_scale=100.0,
                prior_tau_scale=50.0,
                **COMMON,
            ),
        ).result
        self.assertAlmostEqual(
            transformed.primary.population_mean.median,
            10.0 + 100.0 * base.primary.population_mean.median,
            places=6,
        )
        self.assertAlmostEqual(
            transformed.primary.tau.median, 100.0 * base.primary.tau.median, places=6
        )
        self.assertAlmostEqual(
            transformed.primary.evidence.log_bf10,
            base.primary.evidence.log_bf10,
            places=8,
        )
        permuted = cast(
            BayesianMetaAnalysis,
            analyze_ggcoefstats(
                frame(
                    list(reversed(BAYES_ESTIMATES)),
                    list(reversed(BAYES_ERRORS)),
                ),
                type="bayes",
                prior_mean_scale=1.0,
                prior_tau_scale=0.5,
                **COMMON,
            ),
        ).result
        self.assertAlmostEqual(
            permuted.primary.population_mean.median,
            base.primary.population_mean.median,
            places=9,
        )
        self.assertAlmostEqual(
            permuted.primary.evidence.log_bf10,
            base.primary.evidence.log_bf10,
            places=9,
        )

    def test_prior_mode_resource_and_renderer_failures(self) -> None:
        for change in (
            {"prior_mean_scale": None},
            {"prior_tau_scale": None},
            {"prior_mean_scale": 0.0},
            {"prior_tau_scale": float("inf")},
            {"conf_level": 0.9},
            {"credible_level": 0.7},
            {"only_significant": True},
            {"maximum_labels": 2},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                bayes(**change)
        with self.assertRaises(M6CMetaError) as work:
            bayes(maximum_work=24_999_999)
        self.assertEqual(work.exception.code, "m6c_meta_work_preflight_failed")
        with self.assertRaisesRegex(NotImplementedError, "pass 3"):
            render_ggcoefstats(bayes())

    def test_result_sensitivity_and_quadrature_mutations_fail(self) -> None:
        analysis = bayes()
        result: BayesianMetaResult = analysis.result
        for mutation in (
            {"schema_version": cast(Any, 2)},
            {"mode": cast(Any, "robust")},
            {"retained_rows": 2},
            {"credible_level": 0.7},
            {"sensitivities": tuple(reversed(result.sensitivities))},
            {"warnings": ()},
        ):
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                replace(result, **cast(Any, mutation))
        with self.assertRaises(ValueError):
            replace(
                result.primary.quadrature,
                posterior_normalization_error=1e-5,
            )
        with self.assertRaises(ValueError):
            replace(result.primary.evidence, display="strong evidence")
        with self.assertRaises(ValueError):
            replace(
                result.primary,
                tau_squared=replace(result.primary.tau_squared, median=1.0),
            )
        changed_table = replace(
            analysis.table, standard_errors=analysis.table.standard_errors * 2.0
        )
        with self.assertRaises(ValueError):
            BayesianMetaAnalysis(changed_table, result)
        with self.assertRaises(ValueError):
            BayesianMetaAnalysis(
                replace(analysis.table, terms=tuple(reversed(analysis.table.terms))),
                result,
            )

    def test_component_invariants_and_schema_round_trip(self) -> None:
        result = bayes().result
        primary = result.primary
        with self.assertRaises(ValueError):
            replace(primary.prior, mean_scale=0.0)
        with self.assertRaises(ValueError):
            replace(primary.quadrature, algorithm=cast(Any, "other"))
        with self.assertRaises(ValueError):
            replace(primary, label=cast(Any, "other"))
        with self.assertRaises(ValueError):
            replace(
                primary,
                population_mean=replace(
                    primary.population_mean, target=cast(Any, "coefficient")
                ),
            )
        with self.assertRaises(ValueError):
            replace(result.studies[0], standard_error=0.0)
        with self.assertRaises(ValueError):
            replace(result, estimand="")
        changed_interval = replace(primary.population_mean.interval, level=0.9)
        changed_summary = replace(primary.population_mean, interval=changed_interval)
        changed_primary = replace(primary, population_mean=changed_summary)
        with self.assertRaises(ValueError):
            replace(result, primary=changed_primary)
        sensitivity = result.sensitivities[0]
        changed_prior = replace(
            sensitivity.prior, mean_scale=sensitivity.prior.mean_scale + 0.1
        )
        with self.assertRaises(ValueError):
            replace(
                result,
                sensitivities=(
                    replace(sensitivity, prior=changed_prior),
                    *result.sensitivities[1:],
                ),
            )
        with self.assertRaises(ValueError):
            replace(result, limits=replace(result.limits, maximum_studies=2))
        with self.assertRaises(ValueError):
            replace(
                result,
                work=replace(result.work, actual_work=result.work.actual_work - 1),
            )
        payload = result.to_dict()
        json.dumps(payload, allow_nan=False)
        schema = json.loads(
            (ROOT / "schemas" / "coefficient-result.schema.json").read_text()
        )
        self.assertEqual(
            set(payload), set(schema["$defs"]["bayesian_meta_result"]["required"])
        )

    def test_quadrature_faults_are_coded_and_atomic(self) -> None:
        with (
            patch(
                "plotsalot.coefficient_meta_analysis._minimize_scalar",
                return_value=SimpleNamespace(success=False, fun=float("nan")),
            ),
            self.assertRaises(M6CMetaError) as peak,
        ):
            bayes()
        self.assertEqual(peak.exception.code, "bayesian_meta_quadrature_peak_failed")
        with (
            patch(
                "plotsalot.coefficient_meta_analysis._quad",
                return_value=(1.0, 1.0),
            ),
            self.assertRaises(M6CMetaError) as tolerance,
        ):
            bayes()
        self.assertEqual(
            tolerance.exception.code, "bayesian_meta_quadrature_tolerance_failed"
        )
        with (
            patch(
                "plotsalot.coefficient_meta_analysis._quad",
                side_effect=ValueError("injected quadrature failure"),
            ),
            self.assertRaises(M6CMetaError) as failed,
        ):
            bayes()
        self.assertEqual(failed.exception.code, "bayesian_meta_quadrature_failed")

    def test_boundary_dominant_and_500_study_stress(self) -> None:
        fixtures = (
            ([0.2] * 5, [0.2] * 5),
            ([0.2, 0.4, 0.1, 0.3, -0.1], [1e-5, 0.25, 0.3, 0.2, 0.35]),
            (
                (0.2 + 0.1 * np.sin(np.arange(500))).tolist(),
                np.linspace(0.15, 0.35, 500).tolist(),
            ),
        )
        for estimates, errors in fixtures:
            result = cast(
                BayesianMetaAnalysis,
                analyze_ggcoefstats(
                    frame(estimates, errors),
                    type="bayes",
                    prior_mean_scale=1.0,
                    prior_tau_scale=0.5,
                    stats_labels=False,
                    **COMMON,
                ),
            ).result
            with self.subTest(k=len(estimates)):
                self.assertTrue(np.isfinite(result.primary.evidence.log_bf10))
                self.assertEqual(result.retained_rows, len(estimates))
                self.assertLessEqual(result.work.actual_work, result.work.maximum_work)


class M6CPass2EvidenceTests(unittest.TestCase):
    def test_first_held_out_result_is_retained_without_threshold_masking(self) -> None:
        payload = json.loads(
            (ROOT / "docs" / "evidence" / "m6c-pass2-calibration.json").read_text()
        )
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["status"], "held_out_finding")
        self.assertEqual(payload["cases_per_cell"], 2_000)
        self.assertEqual([item["k"] for item in payload["robust"]], [10, 20, 50, 500])
        self.assertEqual(
            [item["wilson_contains_0_95"] for item in payload["robust"]],
            [False, True, True, True],
        )
        self.assertTrue(
            all(
                item["robust_not_worse_under_contamination"]
                for item in payload["robust"]
            )
        )
        self.assertTrue(payload["bayesian"]["mu_passes_dkw_bound"])
        self.assertTrue(payload["bayesian"]["tau_passes_dkw_bound"])


if __name__ == "__main__":
    unittest.main()
