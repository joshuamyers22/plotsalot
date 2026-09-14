from __future__ import annotations

import json
import math
import unittest
from dataclasses import replace

import numpy as np
import polars as pl

from plotsalot import (
    analyze_ggcorrmat,
    analyze_ggscatterstats,
    ggcorrmat,
    ggscatterstats,
    render_ggcorrmat,
    render_ggscatterstats,
)
from plotsalot.correlation_analysis import (
    CorrelationAnalysis,
    CorrelationMatrixAnalysis,
)


class CorrelationTests(unittest.TestCase):
    def test_pearson_result_matches_analytic_case(self) -> None:
        analysis = analyze_ggscatterstats(
            pl.DataFrame({"x": [1.0, 2.0, 3.0, 4.0], "y": [1.0, 3.0, 2.0, 4.0]}),
            "x",
            "y",
        )
        result = analysis.result

        self.assertAlmostEqual(result.estimate, 0.8, places=12)
        self.assertAlmostEqual(
            result.test.statistic or 0.0, math.sqrt(32 / 9), places=12
        )
        self.assertAlmostEqual(result.test.p_value, 0.2, places=12)
        self.assertEqual(result.test.df, 2)
        self.assertEqual(result.sample.analyzed_rows, 4)
        self.assertLess(result.interval.low, result.estimate)
        self.assertGreater(result.interval.high, result.estimate)
        json.dumps(result.to_dict(), allow_nan=False)

    def test_pairwise_nulls_and_perfect_correlation_are_explicit(self) -> None:
        result = analyze_ggscatterstats(
            pl.DataFrame(
                {
                    "x": [1.0, 2.0, None, 3.0, 4.0],
                    "y": [2.0, 4.0, 20.0, 6.0, 8.0],
                }
            ),
            "x",
            "y",
        ).result

        self.assertEqual(result.sample.input_rows, 5)
        self.assertEqual(result.sample.analyzed_rows, 4)
        self.assertEqual(result.sample.dropped_null_rows, 1)
        self.assertEqual(result.estimate, 1.0)
        self.assertIsNone(result.test.statistic)
        self.assertEqual(result.test.p_value, 0.0)
        self.assertEqual((result.interval.low, result.interval.high), (1.0, 1.0))

    def test_scatter_rendering_uses_retained_pairs(self) -> None:
        data = pl.DataFrame({"x": [1.0, 2.0, 3.0, 4.0], "y": [4.0, 1.0, 3.0, 2.0]})
        analysis = analyze_ggscatterstats(data, "x", "y")
        plot = render_ggscatterstats(analysis)
        convenience = ggscatterstats(data, "x", "y", title="Custom")
        self.addCleanup(plot.figure.clear)
        self.addCleanup(convenience.figure.clear)

        self.assertEqual(len(plot.axes["main"].collections), 1)
        self.assertEqual(analysis.result.sample.analyzed_rows, 4)
        self.assertIn("Pearson r", plot.subtitle)
        self.assertEqual(convenience.title, "Custom")

    def test_scatter_renderer_formats_only_the_supplied_typed_result(self) -> None:
        analysis = analyze_ggscatterstats(
            pl.DataFrame({"x": [1.0, 2.0, 3.0, 4.0], "y": [4.0, 1.0, 3.0, 2.0]}),
            "x",
            "y",
        )
        supplied_result = replace(
            analysis.result,
            estimate=0.25,
            test=replace(analysis.result.test, statistic=0.75, p_value=0.5),
            interval=replace(analysis.result.interval, low=-0.1, high=0.5),
        )
        plot = render_ggscatterstats(
            CorrelationAnalysis(sample=analysis.sample, result=supplied_result)
        )
        self.addCleanup(plot.figure.clear)

        self.assertIn("t(2) = 0.75", plot.subtitle)
        self.assertIn("p = 0.500", plot.subtitle)
        self.assertIn("Pearson r = 0.25", plot.subtitle)
        self.assertIn("Fisher CI [-0.10, 0.50]", plot.caption)

    def test_matrix_is_symmetric_and_holm_adjusted(self) -> None:
        data = pl.DataFrame(
            {
                "a": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
                "b": [1.0, 2.0, 4.0, 3.0, 5.0, 7.0],
                "c": [6.0, 5.0, 4.0, 3.0, 2.0, 1.0],
            }
        )
        analysis = analyze_ggcorrmat(data, ["a", "b", "c"])
        result = analysis.result
        cells = {(cell.x, cell.y): cell for cell in result.cells}

        self.assertEqual(len(cells), 9)
        self.assertEqual(cells[("a", "a")].estimate, 1.0)
        self.assertIsNone(cells[("a", "a")].p_value)
        self.assertEqual(cells[("a", "b")].estimate, cells[("b", "a")].estimate)
        self.assertEqual(
            cells[("a", "b")].adjusted_p_value,
            cells[("b", "a")].adjusted_p_value,
        )
        for cell in result.cells:
            if cell.adjusted_p_value is not None and cell.p_value is not None:
                self.assertGreaterEqual(cell.adjusted_p_value, cell.p_value)
        json.dumps(result.to_dict(), allow_nan=False)

        plot = ggcorrmat(data, ("a", "b", "c"))
        self.addCleanup(plot.figure.clear)
        self.assertEqual(len(plot.axes["main"].texts), 9)
        self.assertIn("Holm-adjusted p", plot.caption)

    def test_matrix_none_adjustment_and_pairwise_counts(self) -> None:
        result = analyze_ggcorrmat(
            pl.DataFrame(
                {
                    "a": [1.0, 2.0, 3.0, 4.0, 5.0],
                    "b": [1.0, 2.0, None, 4.0, 6.0],
                    "c": [5.0, 1.0, 2.0, 3.0, 4.0],
                }
            ),
            ["a", "b", "c"],
            p_adjust="none",
        ).result
        cells = {(cell.x, cell.y): cell for cell in result.cells}

        self.assertEqual(cells[("a", "b")].n_obs, 4)
        self.assertEqual(cells[("a", "c")].n_obs, 5)
        self.assertEqual(cells[("a", "b")].adjusted_p_value, cells[("a", "b")].p_value)
        plot = ggcorrmat(
            pl.DataFrame({"a": [1.0, 2.0, 3.0, 4.0], "b": [4.0, 2.0, 3.0, 1.0]}),
            ("a", "b"),
            p_adjust="none",
        )
        self.addCleanup(plot.figure.clear)
        self.assertIn("× = p >", plot.caption)

    def test_matrix_renderer_uses_supplied_cells_without_reanalysis(self) -> None:
        analysis = analyze_ggcorrmat(
            pl.DataFrame({"a": [1.0, 2.0, 3.0, 4.0], "b": [4.0, 2.0, 3.0, 1.0]}),
            ("a", "b"),
        )
        cells = tuple(
            replace(cell, estimate=0.25, significant=False)
            if cell.x != cell.y
            else cell
            for cell in analysis.result.cells
        )
        supplied = CorrelationMatrixAnalysis(
            result=replace(analysis.result, cells=cells)
        )
        supplied_plot = render_ggcorrmat(supplied)
        self.addCleanup(supplied_plot.figure.clear)
        labels = [text.get_text() for text in supplied_plot.axes["main"].texts]

        self.assertEqual(labels.count("0.25 ×"), 2)

    def test_invalid_correlation_inputs_fail(self) -> None:
        valid = pl.DataFrame({"x": [1.0, 2.0, 3.0, 4.0], "y": [4.0, 3.0, 1.0, 2.0]})
        operations = (
            lambda: analyze_ggscatterstats(valid, "x", "x"),
            lambda: analyze_ggscatterstats(valid.head(3), "x", "y"),
            lambda: analyze_ggscatterstats(
                pl.DataFrame({"x": [1.0] * 4, "y": [1.0, 2.0, 3.0, 4.0]}),
                "x",
                "y",
            ),
            lambda: analyze_ggscatterstats(
                pl.DataFrame({"x": [1.0, 2.0, 3.0, np.inf], "y": [1, 2, 3, 4]}),
                "x",
                "y",
            ),
            lambda: analyze_ggcorrmat(valid, ["x"]),
            lambda: analyze_ggcorrmat(valid, "xy"),  # type: ignore[arg-type]
            lambda: analyze_ggcorrmat(valid, ["x", ""]),
            lambda: analyze_ggcorrmat(valid, ["x", "x"]),
            lambda: analyze_ggcorrmat(valid, ["x", "y"], p_adjust="fdr"),
            lambda: analyze_ggcorrmat(valid, ["x", "y"], sig_level=0.0),
        )
        for operation in operations:
            with (
                self.subTest(operation=operation),
                self.assertRaises((TypeError, ValueError)),
            ):
                operation()


if __name__ == "__main__":
    unittest.main()
