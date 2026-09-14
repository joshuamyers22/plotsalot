from __future__ import annotations

import json
import unittest
from collections.abc import MutableMapping
from dataclasses import replace
from pathlib import Path
from typing import cast

import polars as pl
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from plotsalot import (
    HistogramAnalysis,
    PlotAnnotations,
    StatsPlot,
    analyze_gghistostats,
    extract_caption,
    extract_stats,
    extract_subtitle,
)


class ResultAndPlotContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.analysis = analyze_gghistostats(
            pl.DataFrame({"value": [1.0, 2.0, 4.0]}), "value"
        )

    def test_result_mapping_is_versioned_and_json_safe(self) -> None:
        payload = self.analysis.result.to_dict()

        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["analysis"], "gghistostats_one_sample_parametric")
        json.dumps(payload, allow_nan=False)

    def test_result_mapping_matches_the_checked_in_schema_shape(self) -> None:
        schema_path = (
            Path(__file__).resolve().parents[1]
            / "schemas"
            / "analysis-result.schema.json"
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        payload = self.analysis.result.to_dict()

        self.assertEqual(set(payload), set(schema["required"]))
        for field in ("sample", "estimate", "test", "interval", "effect_size"):
            self.assertEqual(
                set(payload[field]), set(schema["properties"][field]["required"])
            )

    def test_result_records_reject_invalid_serialized_states(self) -> None:
        result = self.analysis.result

        invalid_results = (
            lambda: replace(result.estimate, name=""),
            lambda: replace(result.estimate, value=float("inf")),
            lambda: replace(result.estimate, standard_deviation=0.0),
            lambda: replace(result.test, name=""),
            lambda: replace(result.test, alternative="unsupported"),
            lambda: replace(result.test, statistic=float("nan")),
            lambda: replace(result.test, df=0.0),
            lambda: replace(result.test, p_value=1.1),
            lambda: replace(result.interval, target=""),
            lambda: replace(result.interval, level=1.0),
            lambda: replace(result.interval, low=5.0, high=4.0),
            lambda: replace(result.effect_size, standardizer=""),
            lambda: replace(result.effect_size, value=float("nan")),
            lambda: replace(result, schema_version=2),
            lambda: replace(result, column=""),
            lambda: replace(result, analysis="unsupported"),
            lambda: replace(result, estimate=replace(result.estimate, name="median")),
            lambda: replace(result, test=replace(result.test, name="z_test")),
            lambda: replace(
                result,
                interval=replace(result.interval, low=result.estimate.value + 1.0),
            ),
            lambda: replace(result, warnings=("",)),
        )

        for operation in invalid_results:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

    def test_histogram_analysis_rejects_sample_result_mismatch(self) -> None:
        with self.assertRaises(ValueError):
            HistogramAnalysis(
                sample=self.analysis.sample,
                result=replace(self.analysis.result, column="other"),
            )
        with self.assertRaises(ValueError):
            HistogramAnalysis(
                sample=self.analysis.sample,
                result=replace(
                    self.analysis.result,
                    sample=replace(
                        self.analysis.result.sample,
                        input_rows=4,
                        dropped_null_rows=1,
                    ),
                ),
            )

    def test_core_contract_modules_do_not_import_pandas(self) -> None:
        package = Path(__file__).resolve().parents[1] / "src" / "plotsalot"

        for filename in ("result.py", "data.py", "histogram_analysis.py"):
            source = (package / filename).read_text(encoding="utf-8")
            self.assertNotIn("import pandas", source)
            self.assertNotIn("from pandas", source)
            self.assertNotIn("matplotlib", source)

    def test_plot_owns_named_axis_mapping_and_exposes_annotations(self) -> None:
        figure = Figure()
        self.addCleanup(figure.clear)
        axis = figure.subplots()
        caller_mapping = {"main": axis}
        annotations = PlotAnnotations(
            title="Distribution of value",
            subtitle="typed subtitle",
            caption="typed caption",
        )
        plot = StatsPlot(
            figure=figure,
            axes=caller_mapping,
            result=self.analysis.result,
            annotations=annotations,
        )

        caller_mapping.clear()
        self.assertIs(extract_stats(plot), self.analysis.result)
        self.assertEqual(extract_subtitle(plot), "typed subtitle")
        self.assertEqual(extract_caption(plot), "typed caption")
        self.assertEqual(plot.title, "Distribution of value")
        self.assertIn("main", plot.axes)

        immutable_axes = cast(MutableMapping[str, Axes], plot.axes)
        with self.assertRaises(TypeError):
            immutable_axes["other"] = axis

    def test_plot_rejects_empty_or_foreign_axes(self) -> None:
        figure = Figure()
        other_figure = Figure()
        self.addCleanup(figure.clear)
        self.addCleanup(other_figure.clear)
        annotations = PlotAnnotations(title="title", subtitle="sub", caption="cap")

        with self.assertRaises(ValueError):
            PlotAnnotations(title="", subtitle="sub", caption="cap")
        with self.assertRaises(ValueError):
            StatsPlot(
                figure=figure,
                axes={},
                result=self.analysis.result,
                annotations=annotations,
            )
        with self.assertRaises(ValueError):
            StatsPlot(
                figure=figure,
                axes={"": figure.subplots()},
                result=self.analysis.result,
                annotations=annotations,
            )
        with self.assertRaises(ValueError):
            StatsPlot(
                figure=figure,
                axes={"main": other_figure.subplots()},
                result=self.analysis.result,
                annotations=annotations,
            )


if __name__ == "__main__":
    unittest.main()
