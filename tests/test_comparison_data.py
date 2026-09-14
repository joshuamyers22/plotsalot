from __future__ import annotations

import unittest

import numpy as np
import polars as pl

from plotsalot.comparison_data import (
    ComparisonSample,
    RepeatedSample,
    select_comparison_sample,
    select_repeated_sample,
)


class ComparisonDataTests(unittest.TestCase):
    def test_between_boundary_orders_levels_owns_values_and_audits_nulls(self) -> None:
        data = pl.DataFrame(
            {
                "group": ["b", "a", "b", "a", "b", "a", None],
                "value": [2.0, 1.0, 5.0, 3.0, 8.0, 7.0, 99.0],
            }
        )
        sample = select_comparison_sample(data, "group", "value")

        self.assertEqual(sample.levels, ("a", "b"))
        np.testing.assert_array_equal(sample.values[0], [1.0, 3.0, 7.0])
        np.testing.assert_array_equal(sample.values[1], [2.0, 5.0, 8.0])
        self.assertEqual(sample.audit.input_rows, 7)
        self.assertEqual(sample.audit.analyzed_rows, 6)
        self.assertEqual(sample.audit.dropped_null_rows, 1)
        self.assertFalse(sample.values[0].flags.writeable)

    def test_enum_order_is_respected(self) -> None:
        data = pl.DataFrame(
            {
                "group": pl.Series(
                    ["middle", "first", "last"] * 2,
                    dtype=pl.Enum(["last", "middle", "first"]),
                ),
                "value": [1.0, 2.0, 3.0, 4.0, 6.0, 8.0],
            }
        )

        sample = select_comparison_sample(data, "group", "value")
        self.assertEqual(sample.levels, ("last", "middle", "first"))

    def test_between_boundary_rejects_invalid_samples(self) -> None:
        valid = pl.DataFrame(
            {"group": ["a", "a", "b", "b"], "value": [1.0, 2.0, 3.0, 5.0]}
        )
        operations = (
            lambda: select_comparison_sample(object(), "group", "value"),
            lambda: select_comparison_sample(valid, "", "value"),
            lambda: select_comparison_sample(valid, "group", "group"),
            lambda: select_comparison_sample(valid, "missing", "value"),
            lambda: select_comparison_sample(valid, "group", "missing"),
            lambda: select_comparison_sample(
                valid.with_columns(pl.col("value").cast(pl.String)),
                "group",
                "value",
            ),
            lambda: select_comparison_sample(valid, "group", "value", maximum_rows=3),
            lambda: select_comparison_sample(valid, "group", "value", maximum_levels=1),
            lambda: select_comparison_sample(
                pl.DataFrame(
                    {"group": ["a", "a", "b", "b"], "value": [1.0, 1.0, 2.0, 3.0]}
                ),
                "group",
                "value",
            ),
            lambda: select_comparison_sample(
                pl.DataFrame(
                    {
                        "group": ["a", "a", "b", "b"],
                        "value": [1.0, 2.0, 3.0, float("inf")],
                    }
                ),
                "group",
                "value",
            ),
        )
        for operation in operations:
            with (
                self.subTest(operation=operation),
                self.assertRaises((TypeError, ValueError)),
            ):
                operation()

    def test_repeated_boundary_builds_one_complete_block_and_audits_exclusions(
        self,
    ) -> None:
        data = pl.DataFrame(
            {
                "subject": [1, 1, 2, 2, 3, 3, 4, 5, 5, None],
                "condition": ["a", "b", "a", "b", "a", "b", "a", "a", "b", "a"],
                "value": [1.0, 2.0, 2.0, 4.0, 3.0, 7.0, 9.0, 5.0, None, 11.0],
            }
        )

        sample = select_repeated_sample(data, "condition", "value", "subject")
        self.assertEqual(sample.conditions, ("a", "b"))
        self.assertEqual(sample.subjects, (1, 2, 3))
        np.testing.assert_array_equal(
            sample.values, [[1.0, 2.0], [2.0, 4.0], [3.0, 7.0]]
        )
        self.assertFalse(sample.values.flags.writeable)
        self.assertEqual(sample.audit.input_rows, 10)
        self.assertEqual(sample.audit.analyzed_rows, 6)
        self.assertEqual(sample.audit.analyzed_subjects, 3)
        self.assertEqual(sample.audit.dropped_null_identity_rows, 1)
        self.assertEqual(sample.audit.dropped_null_value_rows, 1)
        self.assertEqual(sample.audit.excluded_incomplete_rows, 2)
        self.assertEqual(sample.audit.excluded_incomplete_subjects, 2)

    def test_repeated_boundary_rejects_duplicates_before_null_removal(self) -> None:
        data = pl.DataFrame(
            {
                "subject": [1, 1, 1, 2, 2, 3, 3],
                "condition": ["a", "a", "b", "a", "b", "a", "b"],
                "value": [1.0, None, 2.0, 2.0, 4.0, 3.0, 6.0],
            }
        )
        with self.assertRaisesRegex(
            ValueError, "duplicate subject-condition cell: subject=1, condition='a'"
        ):
            select_repeated_sample(data, "condition", "value", "subject")

    def test_repeated_boundary_rejects_invalid_contracts(self) -> None:
        valid = pl.DataFrame(
            {
                "subject": [1, 1, 2, 2, 3, 3],
                "condition": ["a", "b"] * 3,
                "value": [1.0, 2.0, 2.0, 4.0, 3.0, 7.0],
            }
        )
        operations = (
            lambda: select_repeated_sample(valid, "condition", "value", "condition"),
            lambda: select_repeated_sample(valid, "condition", "value", "missing"),
            lambda: select_repeated_sample(
                valid.with_columns(pl.col("value").cast(pl.String)),
                "condition",
                "value",
                "subject",
            ),
            lambda: select_repeated_sample(
                valid, "condition", "value", "subject", maximum_rows=5
            ),
            lambda: select_repeated_sample(
                valid, "condition", "value", "subject", minimum_subjects=2
            ),
            lambda: select_repeated_sample(
                valid.with_columns(
                    pl.when(pl.col("subject") == 3)
                    .then(None)
                    .otherwise(pl.col("value"))
                    .alias("value")
                ),
                "condition",
                "value",
                "subject",
            ),
            lambda: select_repeated_sample(
                valid.with_columns(
                    pl.when(pl.col("subject") == 3)
                    .then(float("nan"))
                    .otherwise(pl.col("value"))
                    .alias("value")
                ),
                "condition",
                "value",
                "subject",
            ),
        )
        for operation in operations:
            with (
                self.subTest(operation=operation),
                self.assertRaises((TypeError, ValueError)),
            ):
                operation()

    def test_owned_sample_records_reject_mismatches(self) -> None:
        between = select_comparison_sample(
            pl.DataFrame({"g": ["a", "a", "b", "b"], "y": [1.0, 2.0, 3.0, 5.0]}),
            "g",
            "y",
        )
        with self.assertRaises(ValueError):
            ComparisonSample(
                x=between.x,
                y=between.y,
                levels=between.levels,
                values=(between.values[0],),
                audit=between.audit,
            )

        repeated = select_repeated_sample(
            pl.DataFrame(
                {
                    "id": [1, 1, 2, 2, 3, 3],
                    "c": ["a", "b"] * 3,
                    "y": [1.0, 2.0, 2.0, 4.0, 3.0, 7.0],
                }
            ),
            "c",
            "y",
            "id",
        )
        with self.assertRaises(ValueError):
            RepeatedSample(
                x=repeated.x,
                y=repeated.y,
                subject_id=repeated.subject_id,
                conditions=repeated.conditions,
                subjects=repeated.subjects,
                values=repeated.values[:, :1],
                audit=repeated.audit,
            )


if __name__ == "__main__":
    unittest.main()
