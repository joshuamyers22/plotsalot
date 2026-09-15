from __future__ import annotations

import json
import unittest
from typing import Any, cast

import polars as pl

from plotsalot import (
    BayesianMetaAnalysis,
    PosteriorCoefficientTableResult,
    ReportedCoefficientAnalysis,
    RobustCoefficientTableResult,
    RobustMetaAnalysis,
    analyze_ggcoefstats,
    combine_plots,
    extract_caption,
    extract_stats,
    extract_subtitle,
    ggcoefstats,
    render_ggcoefstats,
)

DECLARATIONS: dict[str, Any] = {
    "estimate_label": "Coefficient",
    "effect_scale": "additive score",
    "effect_direction": "positive is higher",
    "effect_units": "score units",
}
META_DECLARATIONS: dict[str, Any] = {
    "meta_analytic_effect": True,
    "estimand": "population treatment effect",
    "effect_scale": "mean difference",
    "effect_direction": "positive favors treatment",
    "effect_units": "points",
}


def robust_coefficients() -> ReportedCoefficientAnalysis:
    data = pl.DataFrame(
        {
            "term": ["dose", "age"],
            "response": ["score", "score"],
            "estimate": [0.8, -0.2],
            "conf_low": [0.4, -0.6],
            "conf_high": [1.2, 0.1],
        }
    )
    return cast(
        ReportedCoefficientAnalysis,
        analyze_ggcoefstats(
            data,
            type="robust",
            robust_method="Huber M-estimator",
            robust_tuning="c=1.345",
            interval_method="sandwich Wald",
            **DECLARATIONS,
        ),
    )


def posterior_coefficients() -> ReportedCoefficientAnalysis:
    data = pl.DataFrame(
        {
            "term": ["dose", "age"],
            "group": ["all", "all"],
            "posterior_median": [0.75, -0.15],
            "credible_low": [0.3, -0.5],
            "credible_high": [1.1, 0.2],
            "probability_above_null": [0.98, 0.25],
            "probability_below_null": [0.02, 0.75],
            "probability_at_null": [0.0, 0.0],
        }
    )
    return cast(
        ReportedCoefficientAnalysis,
        analyze_ggcoefstats(
            data,
            type="bayes",
            posterior_model="normal linear model",
            likelihood="Gaussian likelihood",
            prior_description="proper weakly informative normal priors",
            computation_method="deterministic quadrature",
            **DECLARATIONS,
        ),
    )


def robust_meta() -> RobustMetaAnalysis:
    data = pl.DataFrame(
        {
            "term": [f"study-{index + 1}" for index in range(10)],
            "estimate": [0.1, 0.3, 0.2, 0.5, 0.4, 0.0, 0.6, 0.35, 0.25, 3.0],
            "standard_error": [
                0.2,
                0.25,
                0.2,
                0.3,
                0.22,
                0.18,
                0.28,
                0.2,
                0.24,
                0.3,
            ],
        }
    )
    return cast(
        RobustMetaAnalysis,
        analyze_ggcoefstats(data, type="robust", **META_DECLARATIONS),
    )


def bayesian_meta() -> BayesianMetaAnalysis:
    data = pl.DataFrame(
        {
            "term": ["study-1", "study-2", "study-3"],
            "estimate": [0.2, 0.4, 0.1],
            "standard_error": [0.2, 0.25, 0.3],
        }
    )
    return cast(
        BayesianMetaAnalysis,
        analyze_ggcoefstats(
            data,
            type="bayes",
            prior_mean_scale=1.0,
            prior_tau_scale=0.5,
            **META_DECLARATIONS,
        ),
    )


class M6CRenderIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.robust_coefficient_analysis = robust_coefficients()
        cls.posterior_coefficient_analysis = posterior_coefficients()
        cls.robust_meta_analysis = robust_meta()
        cls.bayesian_meta_analysis = bayesian_meta()

    def test_reported_robust_renderer_uses_retained_intervals_and_provenance(
        self,
    ) -> None:
        analysis = self.robust_coefficient_analysis
        result = cast(RobustCoefficientTableResult, analysis.result)
        plot = render_ggcoefstats(analysis, title="Robust coefficients")
        self.addCleanup(plot.figure.clear)
        self.assertIs(extract_stats(plot), result)
        self.assertEqual(plot.title, "Robust coefficients")
        self.assertIn("confidence intervals", extract_subtitle(plot))
        self.assertIn(result.provenance.robust_method, extract_caption(plot))
        labels = tuple(text.get_text() for text in plot.axes["main"].texts)
        self.assertTrue(any("95% CI [0.4, 1.2]" in label for label in labels))
        vertical = plot.axes["main"].lines[0]
        x_data = cast(
            list[float],
            vertical.get_xdata(),  # pyright: ignore[reportUnknownMemberType]
        )
        self.assertEqual(tuple(x_data), (result.null_value,) * 2)

    def test_reported_posterior_renderer_uses_credible_vocabulary_and_probability(
        self,
    ) -> None:
        analysis = self.posterior_coefficient_analysis
        result = cast(PosteriorCoefficientTableResult, analysis.result)
        plot = render_ggcoefstats(analysis)
        self.addCleanup(plot.figure.clear)
        self.assertIs(plot.result, result)
        self.assertIn("equal-tail credible intervals", plot.subtitle)
        self.assertIn(result.provenance.prior_description, plot.caption)
        labels = tuple(text.get_text() for text in plot.axes["main"].texts)
        self.assertTrue(any("P(>0) = 0.980" in label for label in labels))
        self.assertFalse(any("p =" in label for label in labels))

    def test_robust_meta_renderer_has_profile_role_and_explicit_absences(self) -> None:
        analysis = self.robust_meta_analysis
        result = analysis.result
        plot = render_ggcoefstats(analysis)
        self.addCleanup(plot.figure.clear)
        self.assertIs(plot.result, result)
        self.assertIn("profile CI", plot.subtitle)
        self.assertIn(
            result.meta_analysis.pooled.prediction_absence_reason, plot.caption
        )
        labels = plot.axes["main"].get_legend_handles_labels()[1]
        self.assertEqual(labels, ["pooled profile-likelihood confidence interval"])
        pooled_lines = [
            line for line in plot.axes["main"].lines if line.get_marker() == "D"
        ]
        self.assertEqual(len(pooled_lines), 1)
        pooled_x = cast(
            list[float],
            pooled_lines[0].get_xdata(),  # pyright: ignore[reportUnknownMemberType]
        )
        self.assertAlmostEqual(pooled_x[0], result.meta_analysis.pooled.estimate)

    def test_bayesian_meta_renderer_has_distinct_pooled_and_prediction_roles(
        self,
    ) -> None:
        analysis = self.bayesian_meta_analysis
        result = analysis.result
        plot = render_ggcoefstats(analysis)
        self.addCleanup(plot.figure.clear)
        self.assertIs(plot.result, result)
        self.assertIn(result.primary.evidence.display, plot.subtitle)
        self.assertIn("sensitivities:", plot.caption)
        labels = plot.axes["main"].get_legend_handles_labels()[1]
        self.assertEqual(
            set(labels),
            {
                "pooled equal-tail credible interval",
                "new-study posterior predictive credible interval",
            },
        )
        no_prediction = render_ggcoefstats(analysis, show_prediction=False)
        self.addCleanup(no_prediction.figure.clear)
        self.assertNotIn(
            "new-study posterior predictive credible interval",
            no_prediction.axes["main"].get_legend_handles_labels()[1],
        )

    def test_public_wrapper_and_mixed_mode_composition_preserve_exact_results(
        self,
    ) -> None:
        public = ggcoefstats(
            pl.DataFrame(
                {
                    "term": ["dose"],
                    "estimate": [0.8],
                    "conf_low": [0.4],
                    "conf_high": [1.2],
                }
            ),
            type="robust",
            robust_method="Huber M-estimator",
            robust_tuning="c=1.345",
            interval_method="sandwich Wald",
            **DECLARATIONS,
        )
        self.addCleanup(public.figure.clear)
        self.assertIsInstance(public.result, RobustCoefficientTableResult)

        plots = (
            public,
            render_ggcoefstats(self.posterior_coefficient_analysis),
            render_ggcoefstats(self.robust_meta_analysis),
            render_ggcoefstats(self.bayesian_meta_analysis),
        )
        for plot in plots[1:]:
            self.addCleanup(plot.figure.clear)
        composed = combine_plots(plots, columns=2, panel_tags="A")
        self.addCleanup(composed.figure.clear)
        self.assertEqual(len(composed.result.panels), 4)
        for panel, source in zip(composed.result.panels, plots, strict=True):
            self.assertIs(panel.result, source.result)
        json.dumps(composed.result.to_dict(), allow_nan=False)

    def test_presentation_options_do_not_change_results(self) -> None:
        analysis = cast(
            ReportedCoefficientAnalysis,
            analyze_ggcoefstats(
                pl.DataFrame(
                    {
                        "term": ["dose"],
                        "posterior_median": [0.75],
                        "credible_low": [0.3],
                        "credible_high": [1.1],
                        "probability_above_null": [0.98],
                        "probability_below_null": [0.02],
                        "probability_at_null": [0.0],
                    }
                ),
                type="bayes",
                posterior_model="normal linear model",
                likelihood="Gaussian likelihood",
                prior_description="proper weakly informative normal priors",
                computation_method="deterministic quadrature",
                stats_labels=False,
                **DECLARATIONS,
            ),
        )
        plot = render_ggcoefstats(
            analysis,
            results_subtitle=False,
            show_intervals=False,
        )
        self.addCleanup(plot.figure.clear)
        self.assertIs(plot.result, analysis.result)
        self.assertEqual(tuple(plot.axes["main"].texts), ())

    def test_renderer_and_identity_boundaries_reject_adversarial_inputs(self) -> None:
        with self.assertRaisesRegex(TypeError, "approved coefficient analysis"):
            render_ggcoefstats(cast(Any, object()))
        for term in ("bad\nterm", "x" * 201):
            with (
                self.subTest(term=term),
                self.assertRaisesRegex(ValueError, "renderable"),
            ):
                analyze_ggcoefstats(
                    pl.DataFrame(
                        {
                            "term": [term],
                            "estimate": [0.8],
                            "conf_low": [0.4],
                            "conf_high": [1.2],
                        }
                    ),
                    type="robust",
                    robust_method="Huber M-estimator",
                    robust_tuning="c=1.345",
                    interval_method="sandwich Wald",
                    **DECLARATIONS,
                )
        with self.assertRaisesRegex(ValueError, "M6C study identities.*renderable"):
            analyze_ggcoefstats(
                pl.DataFrame(
                    {
                        "term": ["study-1", "bad\nstudy", "study-3"],
                        "estimate": [0.2, 0.4, 0.1],
                        "standard_error": [0.2, 0.25, 0.3],
                    }
                ),
                type="robust",
                **META_DECLARATIONS,
            )
        unicode_analysis = cast(
            ReportedCoefficientAnalysis,
            analyze_ggcoefstats(
                pl.DataFrame(
                    {
                        "term": ["β-dose"],
                        "estimate": [0.8],
                        "conf_low": [0.4],
                        "conf_high": [1.2],
                    }
                ),
                type="robust",
                robust_method="Huber M-estimator",
                robust_tuning="c=1.345",
                interval_method="sandwich Wald",
                **DECLARATIONS,
            ),
        )
        plot = render_ggcoefstats(unicode_analysis)
        self.addCleanup(plot.figure.clear)
        self.assertEqual(plot.axes["main"].get_yticklabels()[0].get_text(), "β-dose")


if __name__ == "__main__":
    unittest.main()
