from __future__ import annotations

import json
import unittest
import warnings
from dataclasses import replace
from importlib import import_module
from pathlib import Path
from typing import Any, TypedDict, cast
from unittest.mock import patch

import numpy as np
import polars as pl

from plotsalot import (
    CoefficientTableResult,
    TableCoefficientAnalysis,
    analyze_ggcoefstats,
    combine_plots,
    extract_stats,
    ggcoefstats,
    render_ggcoefstats,
    select_coefficients,
)
from plotsalot.coefficient_result import (
    CoefficientModelSummaryResult,
    CoefficientTableResourceLimits,
    ReportedCoefficientInferenceResult,
)
from plotsalot.result import IntervalResult

sm = cast(Any, import_module("statsmodels.api"))


class _Declarations(TypedDict):
    estimate_label: str
    effect_scale: str
    effect_direction: str
    effect_units: str


def _declarations() -> _Declarations:
    return {
        "estimate_label": "regression coefficient",
        "effect_scale": "linear predictor",
        "effect_direction": "positive is higher",
        "effect_units": "outcome units",
    }


def _full_z() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "response": ["y", "y", "y"],
            "group": ["all", "all", "all"],
            "term": ["constant", "x", "z"],
            "estimate": [1.0, -0.5, 0.25],
            "conf_low": [0.5, -0.9, -0.1],
            "conf_high": [1.5, -0.1, 0.6],
            "standard_error": [0.25, 0.2, 0.18],
            "statistic_kind": ["z", "z", "z"],
            "statistic": [4.0, -2.5, 1.39],
            "p_value": [0.0001, 0.012, 0.164],
            "is_intercept": [True, False, False],
            "ignored": [object(), object(), object()],
        }
    )


class CoefficientTableBoundaryTests(unittest.TestCase):
    def test_all_four_profiles_are_resolved_and_arrays_are_owned(self) -> None:
        estimate = pl.DataFrame({"term": ["a", "b"], "estimate": [1.0, 2.0]})
        interval = estimate.with_columns(
            pl.Series("conf_low", [0.5, 1.5]),
            pl.Series("conf_high", [1.5, 2.5]),
        )
        full_z = _full_z()
        full_t = full_z.with_columns(
            pl.lit("t").alias("statistic_kind"), pl.lit(12.0).alias("df")
        )

        tables = tuple(map(select_coefficients, (estimate, interval, full_z, full_t)))
        self.assertEqual(
            tuple(table.profile for table in tables),
            ("estimate_only", "interval", "full_z", "full_t"),
        )
        self.assertFalse(tables[0].estimates.flags.writeable)
        self.assertFalse(
            tables[2].p_values.flags.writeable
            if tables[2].p_values is not None
            else True
        )
        with self.assertRaises(ValueError):
            tables[0].estimates[0] = 9.0

    def test_structured_identity_allows_repeated_terms_but_rejects_duplicate_keys(
        self,
    ) -> None:
        valid = pl.DataFrame(
            {
                "response": ["y1", "y2"],
                "term": ["x", "x"],
                "estimate": [1.0, 2.0],
            }
        )
        table = select_coefficients(valid)
        self.assertEqual(table.keys, (("y1", "x"), ("y2", "x")))
        with self.assertRaises(ValueError):
            select_coefficients(valid.with_columns(pl.lit("y1").alias("response")))

    def test_invalid_or_partial_profiles_fail_without_silent_inference(self) -> None:
        base = pl.DataFrame({"term": ["a"], "estimate": [1.0]})
        cases = (
            lambda: select_coefficients(object()),
            lambda: select_coefficients(base.drop("term")),
            lambda: select_coefficients(base.with_columns(pl.lit(None).alias("term"))),
            lambda: select_coefficients(base.with_columns(pl.lit(1).alias("term"))),
            lambda: select_coefficients(
                base.with_columns(pl.lit(float("inf")).alias("estimate"))
            ),
            lambda: select_coefficients(
                base.with_columns(pl.lit(0.1).alias("standard_error"))
            ),
            lambda: select_coefficients(
                base.with_columns(
                    pl.lit(2.0).alias("conf_low"), pl.lit(3.0).alias("conf_high")
                )
            ),
            lambda: select_coefficients(
                _full_z().with_columns(pl.lit(0.0).alias("standard_error"))
            ),
            lambda: select_coefficients(
                _full_z().with_columns(pl.lit(2.0).alias("p_value"))
            ),
            lambda: select_coefficients(
                _full_z().with_columns(pl.lit("t").alias("statistic_kind"))
            ),
            lambda: select_coefficients(base, maximum_coefficients=0),
            lambda: select_coefficients(base, maximum_coefficients=1_001),
        )
        for operation in cases:
            with (
                self.subTest(operation=operation),
                self.assertRaises((TypeError, ValueError)),
            ):
                operation()


class CoefficientAnalysisAndRenderTests(unittest.TestCase):
    def test_selection_sorting_labels_and_structured_identity_are_retained(
        self,
    ) -> None:
        analysis = analyze_ggcoefstats(
            _full_z(),
            **_declarations(),
            exclude_intercept=True,
            sort="ascending",
            only_significant=True,
        )
        self.assertIsInstance(analysis, TableCoefficientAnalysis)
        result = analysis.result
        self.assertEqual(result.inference_profile, "full_z")
        self.assertEqual(tuple(term.identity.term for term in result.terms), ("x", "z"))
        self.assertEqual(tuple(term.source_position for term in result.terms), (1, 2))
        self.assertEqual(len(result.excluded_intercepts), 1)
        self.assertEqual(result.source_order[0].term, "x")
        self.assertEqual(result.terms[0].identity.key, ("y", "all", "x"))

    def test_estimate_and_interval_profiles_require_labels_off(self) -> None:
        estimate = pl.DataFrame({"term": ["a", "b"], "estimate": [1.0, 2.0]})
        with self.assertRaises(ValueError):
            analyze_ggcoefstats(estimate, **_declarations())
        result = analyze_ggcoefstats(
            estimate, **_declarations(), stats_labels=False
        ).result
        self.assertTrue(all(term.inference is None for term in result.terms))

        interval = estimate.with_columns(
            pl.Series("conf_low", [0.5, 1.5]),
            pl.Series("conf_high", [1.5, 2.5]),
        )
        interval_result = analyze_ggcoefstats(
            interval, **_declarations(), stats_labels=False
        ).result
        self.assertTrue(
            all(term.inference is not None for term in interval_result.terms)
        )
        for analysis in (
            analyze_ggcoefstats(estimate, **_declarations(), stats_labels=False),
            analyze_ggcoefstats(interval, **_declarations(), stats_labels=False),
        ):
            plot = render_ggcoefstats(
                analysis, results_subtitle=False, show_intervals=False
            )
            self.addCleanup(plot.figure.clear)

    def test_fitted_ols_t_and_hc3_z_profiles_snapshot_public_results(self) -> None:
        x = sm.add_constant(np.arange(10.0))
        y = np.array([0.1, 1.0, 2.1, 2.9, 4.2, 5.1, 5.8, 7.2, 7.9, 9.1])
        fitted_t = sm.OLS(y, x).fit()
        fitted_z = sm.OLS(y, x).fit(cov_type="HC3", use_t=False)

        t_result = analyze_ggcoefstats(fitted_t, **_declarations()).result
        z_result = analyze_ggcoefstats(fitted_z, **_declarations()).result
        self.assertEqual(t_result.inference_profile, "full_t")
        self.assertEqual(z_result.inference_profile, "full_z")
        self.assertEqual(
            t_result.model_summary.covariance_type if t_result.model_summary else None,
            "nonrobust",
        )
        self.assertEqual(
            z_result.model_summary.covariance_type if z_result.model_summary else None,
            "HC3",
        )
        np.testing.assert_allclose(
            [term.estimate for term in t_result.terms], fitted_t.params, rtol=0, atol=0
        )
        self.assertEqual(
            t_result.terms[0].inference.df if t_result.terms[0].inference else None,
            fitted_t.df_resid,
        )
        model_plot = render_ggcoefstats(
            analyze_ggcoefstats(fitted_t, **_declarations())
        )
        self.addCleanup(model_plot.figure.clear)
        self.assertIn("AIC", model_plot.caption)

        no_constant = sm.OLS(y, np.arange(1.0, 11.0)[:, None]).fit()
        no_constant_result = analyze_ggcoefstats(
            no_constant, **_declarations(), exclude_intercept=True
        ).result
        self.assertFalse(any(term.is_intercept for term in no_constant_result.terms))

    def test_adapter_rejects_unsupported_ambiguous_or_rank_deficient_models(
        self,
    ) -> None:
        x = cast(
            np.ndarray[Any, np.dtype[np.float64]],
            sm.add_constant(np.arange(6.0)),
        )
        y = np.arange(6.0) + np.array([0.0, 0.1, -0.1, 0.2, -0.2, 0.1])
        rank_deficient = np.array(
            [[1.0, float(index), float(index)] for index in range(6)]
        )
        ols = sm.OLS(y, x).fit()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            deficient_fit = sm.OLS(y, rank_deficient).fit()
            saturated_fit = sm.OLS([1.0, 2.0], np.eye(2)).fit()
        cases = (
            lambda: analyze_ggcoefstats(ols._results, **_declarations()),
            lambda: analyze_ggcoefstats(sm.WLS(y, x).fit(), **_declarations()),
            lambda: analyze_ggcoefstats(
                sm.OLS(y, x).fit(cov_type="HC0"), **_declarations()
            ),
            lambda: analyze_ggcoefstats(deficient_fit, **_declarations()),
            lambda: analyze_ggcoefstats(ols, **_declarations(), null_value=1.0),
        )
        for operation in cases:
            with (
                self.subTest(operation=operation),
                self.assertRaises((TypeError, ValueError)),
            ):
                operation()
        with warnings.catch_warnings(), self.assertRaises(ValueError):
            warnings.simplefilter("ignore")
            analyze_ggcoefstats(saturated_fit, **_declarations())

    def test_adapter_rejects_corrupted_public_fields(self) -> None:
        x = cast(
            np.ndarray[Any, np.dtype[np.float64]],
            sm.add_constant(np.arange(8.0)),
        )
        y = np.arange(8.0) + np.sin(np.arange(8.0)) * 0.1
        fitted = sm.OLS(y, x).fit()

        corruptions: tuple[tuple[object, str, object], ...] = (
            (fitted, "params", ["bad", 1.0]),
            (fitted, "params", [1.0]),
            (fitted, "bse", [0.0, 1.0]),
            (fitted, "pvalues", [2.0, 0.5]),
            (fitted, "cov_type", "HC0"),
            (fitted, "use_t", 1),
            (fitted, "nobs", 1.5),
            (fitted, "df_resid", 0.0),
            (fitted.model, "rank", 1),
            (fitted.model, "k_constant", 2),
            (fitted.model.data, "const_idx", 9),
            (fitted, "aic", float("nan")),
        )
        for target, attribute, value in corruptions:
            with (
                self.subTest(attribute=attribute, value=value),
                patch.object(target, attribute, value),
                self.assertRaises((TypeError, ValueError)),
            ):
                analyze_ggcoefstats(fitted, **_declarations())
        with (
            patch.object(fitted, "conf_int", return_value=np.zeros((1, 2))),
            self.assertRaises(ValueError),
        ):
            analyze_ggcoefstats(fitted, **_declarations())
        with (
            patch.object(
                fitted,
                "conf_int",
                return_value=np.array([[2.0, 3.0], [2.0, 3.0]]),
            ),
            self.assertRaises(ValueError),
        ):
            analyze_ggcoefstats(fitted, **_declarations())

    def test_analysis_options_resources_and_owned_pairing_fail_explicitly(self) -> None:
        data = _full_z()
        cases = (
            lambda: analyze_ggcoefstats(
                data,
                estimate_label="",
                effect_scale="linear predictor",
                effect_direction="positive is higher",
                effect_units="outcome units",
            ),
            lambda: analyze_ggcoefstats(
                data, **_declarations(), null_value=float("nan")
            ),
            lambda: analyze_ggcoefstats(data, **_declarations(), conf_level=0.0),
            lambda: analyze_ggcoefstats(
                data,
                **_declarations(),
                stats_labels=1,  # type: ignore[arg-type]
            ),
            lambda: analyze_ggcoefstats(
                data, **_declarations(), stats_labels=False, only_significant=True
            ),
            lambda: analyze_ggcoefstats(
                data, **_declarations(), maximum_coefficients=0
            ),
            lambda: analyze_ggcoefstats(
                data, **_declarations(), maximum_rendered_points=2
            ),
            lambda: analyze_ggcoefstats(data, **_declarations(), maximum_labels=2),
            lambda: analyze_ggcoefstats(data, **_declarations(), maximum_labels=1_001),
            lambda: analyze_ggcoefstats(
                data.filter(pl.col("is_intercept")),
                **_declarations(),
                exclude_intercept=True,
            ),
        )
        for operation in cases:
            with (
                self.subTest(operation=operation),
                self.assertRaises((TypeError, ValueError)),
            ):
                operation()

        analysis = analyze_ggcoefstats(data, **_declarations())
        with self.assertRaises(ValueError):
            TableCoefficientAnalysis(
                replace(analysis.table, terms=("other", *analysis.table.terms[1:])),
                analysis.result,
            )
        with self.assertRaises(ValueError):
            TableCoefficientAnalysis(
                replace(
                    analysis.table,
                    estimates=analysis.table.estimates + np.array([0.1, 0.0, 0.0]),
                ),
                analysis.result,
            )

    def test_renderer_schema_extraction_and_composition_use_the_same_result(
        self,
    ) -> None:
        analysis = analyze_ggcoefstats(_full_z(), **_declarations())
        plot = render_ggcoefstats(analysis, title="Coefficients")
        self.addCleanup(plot.figure.clear)
        self.assertIs(extract_stats(plot), analysis.result)
        self.assertIn("unadjusted", plot.subtitle)
        labels = tuple(
            label.get_text() for label in plot.axes["main"].get_yticklabels()
        )
        self.assertEqual(labels[0], "y | all | constant")
        vertical = plot.axes["main"].lines[0]
        self.assertEqual(
            tuple(
                cast(
                    list[float],
                    vertical.get_xdata(),  # pyright: ignore[reportUnknownMemberType]
                )
            ),
            (0.0, 0.0),
        )
        composed = combine_plots((plot,), columns=1)
        self.addCleanup(composed.figure.clear)
        self.assertIs(composed.result.panels[0].result, analysis.result)
        json.dumps(analysis.result.to_dict(), allow_nan=False)
        schema = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "schemas"
                / "coefficient-result.schema.json"
            ).read_text()
        )
        self.assertEqual(
            set(analysis.result.to_dict()),
            set(schema["$defs"]["table_result"]["required"]),
        )

    def test_result_rejects_cross_field_mutations_and_public_options(self) -> None:
        result = analyze_ggcoefstats(_full_z(), **_declarations()).result
        self.assertIsInstance(result, CoefficientTableResult)
        first = result.terms[0]
        operations = (
            lambda: replace(result, retained_rows=2),
            lambda: replace(
                result, display_order=tuple(reversed(result.display_order))
            ),
            lambda: replace(result, inference_profile="estimate_only"),
            lambda: replace(
                result, terms=(replace(first, display_position=2), *result.terms[1:])
            ),
            lambda: replace(result, stats_labels=False, only_significant=True),
            lambda: replace(result, limits=replace(result.limits, maximum_labels=2)),
            lambda: analyze_ggcoefstats(_full_z(), **_declarations(), sort="random"),
            lambda: analyze_ggcoefstats(_full_z(), **_declarations(), alpha=1.0),
            lambda: ggcoefstats(_full_z(), **_declarations(), unknown=True),  # type: ignore[call-arg]
        )
        for operation in operations:
            with (
                self.subTest(operation=operation),
                self.assertRaises((TypeError, ValueError)),
            ):
                operation()

    def test_result_component_constructors_reject_invalid_states(self) -> None:
        result = analyze_ggcoefstats(_full_z(), **_declarations()).result
        first = result.terms[0]
        inference = first.inference
        if inference is None or inference.interval is None:
            self.fail("full-z fixture must retain inference")
        inference_interval = inference.interval
        bad_components = (
            lambda: replace(first.identity, term=""),
            lambda: replace(inference, source="other"),
            lambda: replace(inference, statistic=float("nan")),
            lambda: replace(inference, standard_error=0.0),
            lambda: replace(inference, df=0.0),
            lambda: replace(inference, p_value=2.0),
            lambda: replace(inference, significant=1),
            lambda: replace(
                inference, interval=replace(inference_interval, target="other")
            ),
            lambda: replace(first, is_intercept=1),
            lambda: replace(first, source_position=-1),
            lambda: replace(first, estimate=float("nan")),
            lambda: replace(first, estimate=10.0),
            lambda: CoefficientTableResourceLimits(0, 1, 1),
        )
        for operation in bad_components:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

        model = CoefficientModelSummaryResult(
            "statsmodels.regression.linear_model.OLS",
            "statsmodels.regression.linear_model.RegressionResultsWrapper",
            "0.15.0",
            "HC3",
            False,
            10,
            1.0,
            8.0,
            2,
            2,
            1.0,
            2.0,
        )
        for operation in (
            lambda: replace(model, model_class="other"),
            lambda: replace(model, nobs=0),
            lambda: replace(model, df_resid=0.0),
            lambda: replace(model, aic=float("nan")),
        ):
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

        interval_only = ReportedCoefficientInferenceResult(
            "reported",
            IntervalResult("coefficient", "reported", 0.95, 0.0, 2.0),
            None,
            None,
            None,
            None,
            None,
            None,
        )
        for operation in (
            lambda: replace(result, schema_version=2),
            lambda: replace(result, source_kind="other"),
            lambda: replace(result, identity_columns=("group", "response")),
            lambda: replace(result, estimate_label=""),
            lambda: replace(result, input_rows=2),
            lambda: replace(result, source_order=tuple(reversed(result.source_order))),
            lambda: replace(result, terms=result.terms[:-1]),
            lambda: replace(
                result,
                terms=(
                    replace(first, source_position=result.terms[1].source_position),
                    *result.terms[1:],
                ),
            ),
            lambda: replace(result, conf_level=1.0),
            lambda: replace(result, alpha=0.0),
            lambda: replace(result, sort="other"),
            lambda: replace(result, model_summary=model),
            lambda: replace(
                result, terms=(replace(first, inference=None), *result.terms[1:])
            ),
            lambda: replace(
                result,
                terms=(replace(first, inference=interval_only), *result.terms[1:]),
            ),
            lambda: replace(
                result,
                terms=(
                    replace(
                        first, inference=replace(inference, source="statsmodels_ols")
                    ),
                    *result.terms[1:],
                ),
            ),
            lambda: replace(result, warnings=("",)),
        ):
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()


if __name__ == "__main__":
    unittest.main()
