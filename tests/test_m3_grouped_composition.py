from __future__ import annotations

import json
import unittest
from dataclasses import replace
from pathlib import Path

import matplotlib as mpl
import polars as pl

from plotsalot import (
    StatsTheme,
    analyze_grouped_ggbetweenstats,
    analyze_grouped_ggwithinstats,
    combine_plots,
    extract_caption,
    extract_stats,
    extract_subtitle,
    ggbetweenstats,
    grouped_ggbetweenstats,
    grouped_ggwithinstats,
    theme_ggstatsplot,
)


class M3GroupedAndCompositionTests(unittest.TestCase):
    def _grouped_between_data(self) -> pl.DataFrame:
        return pl.DataFrame(
            {
                "outer": ["x"] * 6 + ["y"] * 6 + [None],
                "group": ["a"] * 3 + ["b"] * 3 + ["a"] * 3 + ["b"] * 3 + ["a"],
                "value": [
                    1.0,
                    2.0,
                    4.0,
                    3.0,
                    5.0,
                    8.0,
                    2.0,
                    3.0,
                    6.0,
                    5.0,
                    7.0,
                    9.0,
                    99.0,
                ],
            }
        )

    def test_grouped_between_is_atomic_and_retains_scope(self) -> None:
        analysis = analyze_grouped_ggbetweenstats(
            self._grouped_between_data(), "group", "value", "outer"
        )
        self.assertEqual(tuple(item.group for item in analysis.groups), ("x", "y"))
        self.assertEqual(
            analysis.result.correction_scope,
            "within_each_comparison_result_none_across_outer_groups",
        )
        self.assertEqual(analysis.result.sample.dropped_null_group_rows, 1)
        json.dumps(analysis.result.to_dict(), allow_nan=False)

        invalid = self._grouped_between_data().with_columns(
            pl.when(pl.col("outer") == "y")
            .then(pl.lit(1.0))
            .otherwise(pl.col("value"))
            .alias("value")
        )
        with self.assertRaisesRegex(ValueError, "group 'y' failed"):
            analyze_grouped_ggbetweenstats(invalid, "group", "value", "outer")

    def test_grouped_repeated_scopes_subjects_within_outer_groups(self) -> None:
        data = pl.DataFrame(
            {
                "outer": ["x"] * 6 + ["y"] * 6,
                "subject": [1, 1, 2, 2, 3, 3] * 2,
                "condition": ["a", "b"] * 6,
                "value": [1.0, 2.0, 2.0, 4.0, 4.0, 3.0, 2.0, 5.0, 3.0, 4.0, 5.0, 9.0],
            }
        )
        analysis = analyze_grouped_ggwithinstats(
            data,
            "condition",
            "value",
            "outer",
            subject_id="subject",
        )
        self.assertEqual(len(analysis.groups), 2)
        self.assertEqual(
            analysis.result.correction_scope,
            "within_each_repeated_result_none_across_outer_groups",
        )
        plot = grouped_ggwithinstats(
            data,
            "condition",
            "value",
            "outer",
            subject_id="subject",
        )
        for item in plot.plots:
            self.addCleanup(item.figure.clear)
        self.assertEqual(len(plot.plots), 2)

    def test_composition_flattens_grouped_plots_and_preserves_result_identity(
        self,
    ) -> None:
        grouped = grouped_ggbetweenstats(
            self._grouped_between_data(), "group", "value", "outer"
        )
        single = ggbetweenstats(
            pl.DataFrame({"g": ["a", "a", "b", "b"], "y": [1.0, 3.0, 2.0, 6.0]}),
            "g",
            "y",
        )
        self.addCleanup(single.figure.clear)
        for item in grouped.plots:
            self.addCleanup(item.figure.clear)
        original_canvases = tuple(item.figure.canvas for item in grouped.plots)

        composed = combine_plots(
            [grouped, single],
            columns=2,
            title="Comparison dashboard",
            caption="retained results",
            x_label="Shared x",
            y_label="Shared y",
            panel_tags="A",
        )
        self.addCleanup(composed.figure.clear)
        self.assertEqual(len(composed.result.panels), 3)
        self.assertEqual(tuple(composed.axes), ("panel_1", "panel_2", "panel_3"))
        self.assertIs(composed.result.panels[0].result, grouped.plots[0].result)
        self.assertIs(composed.result.panels[2].result, single.result)
        self.assertEqual(composed.result.panels[0].group, "x")
        self.assertEqual(composed.result.panels[1].group, "y")
        self.assertEqual(composed.result.panels[2].source_index, 1)
        self.assertEqual(composed.result.x_label, "Shared x")
        self.assertEqual(composed.result.y_label, "Shared y")
        self.assertEqual(
            tuple(panel.tag for panel in composed.result.panels), ("A", "B", "C")
        )
        self.assertEqual(composed.title, "Comparison dashboard")
        self.assertIs(extract_stats(composed), composed.result)
        self.assertEqual(extract_subtitle(composed), "")
        self.assertEqual(extract_caption(composed), "retained results")
        self.assertEqual(
            tuple(item.figure.canvas for item in grouped.plots), original_canvases
        )
        json.dumps(composed.result.to_dict(), allow_nan=False)

        schema = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "schemas"
                / "composition-result.schema.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(set(composed.result.to_dict()), set(schema["required"]))

    def test_composition_fails_before_returning_partial_output(self) -> None:
        plot = ggbetweenstats(
            pl.DataFrame({"g": ["a", "a", "b", "b"], "y": [1.0, 3.0, 2.0, 6.0]}),
            "g",
            "y",
        )
        self.addCleanup(plot.figure.clear)
        operations = (
            lambda: combine_plots([]),
            lambda: combine_plots([plot, object()]),
            lambda: combine_plots([plot], rows=0),
            lambda: combine_plots([plot, plot], rows=1, columns=1),
            lambda: combine_plots([plot], guides="collect"),
            lambda: combine_plots([plot], title=""),
            lambda: combine_plots([plot], x_label=""),
            lambda: combine_plots([plot], y_label=""),
            lambda: combine_plots([plot], panel_tags="roman"),
            lambda: combine_plots([plot], maximum_panels=0),
            lambda: combine_plots([plot, plot], maximum_panels=1),
        )
        for operation in operations:
            with (
                self.subTest(operation=operation),
                self.assertRaises((TypeError, ValueError)),
            ):
                operation()

    def test_theme_is_local_and_validated(self) -> None:
        before = dict(mpl.rcParams)
        theme = replace(theme_ggstatsplot(), accent_color="#123456")
        self.assertIsInstance(theme, StatsTheme)
        plot = ggbetweenstats(
            pl.DataFrame({"g": ["a", "a", "b", "b"], "y": [1.0, 3.0, 2.0, 6.0]}),
            "g",
            "y",
            theme=theme,
        )
        self.addCleanup(plot.figure.clear)
        self.assertEqual(dict(mpl.rcParams), before)
        self.assertFalse(plot.axes["main"].spines["top"].get_visible())
        mean_artist = plot.axes["main"].lines[-1]
        self.assertEqual(mean_artist.get_color(), "#123456")

        with self.assertRaises(ValueError):
            replace(theme, grid_alpha=2.0)
        with self.assertRaises(ValueError):
            replace(theme, title_size=0.0)
        with self.assertRaises(ValueError):
            replace(theme, accent_color="")


if __name__ == "__main__":
    unittest.main()
