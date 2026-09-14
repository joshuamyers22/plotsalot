from __future__ import annotations

import json
import unittest
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import polars as pl

from plotsalot import (
    CoefficientAnalysis,
    analyze_ggcoefstats,
    combine_plots,
    extract_stats,
    ggcoefstats,
    render_ggcoefstats,
)
from plotsalot.coefficient_result import CoefficientResourceLimits, PredictionResult
from plotsalot.result import IntervalResult


def _data() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "term": ["A", "B", "C", "D", "E"],
            "estimate": [0.1, 0.5, 1.2, -0.2, 1.8],
            "standard_error": [0.1, 0.2, 0.25, 0.15, 0.3],
        }
    )


def _analysis() -> CoefficientAnalysis:
    return analyze_ggcoefstats(
        _data(),
        meta_analytic_effect=True,
        estimand="mean treatment effect",
        effect_scale="mean difference",
        effect_direction="positive favors treatment",
        effect_units="points",
    )


class CoefficientResultAndRenderTests(unittest.TestCase):
    def test_result_is_json_safe_and_matches_checked_in_schema_shape(self) -> None:
        result = _analysis().result
        payload = result.to_dict()
        schema = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "schemas"
                / "coefficient-result.schema.json"
            ).read_text(encoding="utf-8")
        )

        json.dumps(payload, allow_nan=False)
        self.assertEqual(set(payload), set(schema["required"]))
        self.assertEqual(
            set(payload["terms"][0]), set(schema["$defs"]["term"]["required"])
        )
        self.assertEqual(
            set(payload["meta_analysis"]), set(schema["$defs"]["meta"]["required"])
        )

    def test_result_records_reject_cross_field_contradictions(self) -> None:
        analysis = _analysis()
        result = analysis.result
        first = result.terms[0]
        meta = result.meta_analysis
        cases = (
            lambda: replace(result, schema_version=2),
            lambda: replace(result, retained_rows=4),
            lambda: replace(
                result, display_order=tuple(reversed(result.display_order))
            ),
            lambda: replace(result, terms=result.terms[:-1]),
            lambda: replace(result, conf_level=0.9),
            lambda: replace(result, alpha=0.1),
            lambda: replace(
                result,
                terms=(
                    replace(first, normalized_weight=first.normalized_weight + 0.1),
                    *result.terms[1:],
                ),
            ),
            lambda: replace(
                result,
                terms=(
                    replace(
                        first, random_effects_weight=first.random_effects_weight * 2
                    ),
                    *result.terms[1:],
                ),
            ),
            lambda: replace(
                result,
                meta_analysis=replace(
                    meta,
                    prediction=replace(
                        meta.prediction,
                        interval=None,
                        absence_reason="fewer_than_five_studies",
                    ),
                ),
            ),
            lambda: replace(result, warnings=("",)),
        )
        for operation in cases:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

        with self.assertRaises(ValueError):
            CoefficientAnalysis(
                analysis.table,
                replace(result, source_order=("wrong", *result.source_order[1:])),
            )

    def test_nested_result_records_reject_invalid_states(self) -> None:
        result = _analysis().result
        term = result.terms[0]
        inference = term.inference
        convergence = result.meta_analysis.convergence
        pooled = result.meta_analysis.pooled
        prediction = result.meta_analysis.prediction
        heterogeneity = result.meta_analysis.heterogeneity
        meta = result.meta_analysis
        bad = cast(Any, "unsupported")

        operations = (
            lambda: CoefficientResourceLimits(0, 1, 1),
            lambda: replace(inference, source="unsupported"),
            lambda: replace(inference, standard_error=0.0),
            lambda: replace(inference, statistic=float("inf")),
            lambda: replace(inference, statistic_name=bad),
            lambda: replace(inference, df=cast(Any, 1)),
            lambda: replace(inference, p_value=1.1),
            lambda: replace(inference, significant=cast(Any, 1)),
            lambda: replace(
                inference, interval=replace(inference.interval, target="other")
            ),
            lambda: replace(
                inference, interval=replace(inference.interval, method="other")
            ),
            lambda: replace(term, term=""),
            lambda: replace(term, term=cast(Any, 1)),
            lambda: replace(term, source_position=-1),
            lambda: replace(term, display_position=-1),
            lambda: replace(term, estimate=float("nan")),
            lambda: replace(term, sampling_variance=0.0),
            lambda: replace(term, normalized_weight=0.0),
            lambda: replace(term, estimate=inference.interval.high + 1.0),
            lambda: replace(term, sampling_variance=term.sampling_variance * 2.0),
            lambda: replace(
                term, weighted_contribution=term.weighted_contribution + 1.0
            ),
            lambda: replace(convergence, method=bad),
            lambda: replace(convergence, scale_factor=float("nan")),
            lambda: replace(convergence, converged=False),
            lambda: replace(convergence, boundary=cast(Any, 1)),
            lambda: replace(convergence, bracket_low=-1.0),
            lambda: replace(convergence, iterations=cast(Any, 1.5)),
            lambda: replace(convergence, score_tolerance=0.0),
            lambda: replace(convergence, boundary=True, bracket_high=1.0),
            lambda: replace(pooled, method=bad),
            lambda: replace(pooled, statistic_name=bad),
            lambda: replace(pooled, estimate=float("nan")),
            lambda: replace(pooled, standard_error=0.0),
            lambda: replace(pooled, q_hk=-1.0),
            lambda: replace(pooled, q_star=0.5),
            lambda: replace(pooled, q_star=pooled.q_hk + 1.0),
            lambda: replace(pooled, standard_error=pooled.standard_error * 2.0),
            lambda: replace(pooled, df=1),
            lambda: replace(pooled, p_value=-0.1),
            lambda: replace(pooled, interval=replace(pooled.interval, target="other")),
            lambda: PredictionResult(None, None),
            lambda: PredictionResult(prediction.interval, "fewer_than_five_studies"),
            lambda: PredictionResult(
                replace(cast(IntervalResult, prediction.interval), target="other"),
                None,
            ),
            lambda: PredictionResult(None, bad),
            lambda: replace(heterogeneity, q=float("nan")),
            lambda: replace(heterogeneity, q=-1.0),
            lambda: replace(heterogeneity, df=1),
            lambda: replace(heterogeneity, p_value=1.1),
            lambda: replace(heterogeneity, i_squared=1.1),
            lambda: replace(heterogeneity, tau=heterogeneity.tau + 1.0),
            lambda: replace(
                heterogeneity, tau_squared_interval=cast(Any, pooled.interval)
            ),
            lambda: replace(heterogeneity, tau_squared_interval_absence_reason=bad),
            lambda: replace(meta, estimand=""),
            lambda: replace(meta, estimand=cast(Any, 1)),
            lambda: replace(meta, null_value=float("nan")),
            lambda: replace(meta, dependence=bad),
            lambda: replace(meta, sampling_model=bad),
            lambda: replace(meta, estimator=bad),
            lambda: replace(meta, heterogeneity=replace(heterogeneity, df=3)),
        )
        for operation in operations:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

    def test_top_level_result_rejects_all_reconciliation_failures(self) -> None:
        result = _analysis().result
        first = result.terms[0]
        meta = result.meta_analysis
        pooled = meta.pooled
        prediction = cast(IntervalResult, meta.prediction.interval)
        bad = cast(Any, "unsupported")

        operations = (
            lambda: replace(result, analysis=bad),
            lambda: replace(result, source_kind=bad),
            lambda: replace(result, inference_profile=bad),
            lambda: replace(result, term_column=bad),
            lambda: replace(result, input_rows=cast(Any, True)),
            lambda: replace(result, stats_labels=cast(Any, 1)),
            lambda: replace(result, input_rows=4),
            lambda: replace(result, source_order=("A", "A", "C", "D", "E")),
            lambda: replace(
                result,
                terms=(replace(first, source_position=1), *result.terms[1:]),
            ),
            lambda: replace(result, conf_level=float("nan")),
            lambda: replace(
                result,
                terms=(
                    replace(
                        first,
                        inference=replace(
                            first.inference,
                            interval=replace(first.inference.interval, level=0.9),
                        ),
                    ),
                    *result.terms[1:],
                ),
            ),
            lambda: replace(
                result,
                terms=(
                    replace(
                        first,
                        inference=replace(
                            first.inference,
                            significant=not first.inference.significant,
                        ),
                    ),
                    *result.terms[1:],
                ),
            ),
            lambda: replace(
                result,
                terms=(
                    replace(
                        first,
                        inference=replace(
                            first.inference,
                            statistic=first.inference.statistic + 1.0,
                        ),
                    ),
                    *result.terms[1:],
                ),
            ),
            lambda: replace(
                result,
                meta_analysis=replace(
                    meta,
                    pooled=replace(
                        pooled, interval=replace(pooled.interval, level=0.9)
                    ),
                ),
            ),
            lambda: replace(
                result,
                meta_analysis=replace(
                    meta,
                    prediction=replace(
                        meta.prediction,
                        interval=replace(prediction, level=0.9),
                    ),
                ),
            ),
            lambda: replace(
                result,
                meta_analysis=replace(
                    meta,
                    prediction=replace(
                        meta.prediction,
                        interval=replace(
                            prediction,
                            low=prediction.low + 0.01,
                            high=prediction.high + 0.01,
                        ),
                    ),
                ),
            ),
            lambda: replace(
                result,
                terms=(
                    replace(
                        first, random_effects_weight=first.random_effects_weight * 2
                    ),
                    *result.terms[1:],
                ),
            ),
            lambda: replace(
                result,
                terms=(
                    replace(
                        first,
                        normalized_weight=first.normalized_weight + 0.01,
                        weighted_contribution=(first.normalized_weight + 0.01)
                        * first.estimate,
                    ),
                    *result.terms[1:],
                ),
            ),
            lambda: replace(
                result,
                meta_analysis=replace(meta, pooled=replace(pooled, df=pooled.df + 1)),
            ),
            lambda: replace(
                result,
                meta_analysis=replace(
                    meta,
                    pooled=replace(
                        pooled,
                        conventional_variance=pooled.conventional_variance * 2,
                    ),
                ),
            ),
            lambda: replace(
                result,
                meta_analysis=replace(
                    meta,
                    convergence=replace(meta.convergence, boundary=True),
                ),
            ),
            lambda: replace(
                result,
                limits=replace(result.limits, maximum_studies=4),
            ),
            lambda: replace(
                result,
                stats_labels=True,
                only_significant=False,
                limits=replace(result.limits, maximum_labels=4),
            ),
        )
        for operation in operations:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

    def test_renderer_uses_typed_result_and_preserves_extraction_identity(self) -> None:
        analysis = _analysis()

        plot = render_ggcoefstats(analysis, title="Study effects")
        self.addCleanup(plot.figure.clear)

        self.assertIs(extract_stats(plot), analysis.result)
        self.assertEqual(plot.title, "Study effects")
        self.assertIn("REML + modified Hartung-Knapp", plot.subtitle)
        self.assertIn("prediction", plot.caption)
        labels = tuple(
            label.get_text() for label in plot.axes["main"].get_yticklabels()
        )
        self.assertEqual(labels, ("A", "B", "C", "D", "E", "Pooled"))
        vertical = plot.axes["main"].lines[0]
        x_data = cast(
            list[float],
            vertical.get_xdata(),  # pyright: ignore[reportUnknownMemberType]
        )
        self.assertEqual(tuple(x_data), (0.0, 0.0))

    def test_labels_are_presentation_only_and_plot_composes_with_m4(self) -> None:
        meta_plot = ggcoefstats(
            _data(),
            meta_analytic_effect=True,
            estimand="mean treatment effect",
            effect_scale="mean difference",
            effect_direction="positive favors treatment",
            effect_units="points",
            only_significant=True,
        )
        self.addCleanup(meta_plot.figure.clear)
        visible_labels = tuple(text.get_text() for text in meta_plot.axes["main"].texts)
        self.assertLess(len(visible_labels), len(meta_plot.result.terms) + 1)
        self.assertEqual(len(meta_plot.result.terms), 5)

        composed = combine_plots((meta_plot,), columns=1)
        self.addCleanup(composed.figure.clear)
        self.assertIs(composed.result.panels[0].result, meta_plot.result)

    def test_public_render_functions_reject_invalid_options_and_keywords(self) -> None:
        analysis = _analysis()
        cases = (
            lambda: render_ggcoefstats(analysis, title=""),
            lambda: render_ggcoefstats(analysis, point_color=""),
            lambda: render_ggcoefstats(analysis, point_color="not-a-color"),
            lambda: render_ggcoefstats(analysis, results_subtitle=1),  # type: ignore[arg-type]
            lambda: ggcoefstats(_data(), unknown=True),  # type: ignore[call-arg]
        )
        for operation in cases:
            with (
                self.subTest(operation=operation),
                self.assertRaises((TypeError, ValueError)),
            ):
                operation()


if __name__ == "__main__":
    unittest.main()
