from __future__ import annotations

import json
import unittest
from dataclasses import replace
from datetime import date
from pathlib import Path

import polars as pl

from plotsalot import (
    GroupedAnalysis,
    analyze_grouped_ggcorrmat,
    analyze_grouped_ggdotplotstats,
    analyze_grouped_gghistostats,
    analyze_grouped_ggscatterstats,
    extract_caption,
    extract_stats,
    extract_subtitle,
    grouped_ggcorrmat,
    grouped_ggdotplotstats,
    grouped_gghistostats,
    grouped_ggscatterstats,
)
from plotsalot.grouped import GroupAnalysisItem
from plotsalot.result import GroupResultItem


class GroupedAnalysisTests(unittest.TestCase):
    def test_histogram_order_null_audit_and_extraction_are_stable(self) -> None:
        data = pl.DataFrame(
            {
                "value": [4.0, 1.0, 5.0, 2.0, 99.0],
                "group": ["second", "first", "second", "first", None],
            }
        )

        analysis = analyze_grouped_gghistostats(data, "value", "group")
        self.assertEqual(
            tuple(item.group for item in analysis.groups), ("second", "first")
        )
        self.assertEqual(analysis.result.sample.input_rows, 5)
        self.assertEqual(analysis.result.sample.analyzed_rows, 4)
        self.assertEqual(analysis.result.sample.dropped_null_group_rows, 1)
        self.assertEqual(analysis.result.correction_scope, "none_across_groups")
        self.assertEqual(analysis.result.limits.maximum_groups, 20)
        json.dumps(analysis.result.to_dict(), allow_nan=False)

        plot = grouped_gghistostats(data, "value", "group", title="By cohort")
        for item in plot.plots:
            self.addCleanup(item.figure.clear)
        self.assertIs(extract_stats(plot), plot.result)
        self.assertEqual(plot.title, "By cohort")
        self.assertIn("2 group(s)", extract_subtitle(plot))
        self.assertIn("1 null group row(s)", extract_caption(plot))
        self.assertEqual(len(plot.plots), 2)

    def test_each_grouped_surface_has_a_typed_result_and_plot(self) -> None:
        data = pl.DataFrame(
            {
                "x": [1.0, 2.0, 3.0, 4.0, 2.0, 3.0, 4.0, 6.0],
                "y": [1.0, 3.0, 2.0, 5.0, 6.0, 3.0, 5.0, 1.0],
                "label": ["low", "low", "high", "high"] * 2,
                "group": ["a"] * 4 + ["b"] * 4,
            }
        )

        dot_analysis = analyze_grouped_ggdotplotstats(data, "x", "label", "group")
        scatter_analysis = analyze_grouped_ggscatterstats(data, "x", "y", "group")
        matrix_analysis = analyze_grouped_ggcorrmat(
            data, ("x", "y"), "group", p_adjust="none"
        )
        self.assertEqual(
            dot_analysis.result.analysis, "grouped_ggdotplotstats_one_sample_parametric"
        )
        self.assertEqual(
            scatter_analysis.result.analysis, "grouped_ggscatterstats_pearson"
        )
        self.assertEqual(matrix_analysis.result.correction_scope, "within_group_matrix")
        for result in (
            dot_analysis.result,
            scatter_analysis.result,
            matrix_analysis.result,
        ):
            json.dumps(result.to_dict(), allow_nan=False)

        plots = (
            grouped_ggdotplotstats(data, "x", "label", "group"),
            grouped_ggscatterstats(data, "x", "y", "group"),
            grouped_ggcorrmat(data, ("x", "y"), "group", p_adjust="none"),
        )
        for plot in plots:
            self.assertEqual(len(plot.plots), 2)
            for item in plot.plots:
                self.addCleanup(item.figure.clear)

    def test_grouped_analysis_is_atomic_and_names_the_invalid_group(self) -> None:
        data = pl.DataFrame(
            {
                "value": [1.0, 2.0, 3.0, 7.0, 7.0],
                "group": ["valid", "valid", "valid", "invalid", "invalid"],
            }
        )

        with self.assertRaisesRegex(ValueError, "group 'invalid' failed"):
            analyze_grouped_gghistostats(data, "value", "group")

    def test_grouping_boundary_rejects_invalid_or_oversized_inputs(self) -> None:
        valid = pl.DataFrame(
            {"value": [1.0, 2.0, 3.0, 4.0], "group": ["a", "a", "b", "b"]}
        )
        operations = (
            lambda: analyze_grouped_gghistostats(object(), "value", "group"),
            lambda: analyze_grouped_gghistostats(valid, "value", "missing"),
            lambda: analyze_grouped_gghistostats(
                valid, "value", "group", maximum_rows=3
            ),
            lambda: analyze_grouped_gghistostats(
                valid, "value", "group", maximum_groups=1
            ),
            lambda: analyze_grouped_gghistostats(
                valid, "value", "group", maximum_groups=0
            ),
            lambda: analyze_grouped_gghistostats(
                pl.DataFrame({"value": [1.0, 2.0], "group": [None, None]}),
                "value",
                "group",
            ),
            lambda: analyze_grouped_gghistostats(
                pl.DataFrame({"value": [1.0, 2.0], "group": ["", ""]}),
                "value",
                "group",
            ),
            lambda: analyze_grouped_gghistostats(
                pl.DataFrame(
                    {
                        "value": [1.0, 2.0],
                        "group": [date(2026, 1, 1), date(2026, 1, 1)],
                    }
                ),
                "value",
                "group",
            ),
        )
        for operation in operations:
            with (
                self.subTest(operation=operation),
                self.assertRaises((TypeError, ValueError)),
            ):
                operation()

    def test_numeric_group_identity_keeps_its_json_scalar_type(self) -> None:
        result = analyze_grouped_gghistostats(
            pl.DataFrame({"value": [1.0, 2.0, 3.0, 4.0], "group": [2, 2, 1, 1]}),
            "value",
            "group",
        ).result

        self.assertEqual(tuple(item.group for item in result.groups), (2, 1))
        self.assertIsInstance(result.groups[0].group, int)

    def test_grouped_result_schema_and_record_guards(self) -> None:
        analysis = analyze_grouped_gghistostats(
            pl.DataFrame(
                {"value": [1.0, 2.0, 3.0, 4.0], "group": ["a", "a", "b", "b"]}
            ),
            "value",
            "group",
        )
        result = analysis.result
        schema = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "schemas"
                / "grouped-result.schema.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(set(result.to_dict()), set(schema["required"]))

        with self.assertRaises(ValueError):
            replace(result.sample, input_rows=-1)
        with self.assertRaises(ValueError):
            replace(result.sample, input_rows=result.sample.input_rows + 1)
        with self.assertRaises(ValueError):
            GroupResultItem(group="", result=result.groups[0].result)
        with self.assertRaises(ValueError):
            GroupResultItem(group=float("nan"), result=result.groups[0].result)
        with self.assertRaises(ValueError):
            GroupAnalysisItem(group="", analysis=analysis.groups[0].analysis)
        with self.assertRaises(ValueError):
            GroupAnalysisItem(group=float("inf"), analysis=analysis.groups[0].analysis)

        invalid_results = (
            lambda: replace(result, schema_version=2),
            lambda: replace(result, analysis="unsupported"),
            lambda: replace(result, group_column=""),
            lambda: replace(result, groups=()),
            lambda: replace(result, groups=(result.groups[0], result.groups[0])),
            lambda: replace(result, correction_scope="global"),
            lambda: replace(result, warnings=("",)),
        )
        for operation in invalid_results:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

    def test_grouped_analysis_rejects_result_identity_mismatch(self) -> None:
        analysis = analyze_grouped_gghistostats(
            pl.DataFrame(
                {"value": [1.0, 2.0, 3.0, 4.0], "group": ["a", "a", "b", "b"]}
            ),
            "value",
            "group",
        )

        with self.assertRaises(ValueError):
            GroupedAnalysis(groups=(), result=analysis.result)
        with self.assertRaises(ValueError):
            GroupedAnalysis(
                groups=analysis.groups,
                result=replace(
                    analysis.result,
                    groups=tuple(reversed(analysis.result.groups)),
                ),
            )


if __name__ == "__main__":
    unittest.main()
