from __future__ import annotations

import json
import math
import unittest
from typing import cast
from unittest.mock import patch

import numpy as np
import polars as pl

from plotsalot import (
    analyze_gghistostats,
    extract_caption,
    extract_stats,
    extract_subtitle,
    gghistostats,
    render_gghistostats,
)
from plotsalot.histogram_analysis import Alternative


class GgHistoStatsTests(unittest.TestCase):
    def test_one_sample_result_matches_analytic_fixture(self) -> None:
        data = pl.DataFrame({"value": [1.0, 2.0, 3.0, 4.0, 5.0]})

        plot = gghistostats(data, "value", test_value=0.0)
        result = extract_stats(plot)
        self.addCleanup(plot.figure.clear)

        self.assertEqual(result.schema_version, 1)
        self.assertEqual(result.sample.input_rows, 5)
        self.assertEqual(result.sample.analyzed_rows, 5)
        self.assertEqual(result.sample.dropped_null_rows, 0)
        self.assertAlmostEqual(result.estimate.value, 3.0, places=12)
        self.assertAlmostEqual(
            result.estimate.standard_deviation, math.sqrt(2.5), places=12
        )
        self.assertAlmostEqual(result.test.statistic, math.sqrt(18.0), places=12)
        self.assertEqual(result.test.df, 4.0)
        self.assertAlmostEqual(result.test.p_value, 0.013235599563682695, places=12)
        self.assertAlmostEqual(
            result.effect_size.value, 3.0 / math.sqrt(2.5), places=12
        )
        self.assertLess(result.interval.low, result.estimate.value)
        self.assertGreater(result.interval.high, result.estimate.value)

    def test_nulls_are_dropped_and_reconciled(self) -> None:
        data = pl.DataFrame({"value": [1.0, None, 2.0, 3.0]})

        plot = gghistostats(data, "value")
        self.addCleanup(plot.figure.clear)

        self.assertEqual(plot.result.sample.input_rows, 4)
        self.assertEqual(plot.result.sample.analyzed_rows, 3)
        self.assertEqual(plot.result.sample.dropped_null_rows, 1)
        self.assertIn("1 null row(s) excluded", extract_caption(plot))

    def test_result_is_json_serializable_and_annotations_are_attached(self) -> None:
        plot = gghistostats(pl.DataFrame({"x": [2.0, 3.0, 7.0]}), "x")
        self.addCleanup(plot.figure.clear)

        encoded = json.dumps(plot.result.to_dict(), allow_nan=False)

        self.assertIn('"schema_version": 1', encoded)
        self.assertIn("t(2)", extract_subtitle(plot))
        self.assertIn("main", plot.axes)
        self.assertEqual(len(plot.axes["main"].patches), 3)
        self.assertEqual(len(plot.axes["main"].lines), 2)

    def test_input_dataframe_is_not_mutated(self) -> None:
        data = pl.DataFrame({"value": [1.0, None, 3.0]})
        before = data.clone()

        plot = gghistostats(data, "value")
        self.addCleanup(plot.figure.clear)

        self.assertTrue(data.equals(before))

    def test_analysis_and_rendering_are_separate_and_reusable(self) -> None:
        data = pl.DataFrame({"value": [1.0, 2.0, 5.0]})

        with patch("matplotlib.figure.Figure", side_effect=AssertionError):
            analysis = analyze_gghistostats(data, "value")

        first_plot = render_gghistostats(analysis, title="First")
        second_plot = render_gghistostats(analysis, binwidth=1.0, title="Second")
        self.addCleanup(first_plot.figure.clear)
        self.addCleanup(second_plot.figure.clear)

        self.assertIs(first_plot.result, analysis.result)
        self.assertIs(second_plot.result, analysis.result)
        self.assertEqual(first_plot.title, "First")
        self.assertEqual(second_plot.title, "Second")
        self.assertIsNot(first_plot.figure, second_plot.figure)

    def test_rejects_invalid_inputs(self) -> None:
        valid = pl.DataFrame({"value": [1.0, 2.0, 3.0]})
        cases = (
            (lambda: gghistostats(valid, "missing"), ValueError),
            (
                lambda: gghistostats(pl.DataFrame({"value": ["a", "b"]}), "value"),
                TypeError,
            ),
            (lambda: gghistostats(valid, "value", conf_level=1.0), ValueError),
            (
                lambda: gghistostats(
                    valid, "value", alternative=cast(Alternative, "invalid")
                ),
                ValueError,
            ),
            (lambda: gghistostats(valid, "value", test_value=np.nan), ValueError),
            (lambda: gghistostats(valid, "value", binwidth=0.0), ValueError),
            (
                lambda: gghistostats(pl.DataFrame({"value": [1.0, np.inf]}), "value"),
                ValueError,
            ),
            (
                lambda: gghistostats(pl.DataFrame({"value": [1.0, 1.0, 1.0]}), "value"),
                ValueError,
            ),
        )

        for operation, exception in cases:
            with self.subTest(exception=exception), self.assertRaises(exception):
                operation()
