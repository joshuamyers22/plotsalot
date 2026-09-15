from __future__ import annotations

import json
import unittest
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from typing import Any, cast

import polars as pl

from plotsalot import (
    PosteriorCoefficientProvenanceResult,
    PosteriorCoefficientSummaryResult,
    PosteriorCoefficientSummaryTable,
    PosteriorCoefficientTableResult,
    PosteriorCoefficientTermResult,
    ReportedCoefficientAnalysis,
    RobustCoefficientProvenanceResult,
    RobustCoefficientSummaryTable,
    RobustCoefficientTableResult,
    RobustCoefficientTermResult,
    analyze_ggcoefstats,
    ggcoefstats,
    render_ggcoefstats,
    select_posterior_coefficient_summaries,
    select_robust_coefficient_summaries,
)
from plotsalot.result import IntervalResult

ROOT = Path(__file__).resolve().parents[1]
V1_CANONICAL_SHA256 = "8b2766c45d306baaa27a8fed55155af3b17760c140ea294d31cf56ba6c954170"


def robust_frame() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "term": ["Intercept", "dose", "age"],
            "response": ["score", "score", "score"],
            "component": ["mean", "mean", "mean"],
            "estimate": [2.0, 0.8, -0.2],
            "conf_low": [1.5, 0.4, -0.6],
            "conf_high": [2.5, 1.2, 0.1],
            "is_intercept": [True, False, False],
            "ignored_note": ["a", "b", "c"],
        }
    )


def posterior_frame() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "term": ["Intercept", "dose", "age"],
            "group": ["all", "all", "all"],
            "posterior_median": [2.0, 0.75, -0.15],
            "credible_low": [1.4, 0.3, -0.5],
            "credible_high": [2.6, 1.1, 0.2],
            "probability_above_null": [1.0, 0.98, 0.25],
            "probability_below_null": [0.0, 0.02, 0.75],
            "probability_at_null": [0.0, 0.0, 0.0],
            "is_intercept": [True, False, False],
        }
    )


COMMON: dict[str, Any] = {
    "estimate_label": "Coefficient",
    "effect_scale": "additive score",
    "effect_direction": "positive is higher",
    "effect_units": "score units",
}


def analyze_robust(**changes: object) -> ReportedCoefficientAnalysis:
    options: dict[str, object] = {
        **COMMON,
        "type": "robust",
        "robust_method": "  Huber   M-estimator  ",
        "robust_tuning": "c=1.345",
        "interval_method": "sandwich Wald",
    }
    options.update(changes)
    return cast(
        ReportedCoefficientAnalysis,
        analyze_ggcoefstats(robust_frame(), **cast(Any, options)),
    )


def analyze_posterior(**changes: object) -> ReportedCoefficientAnalysis:
    options: dict[str, object] = {
        **COMMON,
        "type": "bayes",
        "posterior_model": "normal linear model",
        "likelihood": "Gaussian likelihood",
        "prior_description": "proper weakly informative normal priors",
        "computation_method": "deterministic quadrature",
    }
    options.update(changes)
    return cast(
        ReportedCoefficientAnalysis,
        analyze_ggcoefstats(posterior_frame(), **cast(Any, options)),
    )


class M6CCoefficientBoundaryTests(unittest.TestCase):
    def test_robust_profile_is_owned_strict_and_ignores_unknown_columns(self) -> None:
        table = select_robust_coefficient_summaries(robust_frame())
        self.assertIsInstance(table, RobustCoefficientSummaryTable)
        self.assertEqual(table.profile, "robust_interval")
        self.assertEqual(table.identity_columns, ("response", "component"))
        self.assertEqual(table.keys[1], ("score", "mean", "dose"))
        self.assertFalse(table.estimates.flags.writeable)
        with self.assertRaises(ValueError):
            table.estimates[0] = 99.0

    def test_posterior_profile_is_owned_and_accepts_partition_boundary(self) -> None:
        frame = posterior_frame().with_columns(
            pl.lit(0.5000000000005).alias("probability_above_null"),
            pl.lit(0.5).alias("probability_below_null"),
            pl.lit(0.0).alias("probability_at_null"),
        )
        table = select_posterior_coefficient_summaries(frame)
        self.assertIsInstance(table, PosteriorCoefficientSummaryTable)
        self.assertFalse(table.posterior_medians.flags.writeable)

    def test_profile_requires_polars_complete_rows_and_numeric_values(self) -> None:
        with self.assertRaises(TypeError):
            select_robust_coefficient_summaries({"term": ["x"]})
        with self.assertRaisesRegex(ValueError, "missing required"):
            select_robust_coefficient_summaries(robust_frame().drop("conf_high"))
        with self.assertRaisesRegex(ValueError, "null"):
            select_robust_coefficient_summaries(
                robust_frame().with_columns(
                    pl.when(pl.col("term") == "dose")
                    .then(None)
                    .otherwise(pl.col("estimate"))
                    .alias("estimate")
                )
            )
        with self.assertRaises(TypeError):
            select_posterior_coefficient_summaries(
                posterior_frame().with_columns(
                    pl.col("posterior_median").cast(pl.String)
                )
            )

    def test_mixed_and_reserved_fields_are_rejected(self) -> None:
        for column, value in (
            ("standard_error", 0.1),
            ("p_value", 0.04),
            ("posterior_median", 0.2),
            ("credible_low", -0.1),
            ("bf10", 3.0),
            ("model", "fitted object reference"),
        ):
            with (
                self.subTest(profile="robust", column=column),
                self.assertRaisesRegex(ValueError, "reserved"),
            ):
                select_robust_coefficient_summaries(
                    robust_frame().with_columns(pl.lit(value).alias(column))
                )
        for column, value in (
            ("estimate", 0.2),
            ("conf_low", -0.1),
            ("standard_error", 0.1),
            ("statistic", 2.0),
            ("p_value", 0.04),
            ("draws", "posterior draw reference"),
        ):
            with (
                self.subTest(profile="posterior", column=column),
                self.assertRaisesRegex(ValueError, "reserved"),
            ):
                select_posterior_coefficient_summaries(
                    posterior_frame().with_columns(pl.lit(value).alias(column))
                )

    def test_interval_and_probability_invariants_fail_atomically(self) -> None:
        for column, value in (
            ("conf_low", 2.1),
            ("conf_high", 1.9),
            ("estimate", float("inf")),
        ):
            with self.subTest(column=column), self.assertRaises(ValueError):
                select_robust_coefficient_summaries(
                    robust_frame().with_columns(pl.lit(value).alias(column))
                )
        with self.assertRaisesRegex(ValueError, "partition"):
            select_posterior_coefficient_summaries(
                posterior_frame().with_columns(
                    pl.lit(0.500000000002).alias("probability_above_null"),
                    pl.lit(0.5).alias("probability_below_null"),
                    pl.lit(0.0).alias("probability_at_null"),
                )
            )
        with self.assertRaisesRegex(ValueError, "partition"):
            select_posterior_coefficient_summaries(
                posterior_frame().with_columns(
                    pl.lit(-0.01).alias("probability_at_null")
                )
            )

    def test_identity_intercept_and_row_limits_remain_strict(self) -> None:
        duplicate = robust_frame().with_columns(pl.lit("dose").alias("term"))
        with self.assertRaisesRegex(ValueError, "unique"):
            select_robust_coefficient_summaries(duplicate)
        with self.assertRaises(TypeError):
            select_robust_coefficient_summaries(
                robust_frame().with_columns(pl.col("is_intercept").cast(pl.Int64))
            )
        with self.assertRaises(ValueError):
            select_posterior_coefficient_summaries(
                posterior_frame(), maximum_coefficients=2
            )

    def test_table_value_objects_reject_all_structural_mutations(self) -> None:
        robust = select_robust_coefficient_summaries(robust_frame())
        posterior = select_posterior_coefficient_summaries(posterior_frame())
        mutations: tuple[tuple[object, dict[str, object]], ...] = (
            (robust, {"terms": ()}),
            (robust, {"identity_columns": ("component", "response")}),
            (robust, {"identities": robust.identities[:-1]}),
            (robust, {"is_intercepts": robust.is_intercepts[:-1]}),
            (robust, {"estimates": robust.estimates[:-1]}),
            (robust, {"profile": "interval"}),
            (posterior, {"posterior_medians": posterior.posterior_medians[:-1]}),
            (posterior, {"credible_low": posterior.credible_high}),
            (posterior, {"profile": "credible"}),
        )
        for value, mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                replace(value, **cast(Any, mutation))
        with self.assertRaises(ValueError):
            select_robust_coefficient_summaries(
                robust_frame(), maximum_coefficients=cast(Any, True)
            )
        no_marker = select_robust_coefficient_summaries(
            robust_frame().drop("is_intercept")
        )
        self.assertEqual(no_marker.is_intercepts, (False, False, False))
        with self.assertRaises(TypeError):
            select_robust_coefficient_summaries(
                robust_frame().with_columns(pl.col("term").cast(pl.Categorical))
            )


class M6CCoefficientAnalysisTests(unittest.TestCase):
    def test_robust_dispatch_normalizes_provenance_and_preserves_audit(self) -> None:
        analysis = analyze_robust(exclude_intercept=True, sort="descending")
        result = cast(RobustCoefficientTableResult, analysis.result)
        self.assertEqual((result.schema_version, result.mode), (2, "robust"))
        self.assertEqual(result.provenance.robust_method, "Huber M-estimator")
        self.assertEqual(result.provenance.source, "caller_reported_unverified")
        self.assertEqual([term.identity.term for term in result.terms], ["dose", "age"])
        self.assertEqual([term.source_position for term in result.terms], [1, 2])
        self.assertEqual(
            result.source_order, tuple(term.identity for term in result.terms)
        )
        self.assertEqual(result.excluded_intercepts[0].term, "Intercept")
        self.assertEqual(result.interval_kind, "confidence")
        self.assertNotIn("alpha", result.to_dict())

    def test_posterior_dispatch_sorts_points_and_retains_probabilities(self) -> None:
        analysis = analyze_posterior(exclude_intercept=True, sort="ascending")
        result = cast(PosteriorCoefficientTableResult, analysis.result)
        self.assertEqual((result.schema_version, result.mode), (3, "bayes"))
        self.assertEqual([term.identity.term for term in result.terms], ["age", "dose"])
        self.assertEqual(result.source_order[0].term, "dose")
        summary = result.terms[0].summary
        self.assertEqual(summary.probability_below_null, 0.75)
        self.assertEqual(
            summary.interval.method, "caller_reported_equal_tail_credible_interval"
        )
        self.assertEqual(result.interval_kind, "equal_tail_credible")
        self.assertNotIn("alpha", result.to_dict())
        self.assertNotIn("bf10", json.dumps(result.to_dict()))

    def test_source_permutation_changes_source_not_semantic_sort(self) -> None:
        original = cast(
            RobustCoefficientTableResult,
            analyze_robust(sort="ascending", exclude_intercept=True).result,
        )
        permuted_frame = robust_frame().reverse()
        permuted_analysis = cast(
            ReportedCoefficientAnalysis,
            analyze_ggcoefstats(
                permuted_frame,
                type="robust",
                robust_method="Huber M-estimator",
                robust_tuning="c=1.345",
                interval_method="sandwich Wald",
                sort="ascending",
                exclude_intercept=True,
                **COMMON,
            ),
        )
        permuted = cast(RobustCoefficientTableResult, permuted_analysis.result)
        self.assertEqual(
            [term.identity.term for term in original.terms],
            [term.identity.term for term in permuted.terms],
        )
        self.assertNotEqual(original.source_order, permuted.source_order)

    def test_provenance_and_interval_level_validation(self) -> None:
        for change in (
            {"robust_method": ""},
            {"robust_tuning": "bad\nvalue"},
            {"interval_method": "x" * 201},
            {"conf_level": 0.799},
            {"conf_level": 0.991},
            {"credible_level": 0.9},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                analyze_robust(**change)
        for change in (
            {"posterior_model": ""},
            {"likelihood": "bad\u0000value"},
            {"prior_description": "x" * 201},
            {"credible_level": 0.75},
            {"conf_level": 0.9},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                analyze_posterior(**change)

    def test_mode_specific_options_and_unsupported_surfaces_fail(self) -> None:
        with self.assertRaisesRegex(ValueError, "Bayesian provenance"):
            analyze_robust(posterior_model="wrong mode")
        with self.assertRaisesRegex(ValueError, "robust provenance"):
            analyze_posterior(robust_method="wrong mode")
        with self.assertRaisesRegex(ValueError, "only_significant"):
            analyze_robust(only_significant=True)
        with self.assertRaisesRegex(ValueError, "alpha"):
            analyze_posterior(alpha=0.1)
        robust_analysis = analyze_robust()
        rendered = render_ggcoefstats(robust_analysis)
        self.addCleanup(rendered.figure.clear)
        self.assertIs(rendered.result, robust_analysis.result)
        public = ggcoefstats(
            robust_frame(),
            type="robust",
            robust_method="Huber M-estimator",
            robust_tuning="c=1.345",
            interval_method="sandwich Wald",
            **COMMON,
        )
        self.addCleanup(public.figure.clear)
        self.assertIsInstance(public.result, RobustCoefficientTableResult)
        with self.assertRaises(TypeError):
            analyze_ggcoefstats(
                object(),
                type="robust",
                robust_method="Huber",
                robust_tuning="c=1",
                interval_method="Wald",
                **COMMON,
            )

    def test_mode_and_declaration_validation(self) -> None:
        with self.assertRaisesRegex(ValueError, "type must"):
            analyze_ggcoefstats(robust_frame(), type=cast(Any, "automatic"), **COMMON)
        with self.assertRaisesRegex(ValueError, "reported-summary"):
            analyze_ggcoefstats(
                robust_frame(),
                robust_method="Huber",
                stats_labels=False,
                **COMMON,
            )
        with self.assertRaises(ValueError):
            analyze_robust(effect_units="   ")
        with self.assertRaises(ValueError):
            analyze_posterior(null_value=float("nan"))

    def test_result_constructors_reject_identity_and_semantic_mutations(self) -> None:
        robust = cast(RobustCoefficientTableResult, analyze_robust().result)
        posterior = cast(PosteriorCoefficientTableResult, analyze_posterior().result)
        for mutation in (
            {"schema_version": cast(Any, 3)},
            {"mode": cast(Any, "bayes")},
            {"interval_kind": cast(Any, "credible")},
            {"source_order": tuple(reversed(robust.source_order))},
            {"retained_rows": 2},
            {"only_significant": True},
        ):
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                replace(robust, **cast(Any, mutation))
        with self.assertRaises(ValueError):
            replace(
                robust,
                provenance=replace(robust.provenance, source=cast(Any, "verified")),
            )
        with self.assertRaises(ValueError):
            replace(
                robust,
                terms=(
                    replace(
                        robust.terms[0],
                        interval=replace(robust.terms[0].interval, level=0.9),
                    ),
                    *robust.terms[1:],
                ),
            )
        with self.assertRaises(ValueError):
            replace(robust, provenance=posterior.provenance)
        with self.assertRaises(ValueError):
            replace(posterior, credible_level=0.7)
        with self.assertRaises(ValueError):
            replace(posterior, provenance=robust.provenance)
        with self.assertRaises(ValueError):
            replace(
                posterior,
                terms=(
                    replace(
                        posterior.terms[0],
                        summary=replace(
                            posterior.terms[0].summary,
                            probability_at_null=0.1,
                        ),
                    ),
                    *posterior.terms[1:],
                ),
            )

    def test_provenance_and_summary_value_objects_reject_mutation(self) -> None:
        with self.assertRaises(ValueError):
            RobustCoefficientProvenanceResult(" Huber", "c=1", "Wald")
        with self.assertRaises(ValueError):
            PosteriorCoefficientProvenanceResult(
                "model", "likelihood", "prior", "bad\nmethod"
            )
        posterior = cast(PosteriorCoefficientTableResult, analyze_posterior().result)
        summary: PosteriorCoefficientSummaryResult = posterior.terms[0].summary
        with self.assertRaises(ValueError):
            replace(summary, probability_above_null=0.5)

    def test_term_and_summary_objects_reject_contradictions(self) -> None:
        robust = cast(RobustCoefficientTableResult, analyze_robust().result)
        posterior = cast(PosteriorCoefficientTableResult, analyze_posterior().result)
        robust_term: RobustCoefficientTermResult = robust.terms[0]
        posterior_term: PosteriorCoefficientTermResult = posterior.terms[0]
        for mutation in (
            {"is_intercept": cast(Any, 1)},
            {"source_position": -1},
            {"display_position": -1},
            {"estimate": float("inf")},
            {"interval": IntervalResult("coefficient", "wrong_method", 0.95, 1.5, 2.5)},
        ):
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                replace(robust_term, **cast(Any, mutation))
        for mutation in (
            {"median": float("nan")},
            {"null_value": float("inf")},
            {
                "interval": IntervalResult(
                    "wrong_target",
                    "caller_reported_equal_tail_credible_interval",
                    0.95,
                    1.4,
                    2.6,
                )
            },
            {"probability_above_null": -0.1},
            {"probability_at_null": 0.1},
        ):
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                replace(posterior_term.summary, **cast(Any, mutation))
        with self.assertRaises(ValueError):
            replace(posterior_term, source_position=-1)

    def test_result_common_reconciliation_rejects_adversarial_mutations(self) -> None:
        robust = cast(RobustCoefficientTableResult, analyze_robust().result)
        bad_display_term = replace(robust.terms[0], display_position=1)
        bad_source_term = replace(robust.terms[0], source_position=1)
        bad_identity_term = replace(robust.terms[0], identity=robust.terms[1].identity)
        mutations: tuple[dict[str, object], ...] = (
            {"identity_columns": ("group", "response")},
            {"effect_units": ""},
            {"null_value": float("inf")},
            {"input_rows": cast(Any, 3.0)},
            {"input_rows": 4},
            {"display_order": robust.display_order[:-1]},
            {"source_order": (*robust.source_order[:-1], robust.source_order[0])},
            {"terms": (bad_display_term, *robust.terms[1:])},
            {"terms": (bad_source_term, *robust.terms[1:])},
            {"terms": (bad_identity_term, *robust.terms[1:])},
            {"conf_level": float("nan")},
            {"stats_labels": cast(Any, 1)},
            {"sort": cast(Any, "random")},
            {"limits": replace(robust.limits, maximum_rendered_points=1)},
            {"limits": replace(robust.limits, maximum_labels=1)},
            {"warnings": ("",)},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                replace(robust, **cast(Any, mutation))

    def test_analysis_pairing_and_resource_preflight_rejects_mismatch(self) -> None:
        robust_analysis = analyze_robust()
        posterior_analysis = analyze_posterior()
        with self.assertRaises(ValueError):
            ReportedCoefficientAnalysis(
                robust_analysis.table, posterior_analysis.result
            )
        robust = cast(RobustCoefficientTableResult, robust_analysis.result)
        changed_terms = (
            replace(robust.terms[0], estimate=1.9),
            *robust.terms[1:],
        )
        changed_result = replace(robust, terms=changed_terms)
        with self.assertRaisesRegex(ValueError, "points"):
            ReportedCoefficientAnalysis(robust_analysis.table, changed_result)
        for change in (
            {"stats_labels": cast(Any, 1)},
            {"sort": "random"},
            {"maximum_rendered_points": 2},
            {"maximum_labels": 2},
            {"maximum_coefficients": 0},
        ):
            with (
                self.subTest(change=change),
                self.assertRaises((TypeError, ValueError)),
            ):
                analyze_robust(**change)
        intercept_only = robust_frame().head(1)
        with self.assertRaisesRegex(ValueError, "removed every"):
            analyze_ggcoefstats(
                intercept_only,
                type="robust",
                robust_method="Huber",
                robust_tuning="c=1",
                interval_method="Wald",
                exclude_intercept=True,
                **COMMON,
            )

    def test_json_round_trip_and_schema_discriminators(self) -> None:
        schema = json.loads(
            (ROOT / "schemas" / "coefficient-result.schema.json").read_text()
        )
        refs = {item["$ref"] for item in schema["oneOf"]}
        self.assertIn("#/$defs/robust_table_result", refs)
        self.assertIn("#/$defs/posterior_table_result", refs)
        for analysis, definition in (
            (analyze_robust(), "robust_table_result"),
            (analyze_posterior(), "posterior_table_result"),
        ):
            payload = analysis.result.to_dict()
            encoded = json.dumps(
                payload, sort_keys=True, separators=(",", ":"), allow_nan=False
            )
            self.assertEqual(json.loads(encoded), json.loads(json.dumps(payload)))
            required = set(schema["$defs"][definition]["required"])
            self.assertEqual(required, set(payload))

    def test_classical_v1_serialization_is_byte_stable(self) -> None:
        result = analyze_ggcoefstats(
            pl.DataFrame({"term": ["x"], "estimate": [1.25]}),
            estimate_label="Estimate",
            effect_scale="additive",
            effect_direction="higher is positive",
            effect_units="units",
            stats_labels=False,
        ).result
        encoded = json.dumps(
            result.to_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
        self.assertEqual(sha256(encoded).hexdigest(), V1_CANONICAL_SHA256)


if __name__ == "__main__":
    unittest.main()
