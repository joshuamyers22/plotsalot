from __future__ import annotations

import json
import math
import unittest
from dataclasses import replace
from pathlib import Path
from typing import cast

import polars as pl

from plotsalot import analyze_categorical
from plotsalot.categorical_analysis import CategoricalAnalysis
from plotsalot.result import ScalarIdentity


def _two_way_counts() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "x": ["a", "a", "b", "b", "c", "c"],
            "y": ["u", "v", "u", "v", "u", "v"],
            "n": [30, 10, 15, 25, 10, 30],
        }
    )


class CategoricalAnalysisTests(unittest.TestCase):
    def test_one_way_goodness_of_fit_is_analytic_and_reconciled(self) -> None:
        data = pl.DataFrame({"x": ["a", "b", "c"], "n": [20, 30, 50]})

        analysis = analyze_categorical(data, "x", counts="n")
        result = analysis.result

        expected = 100.0 / 3.0
        statistic = sum((value - expected) ** 2 / expected for value in (20, 30, 50))
        self.assertEqual(result.design, "one_way")
        self.assertEqual(result.omnibus.name, "pearson_chi_square_goodness_of_fit")
        self.assertAlmostEqual(result.omnibus.statistic, statistic, places=12)
        self.assertEqual(result.omnibus.df, 2.0)
        self.assertAlmostEqual(
            result.effect.value, math.sqrt(statistic / 100), places=12
        )
        self.assertLessEqual(result.effect.interval.low, result.effect.value)
        self.assertGreaterEqual(result.effect.interval.high, result.effect.value)
        self.assertEqual(result.row_totals, (20, 30, 50))
        self.assertAlmostEqual(
            sum(cell.contribution or 0.0 for cell in result.cells), statistic, places=12
        )

    def test_custom_ratio_is_exact_and_changes_the_null(self) -> None:
        data = pl.DataFrame({"x": ["a", "b", "c"], "n": [20, 30, 50]})

        result = analyze_categorical(
            data, "x", counts="n", ratio={"a": 0.2, "b": 0.3, "c": 0.5}
        ).result

        self.assertEqual(result.ratio, (0.2, 0.3, 0.5))
        self.assertEqual(result.omnibus.statistic, 0.0)
        self.assertEqual(result.effect.value, 0.0)
        self.assertEqual(result.effect.interval.low, 0.0)

    def test_independence_pairwise_and_strata_are_complete_and_separate(self) -> None:
        result = analyze_categorical(_two_way_counts(), "x", "y", counts="n").result

        expected = ((55 / 3, 65 / 3),) * 3
        observed = ((30, 10), (15, 25), (10, 30))
        statistic = sum(
            (value - expected[row][column]) ** 2 / expected[row][column]
            for row, values in enumerate(observed)
            for column, value in enumerate(values)
        )
        self.assertEqual(result.design, "independent")
        self.assertAlmostEqual(result.omnibus.statistic, statistic, places=12)
        self.assertEqual(result.omnibus.df, 2.0)
        self.assertAlmostEqual(
            result.effect.value, math.sqrt(statistic / 120), places=12
        )
        self.assertEqual(
            tuple((item.left, item.right) for item in result.pairwise),
            (("a", "b"), ("a", "c"), ("b", "c")),
        )
        self.assertTrue(all(item.family == "pairwise" for item in result.pairwise))
        self.assertEqual(tuple(item.left for item in result.strata), ("u", "v"))
        self.assertTrue(all(item.family == "stratum" for item in result.strata))
        self.assertTrue(
            all(
                item.adjusted_p_value >= item.test.p_value
                for item in (*result.pairwise, *result.strata)
            )
        )

    def test_raw_and_weighted_analysis_have_statistical_equivalence(self) -> None:
        weighted = _two_way_counts()
        raw = pl.DataFrame(
            {
                "x": [
                    value
                    for x, count in zip(weighted["x"], weighted["n"], strict=True)
                    for value in [x] * count
                ],
                "y": [
                    value
                    for y, count in zip(weighted["y"], weighted["n"], strict=True)
                    for value in [y] * count
                ],
            }
        )

        aggregate_result = analyze_categorical(weighted, "x", "y", counts="n").result
        raw_result = analyze_categorical(raw, "x", "y").result

        self.assertEqual(aggregate_result.x_levels, raw_result.x_levels)
        self.assertEqual(aggregate_result.y_levels, raw_result.y_levels)
        self.assertEqual(aggregate_result.row_totals, raw_result.row_totals)
        self.assertEqual(aggregate_result.column_totals, raw_result.column_totals)
        self.assertEqual(aggregate_result.omnibus, raw_result.omnibus)
        self.assertEqual(aggregate_result.effect, raw_result.effect)
        self.assertEqual(aggregate_result.pairwise, raw_result.pairwise)
        self.assertEqual(aggregate_result.strata, raw_result.strata)

    def test_paired_path_is_exact_binomial_with_signed_effect(self) -> None:
        data = pl.DataFrame(
            {
                "x": ["no", "no", "yes", "yes"],
                "y": ["no", "yes", "no", "yes"],
                "n": [30, 5, 15, 40],
            }
        )

        result = analyze_categorical(
            data,
            "x",
            "y",
            counts="n",
            paired=True,
            proportion_test=False,
        ).result

        self.assertEqual(result.design, "paired")
        self.assertEqual(result.omnibus.name, "exact_binomial_paired")
        self.assertEqual(result.omnibus.statistic, 5.0)
        self.assertAlmostEqual(result.omnibus.p_value, 0.04138946533203125)
        self.assertEqual(result.effect.name, "cohen_g")
        self.assertAlmostEqual(result.effect.value, -0.25)
        self.assertLessEqual(result.effect.interval.low, -0.25)
        self.assertGreaterEqual(result.effect.interval.high, -0.25)
        self.assertIsNone(result.adequacy)
        self.assertEqual(result.pairwise, ())
        self.assertEqual(result.strata, ())

    def test_sparse_and_unsupported_paths_fail_explicitly(self) -> None:
        sparse = pl.DataFrame(
            {"x": ["a", "a", "b", "b"], "y": ["u", "v", "u", "v"], "n": [1, 0, 0, 1]}
        )
        paired_no_discordance = pl.DataFrame(
            {"x": ["a", "a", "b", "b"], "y": ["a", "b", "a", "b"], "n": [10, 0, 0, 10]}
        )
        valid = _two_way_counts()
        operations = (
            lambda: analyze_categorical(sparse, "x", "y", counts="n"),
            lambda: analyze_categorical(valid, "x", "y", counts="n", type="robust"),
            lambda: analyze_categorical(
                valid, "x", "y", counts="n", alternative="less"
            ),
            lambda: analyze_categorical(valid, "x", "y", counts="n", p_adjust="fdr"),
            lambda: analyze_categorical(
                valid, "x", "y", counts="n", ratio={"a": 0.5, "b": 0.5}
            ),
            lambda: analyze_categorical(valid, "x", "y", counts="n", paired=True),
            lambda: analyze_categorical(
                paired_no_discordance,
                "x",
                "y",
                counts="n",
                paired=True,
                proportion_test=False,
            ),
            lambda: analyze_categorical(
                valid, "x", "y", counts="n", paired=cast(bool, 1)
            ),
        )
        for operation in operations:
            with (
                self.subTest(operation=operation),
                self.assertRaises((TypeError, ValueError)),
            ):
                operation()

    def test_option_ratio_and_design_boundaries_are_explicit(self) -> None:
        one_way = pl.DataFrame({"x": ["a", "b", "c"], "n": [20, 30, 50]})
        independent = _two_way_counts()
        invalid_options = (
            lambda: analyze_categorical(
                one_way, "x", counts="n", conf_level=cast(float, True)
            ),
            lambda: analyze_categorical(one_way, "x", counts="n", conf_level=1.0),
            lambda: analyze_categorical(
                one_way, "x", counts="n", alpha=cast(float, True)
            ),
            lambda: analyze_categorical(one_way, "x", counts="n", alpha=0.0),
            lambda: analyze_categorical(
                one_way, "x", counts="n", pairwise_display="bad"
            ),
            lambda: analyze_categorical(
                one_way, "x", counts="n", maximum_labels=cast(int, True)
            ),
            lambda: analyze_categorical(one_way, "x", counts="n", maximum_labels=0),
            lambda: analyze_categorical(
                one_way, "x", counts="n", ratio={"a": 0.5, "b": 0.5}
            ),
            lambda: analyze_categorical(
                one_way,
                "x",
                counts="n",
                ratio=cast(
                    dict[ScalarIdentity, float],
                    {"a": "0.2", "b": 0.3, "c": 0.5},
                ),
            ),
            lambda: analyze_categorical(
                one_way, "x", counts="n", ratio={"a": -0.2, "b": 0.7, "c": 0.5}
            ),
            lambda: analyze_categorical(
                one_way, "x", counts="n", ratio={"a": 0.2, "b": 0.2, "c": 0.2}
            ),
            lambda: analyze_categorical(one_way, "x", counts="n", paired=True),
            lambda: analyze_categorical(
                independent,
                "x",
                "y",
                counts="n",
                paired=True,
                ratio={"a": 0.3, "b": 0.3, "c": 0.4},
                proportion_test=False,
            ),
            lambda: analyze_categorical(
                pl.DataFrame(
                    {
                        "x": ["a", "a", "b", "b"],
                        "y": ["a", "b", "a", "b"],
                        "n": [0, 5, 0, 5],
                    }
                ),
                "x",
                "y",
                counts="n",
                paired=True,
                proportion_test=False,
            ),
            lambda: analyze_categorical(
                independent,
                "x",
                "y",
                counts="n",
                maximum_labels=5,
            ),
        )
        for operation in invalid_options:
            with (
                self.subTest(operation=operation),
                self.assertRaises((TypeError, ValueError)),
            ):
                operation()

        no_adjustment = analyze_categorical(
            independent,
            "x",
            "y",
            counts="n",
            p_adjust="none",
            proportion_test=False,
        ).result
        self.assertIsNone(no_adjustment.ratio)
        self.assertEqual(no_adjustment.strata, ())
        self.assertTrue(
            all(
                item.adjusted_p_value == item.test.p_value
                for item in no_adjustment.pairwise
            )
        )

    def test_expected_count_rules_reject_sparse_generic_and_empty_margin_tables(
        self,
    ) -> None:
        generic_sparse = pl.DataFrame({"x": ["a", "b", "c"], "n": [1, 2, 3]})
        sparse_2x2 = pl.DataFrame(
            {
                "x": ["a", "a", "b", "b"],
                "y": ["u", "v", "u", "v"],
                "n": [4, 4, 4, 4],
            }
        )
        empty_margin = pl.DataFrame(
            {
                "x": ["a", "a", "b", "b"],
                "y": pl.Series(
                    ["u", "v", "u", "v"], dtype=pl.Enum(["u", "v", "empty"])
                ),
                "n": [10, 10, 10, 10],
            }
        )
        for data, y in ((generic_sparse, None), (sparse_2x2, "y"), (empty_margin, "y")):
            with self.subTest(y=y), self.assertRaises(ValueError):
                analyze_categorical(data, "x", y, counts="n")

    def test_result_is_json_safe_matches_schema_and_rejects_incoherence(self) -> None:
        analysis = analyze_categorical(_two_way_counts(), "x", "y", counts="n")
        result = analysis.result
        payload = result.to_dict()
        schema = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "schemas"
                / "categorical-result.schema.json"
            ).read_text(encoding="utf-8")
        )

        json.dumps(payload, allow_nan=False)
        self.assertEqual(set(payload), set(schema["required"]))
        invalid = (
            lambda: replace(result, analysis="unsupported"),
            lambda: replace(result, x_levels=("a", "a", "c")),
            lambda: replace(result, cells=result.cells[:-1]),
            lambda: replace(result, row_totals=(1, 2, 3)),
            lambda: replace(result, pairwise=result.pairwise[:-1]),
            lambda: replace(result, strata=()),
            lambda: replace(result, ratio=(0.4, 0.4, 0.4)),
            lambda: replace(result, conf_level=0.9),
            lambda: replace(result, warnings=("",)),
        )
        for operation in invalid:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()
        with self.assertRaises(ValueError):
            CategoricalAnalysis(analysis.table, replace(result, x="other"))


if __name__ == "__main__":
    unittest.main()
