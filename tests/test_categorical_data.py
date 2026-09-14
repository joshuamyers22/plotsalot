from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import date
from typing import cast

import numpy as np
import polars as pl

from plotsalot.categorical_data import select_categorical_table


class CategoricalDataTests(unittest.TestCase):
    def test_aggregate_table_is_ordered_owned_and_audited(self) -> None:
        data = pl.DataFrame(
            {
                "x": ["b", "a", "b", None, "a", "b", "a"],
                "y": ["v", "u", "u", "u", None, "v", "u"],
                "n": [20, 10, 15, 99, 99, None, 5],
            }
        )

        table = select_categorical_table(data, "x", "y", counts="n")

        self.assertEqual(table.x_levels, ("a", "b"))
        self.assertEqual(table.y_levels, ("u", "v"))
        np.testing.assert_array_equal(table.observed, [[15, 0], [15, 20]])
        self.assertFalse(table.observed.flags.writeable)
        self.assertEqual(table.audit.input_rows, 7)
        self.assertEqual(table.audit.analyzed_rows, 4)
        self.assertEqual(table.audit.weighted_total, 50)
        self.assertEqual(table.audit.dropped_null_x_rows, 1)
        self.assertEqual(table.audit.dropped_null_y_rows, 1)
        self.assertEqual(table.audit.dropped_null_count_rows, 1)

    def test_raw_and_aggregate_inputs_build_the_same_table(self) -> None:
        aggregate = pl.DataFrame(
            {
                "x": ["a", "a", "b", "b"],
                "y": ["u", "v", "u", "v"],
                "n": [10, 20, 30, 40],
            }
        )
        raw = pl.DataFrame(
            {
                "x": ["a"] * 30 + ["b"] * 70,
                "y": ["u"] * 10 + ["v"] * 20 + ["u"] * 30 + ["v"] * 40,
            }
        )

        weighted = select_categorical_table(aggregate, "x", "y", counts="n")
        expanded = select_categorical_table(raw, "x", "y")

        self.assertEqual(weighted.x_levels, expanded.x_levels)
        self.assertEqual(weighted.y_levels, expanded.y_levels)
        np.testing.assert_array_equal(weighted.observed, expanded.observed)
        self.assertEqual(weighted.audit.weighted_total, expanded.audit.weighted_total)

    def test_enum_declared_order_and_zero_count_categories_are_preserved(self) -> None:
        data = pl.DataFrame(
            {
                "x": pl.Series(
                    ["middle", "first"], dtype=pl.Enum(["last", "middle", "first"])
                ),
                "n": [0, 20],
            }
        )

        table = select_categorical_table(data, "x", counts="n")

        self.assertEqual(table.x_levels, ("last", "middle", "first"))
        np.testing.assert_array_equal(table.observed[:, 0], [0, 0, 20])

        categorical = select_categorical_table(
            pl.DataFrame(
                {
                    "x": pl.Series(["middle", "first", "last"], dtype=pl.Categorical),
                    "n": [10, 20, 30],
                }
            ),
            "x",
            counts="n",
        )
        self.assertEqual(categorical.x_levels, ("first", "last", "middle"))
        reordered = select_categorical_table(
            pl.DataFrame(
                {
                    "x": pl.Series(["last", "first", "middle"], dtype=pl.Categorical),
                    "n": [30, 20, 10],
                }
            ),
            "x",
            counts="n",
        )
        self.assertEqual(reordered.x_levels, categorical.x_levels)
        np.testing.assert_array_equal(reordered.observed, categorical.observed)

    def test_invalid_counts_categories_and_limits_fail_before_inference(self) -> None:
        valid = pl.DataFrame({"x": ["a", "b"], "n": [10, 10]})
        operations = (
            lambda: select_categorical_table(object(), "x"),
            lambda: select_categorical_table(valid, "", counts="n"),
            lambda: select_categorical_table(valid, "x", counts="x"),
            lambda: select_categorical_table(valid, "missing", counts="n"),
            lambda: select_categorical_table(
                valid.with_columns(pl.col("n").cast(pl.Float64)), "x", counts="n"
            ),
            lambda: select_categorical_table(
                pl.DataFrame({"x": ["a", "b"], "n": [10, -1]}),
                "x",
                counts="n",
            ),
            lambda: select_categorical_table(
                pl.DataFrame({"x": ["a", "b"], "n": [0, 0]}),
                "x",
                counts="n",
            ),
            lambda: select_categorical_table(valid, "x", counts="n", maximum_rows=1),
            lambda: select_categorical_table(
                valid, "x", counts="n", maximum_total_count=19
            ),
            lambda: select_categorical_table(
                valid, "x", counts="n", maximum_levels=cast(int, True)
            ),
            lambda: select_categorical_table(
                valid,
                "x",
                counts="n",
                maximum_total_count=np.iinfo(np.int64).max + 1,
            ),
        )
        for operation in operations:
            with (
                self.subTest(operation=operation),
                self.assertRaises((TypeError, ValueError)),
            ):
                operation()

    def test_scalar_identity_paths_are_deterministic_and_restricted(self) -> None:
        boolean = select_categorical_table(
            pl.DataFrame({"x": [True, False], "n": [10, 10]}), "x", counts="n"
        )
        integer = select_categorical_table(
            pl.DataFrame({"x": [2, 1], "n": [10, 10]}), "x", counts="n"
        )
        floating = select_categorical_table(
            pl.DataFrame({"x": [2.5, 1.5], "n": [10, 10]}), "x", counts="n"
        )
        self.assertEqual(boolean.x_levels, (False, True))
        self.assertEqual(integer.x_levels, (1, 2))
        self.assertEqual(floating.x_levels, (1.5, 2.5))

        invalid = (
            pl.DataFrame({"x": ["", "a"], "n": [10, 10]}),
            pl.DataFrame({"x": [1.0, float("nan")], "n": [10, 10]}),
            pl.DataFrame({"x": [date(2026, 1, 1), date(2026, 1, 2)], "n": [10, 10]}),
        )
        for data in invalid:
            with self.subTest(data=data), self.assertRaises((TypeError, ValueError)):
                select_categorical_table(data, "x", counts="n")

    def test_table_record_and_additional_boundary_failures_are_guarded(self) -> None:
        table = select_categorical_table(
            pl.DataFrame({"x": ["a", "b"], "n": [10, 10]}), "x", counts="n"
        )
        invalid_tables = (
            lambda: replace(table, x=""),
            lambda: replace(table, x_levels=("a",)),
            lambda: replace(table, y_levels=("u", "v")),
            lambda: replace(table, y="y", y_levels=("u",)),
            lambda: replace(table, observed=np.array([10, 10], dtype=np.int64)),
            lambda: replace(table, observed=np.array([[10.0], [10.0]])),
            lambda: replace(table, observed=np.array([[-1], [21]], dtype=np.int64)),
            lambda: replace(
                table,
                audit=replace(table.audit, weighted_total=19),
            ),
        )
        for operation in invalid_tables:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

        boundary_operations = (
            lambda: select_categorical_table(
                pl.DataFrame({"x": ["a", "b"], "n": [True, False]}),
                "x",
                counts="n",
            ),
            lambda: select_categorical_table(
                pl.DataFrame({"x": [None, None], "n": [10, 10]}),
                "x",
                counts="n",
            ),
            lambda: select_categorical_table(
                pl.DataFrame({"x": ["a", "b"], "y": ["u", "u"], "n": [10, 10]}),
                "x",
                "y",
                counts="n",
            ),
            lambda: select_categorical_table(
                pl.DataFrame(
                    {
                        "x": ["a", "a", "b", "b", "c", "c"],
                        "y": ["u", "v", "u", "v", "u", "v"],
                        "n": [10] * 6,
                    }
                ),
                "x",
                "y",
                counts="n",
                maximum_cells=5,
            ),
            lambda: select_categorical_table(
                pl.DataFrame({"x": ["a", "b"], "n": [10, 10]}),
                "x",
                counts="n",
                maximum_levels=21,
            ),
        )
        for operation in boundary_operations:
            with (
                self.subTest(operation=operation),
                self.assertRaises((TypeError, ValueError)),
            ):
                operation()


if __name__ == "__main__":
    unittest.main()
