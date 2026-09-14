from __future__ import annotations

import json
import math
import unittest
from dataclasses import replace
from datetime import date

import numpy as np
import polars as pl

from plotsalot import (
    DotPlotAnalysis,
    analyze_ggdotplotstats,
    extract_stats,
    ggdotplotstats,
    render_ggdotplotstats,
)


class GgDotPlotStatsTests(unittest.TestCase):
    def test_labeled_estimates_and_overall_sample_reconcile(self) -> None:
        data = pl.DataFrame(
            {
                "value": [1.0, 3.0, 2.0, 4.0, None, 10.0],
                "label": ["b", "b", "a", "a", "a", None],
            }
        )

        analysis = analyze_ggdotplotstats(data, "value", "label")
        result = analysis.result

        self.assertEqual(result.sample.input_rows, 6)
        self.assertEqual(result.sample.analyzed_rows, 4)
        self.assertEqual(result.sample.dropped_null_rows, 2)
        self.assertEqual(
            [(estimate.label, estimate.value) for estimate in result.estimates],
            [("b", 2.0), ("a", 3.0)],
        )
        self.assertEqual(result.estimates[1].sample.input_rows, 3)
        self.assertEqual(result.estimates[1].sample.analyzed_rows, 2)
        self.assertEqual(result.estimates[1].sample.dropped_null_rows, 1)
        self.assertAlmostEqual(result.one_sample.estimate.value, 2.5, places=12)
        self.assertAlmostEqual(
            result.estimates[0].standard_deviation or 0.0,
            math.sqrt(2.0),
            places=12,
        )
        json.dumps(result.to_dict(), allow_nan=False)

    def test_singleton_and_constant_labels_have_typed_warnings(self) -> None:
        result = analyze_ggdotplotstats(
            pl.DataFrame(
                {"value": [1.0, 1.0, 3.0], "label": ["constant", "constant", "one"]}
            ),
            "value",
            "label",
        ).result

        by_label = {estimate.label: estimate for estimate in result.estimates}
        self.assertIsNone(by_label["constant"].interval)
        self.assertIsNone(by_label["one"].interval)
        self.assertIn("constant", " ".join(result.warnings))
        self.assertIn("singleton", " ".join(result.warnings))

    def test_numeric_labels_preserve_json_scalar_identity(self) -> None:
        result = analyze_ggdotplotstats(
            pl.DataFrame({"value": [1.0, 2.0, 3.0], "label": [2, 2, 1]}),
            "value",
            "label",
        ).result

        self.assertEqual({estimate.label for estimate in result.estimates}, {1, 2})
        self.assertTrue(all(isinstance(item.label, int) for item in result.estimates))

    def test_analysis_and_rendering_are_separate(self) -> None:
        analysis = analyze_ggdotplotstats(
            pl.DataFrame(
                {"value": [1.0, 2.0, 4.0, 5.0], "label": ["a", "a", "b", "b"]}
            ),
            "value",
            "label",
        )

        plot = render_ggdotplotstats(analysis, title="Labeled means")
        self.addCleanup(plot.figure.clear)

        self.assertIs(extract_stats(plot), analysis.result)
        self.assertEqual(plot.title, "Labeled means")
        self.assertGreaterEqual(len(plot.axes["main"].lines), 3)

    def test_renderer_formats_only_the_supplied_typed_result(self) -> None:
        analysis = analyze_ggdotplotstats(
            pl.DataFrame(
                {"value": [1.0, 2.0, 4.0, 5.0], "label": ["a", "a", "b", "b"]}
            ),
            "value",
            "label",
        )
        one_sample = replace(
            analysis.result.one_sample,
            test=replace(
                analysis.result.one_sample.test,
                statistic=1.234,
                p_value=0.456,
            ),
            effect_size=replace(
                analysis.result.one_sample.effect_size,
                value=-0.5,
            ),
        )
        supplied = DotPlotAnalysis(
            sample=analysis.sample,
            result=replace(analysis.result, one_sample=one_sample),
        )
        plot = render_ggdotplotstats(supplied)
        self.addCleanup(plot.figure.clear)

        self.assertIn("t(3) = 1.23", plot.subtitle)
        self.assertIn("p = 0.456", plot.subtitle)
        self.assertIn("Cohen's d = -0.50", plot.subtitle)

    def test_convenience_surface_and_invalid_inputs(self) -> None:
        valid = pl.DataFrame({"value": [1.0, 2.0, 3.0], "label": ["a", "a", "b"]})
        plot = ggdotplotstats(valid, "value", "label", show_intervals=False)
        self.addCleanup(plot.figure.clear)
        self.assertEqual(plot.result.label_column, "label")

        operations = (
            lambda: analyze_ggdotplotstats(object(), "value", "label"),
            lambda: analyze_ggdotplotstats(valid, "value", "value"),
            lambda: analyze_ggdotplotstats(valid, "missing", "label"),
            lambda: analyze_ggdotplotstats(
                pl.DataFrame({"value": ["x", "y"], "label": ["a", "b"]}),
                "value",
                "label",
            ),
            lambda: analyze_ggdotplotstats(
                pl.DataFrame({"value": [1.0, np.inf], "label": ["a", "b"]}),
                "value",
                "label",
            ),
            lambda: analyze_ggdotplotstats(valid, "value", "label", maximum_rows=2),
            lambda: analyze_ggdotplotstats(
                pl.DataFrame({"value": [1.0, 2.0], "label": [None, None]}),
                "value",
                "label",
            ),
            lambda: analyze_ggdotplotstats(
                pl.DataFrame(
                    {
                        "value": [1.0, 2.0],
                        "label": [date(2026, 1, 1), date(2026, 1, 1)],
                    }
                ),
                "value",
                "label",
            ),
        )
        for operation in operations:
            with (
                self.subTest(operation=operation),
                self.assertRaises((TypeError, ValueError)),
            ):
                operation()


if __name__ == "__main__":
    unittest.main()
