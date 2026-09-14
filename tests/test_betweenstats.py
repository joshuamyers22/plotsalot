from __future__ import annotations

import json
import math
import unittest
from pathlib import Path

import numpy as np
import polars as pl

from plotsalot import (
    analyze_ggbetweenstats,
    extract_stats,
    ggbetweenstats,
    render_ggbetweenstats,
)


class BetweenStatsTests(unittest.TestCase):
    def test_two_group_welch_values_match_the_approved_formula(self) -> None:
        data = pl.DataFrame(
            {
                "group": ["b"] * 4 + ["a"] * 4,
                "value": [2.0, 3.0, 5.0, 7.0, 1.0, 2.0, 4.0, 8.0],
            }
        )
        analysis = analyze_ggbetweenstats(data, "group", "value")
        result = analysis.result

        left = np.array([1.0, 2.0, 4.0, 8.0])
        right = np.array([2.0, 3.0, 5.0, 7.0])
        estimate = float(left.mean() - right.mean())
        v1 = float(left.var(ddof=1) / left.size)
        v2 = float(right.var(ddof=1) / right.size)
        standard_error = math.sqrt(v1 + v2)
        expected_df = ((v1 + v2) ** 2) / (
            (v1**2 / (left.size - 1)) + (v2**2 / (right.size - 1))
        )
        correction_df = left.size + right.size - 2
        correction = math.gamma(correction_df / 2) / (
            math.sqrt(correction_df / 2) * math.gamma((correction_df - 1) / 2)
        )
        expected_g = (
            estimate
            / math.sqrt((left.var(ddof=1) + right.var(ddof=1)) / 2)
            * correction
        )

        self.assertEqual(tuple(level.level for level in result.levels), ("a", "b"))
        self.assertEqual(result.omnibus.name, "welch_t")
        self.assertAlmostEqual(result.estimate or 0.0, estimate, places=14)
        self.assertAlmostEqual(result.omnibus.statistic, estimate / standard_error)
        self.assertAlmostEqual(result.omnibus.df2, expected_df)
        self.assertAlmostEqual(result.effect_size.value, expected_g)
        self.assertEqual(result.pairwise, ())
        self.assertIsNone(result.correction)
        json.dumps(result.to_dict(), allow_nan=False)

    def test_welch_anova_and_holm_family_are_complete_and_stable(self) -> None:
        data = pl.DataFrame(
            {
                "group": ["b"] * 4 + ["a"] * 4 + ["c"] * 4,
                "value": [2.0, 3.0, 5.0, 7.0, 1.0, 2.0, 4.0, 8.0, 8.0, 9.0, 11.0, 15.0],
            }
        )
        result = analyze_ggbetweenstats(
            data, "group", "value", pairwise_display="none"
        ).result

        self.assertEqual(result.omnibus.name, "welch_anova")
        self.assertEqual(result.omnibus.df1, 2.0)
        self.assertEqual(len(result.pairwise), 3)
        self.assertEqual(
            tuple((item.left, item.right) for item in result.pairwise),
            (("a", "b"), ("a", "c"), ("b", "c")),
        )
        raw = [item.test.p_value for item in result.pairwise]
        adjusted = [item.adjusted_p_value for item in result.pairwise]
        order = sorted(range(3), key=raw.__getitem__)
        running = 0.0
        expected = [0.0, 0.0, 0.0]
        for rank, index in enumerate(order):
            running = max(running, (3 - rank) * raw[index])
            expected[index] = min(1.0, running)
        np.testing.assert_allclose(adjusted, expected, rtol=1e-12, atol=1e-15)
        self.assertGreaterEqual(result.effect_size.value, 0.0)

        reordered = analyze_ggbetweenstats(
            data.reverse(), "group", "value", pairwise_display="none"
        ).result
        self.assertEqual(
            tuple(level.level for level in reordered.levels), ("a", "b", "c")
        )
        self.assertEqual(
            [(item.left, item.right) for item in reordered.pairwise],
            [(item.left, item.right) for item in result.pairwise],
        )
        np.testing.assert_allclose(
            [item.test.statistic for item in reordered.pairwise],
            [item.test.statistic for item in result.pairwise],
        )

    def test_none_adjustment_and_display_never_remove_results(self) -> None:
        data = pl.DataFrame(
            {
                "group": ["a"] * 3 + ["b"] * 3 + ["c"] * 3,
                "value": [1.0, 2.0, 4.0, 2.0, 5.0, 7.0, 8.0, 10.0, 11.0],
            }
        )
        result = analyze_ggbetweenstats(
            data,
            "group",
            "value",
            p_adjust="none",
            pairwise_display="non-significant",
        ).result
        self.assertEqual(len(result.pairwise), 3)
        for item in result.pairwise:
            self.assertEqual(item.test.p_value, item.adjusted_p_value)

    def test_renderer_uses_the_existing_result_and_honors_display(self) -> None:
        data = pl.DataFrame(
            {
                "group": ["a"] * 3 + ["b"] * 3 + ["c"] * 3,
                "value": [1.0, 2.0, 4.0, 2.0, 5.0, 7.0, 8.0, 10.0, 11.0],
            }
        )
        analysis = analyze_ggbetweenstats(
            data, "group", "value", pairwise_display="all"
        )
        plot = render_ggbetweenstats(analysis, title="Independent comparison")
        self.addCleanup(plot.figure.clear)

        self.assertIs(extract_stats(plot), analysis.result)
        self.assertEqual(plot.title, "Independent comparison")
        self.assertIn("welch_anova", plot.subtitle)
        self.assertGreater(len(plot.axes["main"].collections), 0)
        self.assertTrue(
            any(
                "p =" in text.get_text() or "p <" in text.get_text()
                for text in plot.axes["main"].texts
            )
        )

        quiet = ggbetweenstats(
            data,
            "group",
            "value",
            pairwise_display="none",
            results_subtitle=False,
        )
        self.addCleanup(quiet.figure.clear)
        self.assertIn("welch_anova", quiet.subtitle)

    def test_result_matches_schema_top_level(self) -> None:
        result = analyze_ggbetweenstats(
            pl.DataFrame({"g": ["a", "a", "b", "b"], "y": [1.0, 3.0, 2.0, 5.0]}),
            "g",
            "y",
        ).result
        schema = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "schemas"
                / "comparison-result.schema.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(set(result.to_dict()), set(schema["required"]))

    def test_between_surface_rejects_unsupported_and_resource_states(self) -> None:
        valid = pl.DataFrame({"g": ["a", "a", "b", "b"], "y": [1.0, 3.0, 2.0, 5.0]})
        operations = (
            lambda: analyze_ggbetweenstats(valid, "g", "y", type="robust"),
            lambda: analyze_ggbetweenstats(valid, "g", "y", alternative="less"),
            lambda: analyze_ggbetweenstats(valid, "g", "y", conf_level=1.0),
            lambda: analyze_ggbetweenstats(valid, "g", "y", p_adjust="fdr"),
            lambda: analyze_ggbetweenstats(valid, "g", "y", pairwise_alpha=0.0),
            lambda: analyze_ggbetweenstats(valid, "g", "y", pairwise_display="x"),
            lambda: analyze_ggbetweenstats(valid, "g", "y", maximum_levels=1),
            lambda: analyze_ggbetweenstats(
                valid, "g", "y", maximum_rendered_observations=0
            ),
        )
        for operation in operations:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

        analysis = analyze_ggbetweenstats(
            valid, "g", "y", maximum_rendered_observations=3
        )
        with self.assertRaisesRegex(ValueError, "maximum_rendered_observations=3"):
            render_ggbetweenstats(analysis)


if __name__ == "__main__":
    unittest.main()
