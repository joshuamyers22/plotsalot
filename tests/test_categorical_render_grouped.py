from __future__ import annotations

import unittest
from dataclasses import replace

import matplotlib.colors as mcolors
import polars as pl
from matplotlib.patches import Rectangle

from plotsalot import (
    CategoricalAnalysis,
    analyze_categorical,
    analyze_grouped_ggbarstats,
    combine_plots,
    extract_stats,
    ggbarstats,
    ggpiestats,
    grouped_ggbarstats,
    grouped_ggpiestats,
    render_ggbarstats,
    render_ggpiestats,
)


def _data() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "x": ["a", "a", "b", "b", "c", "c"],
            "y": ["u", "v", "u", "v", "u", "v"],
            "n": [30, 10, 15, 25, 10, 30],
        }
    )


class CategoricalRenderTests(unittest.TestCase):
    def test_bar_and_pie_consume_the_same_analysis_result(self) -> None:
        analysis = analyze_categorical(_data(), "x", "y", counts="n")

        bar = render_ggbarstats(analysis, label="both")
        pie = render_ggpiestats(analysis, label="both")
        self.addCleanup(bar.figure.clear)
        self.addCleanup(pie.figure.clear)

        self.assertIs(extract_stats(bar), analysis.result)
        self.assertIs(extract_stats(pie), analysis.result)
        self.assertEqual(len(bar.axes["main"].patches), 6)
        self.assertEqual(len(pie.axes), 2)
        self.assertEqual(len(pie.axes["facet_1"].patches), 3)
        self.assertIn("N = 120", bar.caption)
        self.assertEqual(bar.subtitle, pie.subtitle)
        bar_text = tuple(text.get_text() for text in bar.axes["main"].texts)
        self.assertIn("30 (55%)", bar_text)
        self.assertIn("N=55", bar_text)
        self.assertTrue(any("p=" in value for value in bar_text))
        self.assertIn("N=55", pie.axes["facet_1"].get_title())

    def test_one_way_zero_category_and_label_modes_are_semantic(self) -> None:
        data = pl.DataFrame(
            {
                "x": pl.Series(["a", "b", "c"], dtype=pl.Enum(["c", "a", "b"])),
                "n": [10, 20, 0],
            }
        )

        bar = ggbarstats(data, "x", counts="n", label="none")
        pie = ggpiestats(data, "x", counts="n", label="count")
        self.addCleanup(bar.figure.clear)
        self.addCleanup(pie.figure.clear)

        self.assertEqual(bar.result.x_levels, ("c", "a", "b"))
        heights = tuple(
            patch.get_height()
            for patch in bar.axes["main"].patches
            if isinstance(patch, Rectangle)
        )
        for actual, expected in zip(heights, (0.0, 1 / 3, 2 / 3), strict=True):
            self.assertAlmostEqual(actual, expected)
        labels = tuple(text.get_text() for text in pie.axes["facet_1"].texts)
        self.assertNotIn("0", labels)
        self.assertIn("10", labels)
        self.assertIn("20", labels)

    def test_pairwise_filter_and_subtitle_toggle_change_display_only(self) -> None:
        analysis = analyze_categorical(
            _data(), "x", "y", counts="n", pairwise_display="all"
        )
        all_plot = render_ggbarstats(analysis, results_subtitle=False)
        hidden_result = replace(analysis.result, pairwise_display="none")
        hidden_analysis = CategoricalAnalysis(analysis.table, hidden_result)
        hidden_plot = render_ggbarstats(hidden_analysis)
        self.addCleanup(all_plot.figure.clear)
        self.addCleanup(hidden_plot.figure.clear)

        self.assertIn("a vs b", all_plot.caption)
        self.assertNotIn("pairwise:", hidden_plot.caption)
        self.assertEqual(all_plot.result.pairwise, hidden_plot.result.pairwise)
        visible_text = tuple(text.get_text() for text in all_plot.axes["main"].texts)
        self.assertNotIn(all_plot.subtitle, visible_text)

    def test_renderer_uses_injected_statistical_result(self) -> None:
        analysis = analyze_categorical(_data(), "x", "y", counts="n")
        injected_test = replace(analysis.result.omnibus, p_value=0.5)
        injected_result = replace(analysis.result, omnibus=injected_test)
        injected = CategoricalAnalysis(analysis.table, injected_result)

        plot = render_ggpiestats(injected)
        self.addCleanup(plot.figure.clear)

        self.assertIn("p = 0.500", plot.subtitle)

    def test_public_functions_reject_unknown_keywords(self) -> None:
        with self.assertRaises(TypeError):
            ggbarstats(_data(), "x", unknown=True)  # type: ignore[call-arg]
        with self.assertRaises(TypeError):
            ggpiestats(_data(), "x", unknown=True)  # type: ignore[call-arg]

    def test_categorical_plots_compose_without_losing_results(self) -> None:
        bar = ggbarstats(_data(), "x", "y", counts="n")
        pie = ggpiestats(_data(), "x", "y", counts="n")
        composed = combine_plots((bar, pie), columns=2)
        self.addCleanup(bar.figure.clear)
        self.addCleanup(pie.figure.clear)
        self.addCleanup(composed.figure.clear)

        self.assertEqual(len(composed.result.panels), 2)
        self.assertIs(composed.result.panels[0].result, bar.result)
        self.assertIs(composed.result.panels[1].result, pie.result)


class GroupedCategoricalTests(unittest.TestCase):
    def test_group_order_audit_nested_scope_and_common_colors_are_stable(self) -> None:
        data = pl.DataFrame(
            {
                "group": ["second"] * 4 + ["first"] * 4 + [None],
                "x": ["b", "c", "b", "c", "a", "b", "a", "b", "a"],
                "n": [20, 20, 10, 30, 25, 15, 15, 25, 99],
            }
        )

        analysis = analyze_grouped_ggbarstats(data, "x", "group", counts="n")
        bars = grouped_ggbarstats(data, "x", "group", counts="n")
        pies = grouped_ggpiestats(data, "x", "group", counts="n")
        for grouped in (bars, pies):
            for plot in grouped.plots:
                self.addCleanup(plot.figure.clear)

        self.assertEqual(
            tuple(item.group for item in analysis.groups), ("second", "first")
        )
        self.assertEqual(analysis.result.sample.input_rows, 9)
        self.assertEqual(analysis.result.sample.analyzed_rows, 8)
        self.assertEqual(analysis.result.sample.dropped_null_group_rows, 1)
        self.assertEqual(
            analysis.result.correction_scope,
            "within_each_categorical_result_none_across_outer_groups",
        )
        self.assertEqual(len(bars.plots), 2)
        self.assertEqual(len(pies.plots), 2)
        second_b = bars.plots[0].axes["main"].patches[0].get_facecolor()
        first_b = bars.plots[1].axes["main"].patches[1].get_facecolor()
        self.assertEqual(mcolors.to_hex(second_b), mcolors.to_hex(first_b))

    def test_invalid_inner_group_fails_atomically_and_names_group(self) -> None:
        data = pl.DataFrame(
            {
                "group": ["valid"] * 4 + ["invalid"] * 2,
                "x": ["a", "a", "b", "b", "a", "a"],
                "n": [10, 10, 10, 10, 10, 10],
            }
        )

        with self.assertRaisesRegex(ValueError, "group 'invalid' failed"):
            analyze_grouped_ggbarstats(data, "x", "group", counts="n")

    def test_grouped_public_function_rejects_unknown_keywords(self) -> None:
        data = pl.DataFrame({"group": ["a", "a", "b", "b"], "x": ["u", "v", "u", "v"]})
        with self.assertRaises(TypeError):
            grouped_ggbarstats(data, "x", "group", unknown=True)  # type: ignore[call-arg]
        with self.assertRaises(TypeError):
            grouped_ggpiestats(data, "x", "group", unknown=True)  # type: ignore[call-arg]


if __name__ == "__main__":
    unittest.main()
