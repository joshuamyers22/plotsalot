from __future__ import annotations

import unittest
from typing import Any, cast

import numpy as np
import polars as pl

from plotsalot import StudyEffectTable, select_study_effects


def _valid() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "term": ["study-a", "study-b", "study-c"],
            "estimate": [0.1, 0.2, 0.3],
            "standard_error": [0.05, 0.1, 0.2],
            "citation": ["A", "B", "C"],
        }
    )


class StudyEffectBoundaryTests(unittest.TestCase):
    def test_selection_is_owned_read_only_and_preserves_source_order(self) -> None:
        frame = _valid()

        table = select_study_effects(frame)

        self.assertEqual(table.terms, ("study-a", "study-b", "study-c"))
        self.assertEqual(table.estimates.dtype, np.dtype(np.float64))
        self.assertEqual(table.standard_errors.dtype, np.dtype(np.float64))
        self.assertFalse(table.estimates.flags.writeable)
        self.assertFalse(table.standard_errors.flags.writeable)
        np.testing.assert_array_equal(table.estimates, [0.1, 0.2, 0.3])
        with self.assertRaises(ValueError):
            table.estimates[0] = 99.0
        with self.assertRaises(ValueError):
            table.estimates.setflags(write=True)

    def test_additional_nonparticipating_columns_are_ignored(self) -> None:
        table = select_study_effects(_valid())

        self.assertFalse(hasattr(table, "citation"))

    def test_boundary_rejects_invalid_and_ambiguous_inputs(self) -> None:
        valid = _valid()
        cases = (
            lambda: select_study_effects(object()),
            lambda: select_study_effects(valid.drop("term")),
            lambda: select_study_effects(
                valid.with_columns(pl.lit(None).alias("term"))
            ),
            lambda: select_study_effects(
                valid.with_columns(pl.lit("study-a").alias("term"))
            ),
            lambda: select_study_effects(
                valid.with_columns(pl.Series("term", [1, 2, 3]))
            ),
            lambda: select_study_effects(
                valid.with_columns(pl.lit("bad").alias("estimate"))
            ),
            lambda: select_study_effects(
                valid.with_columns(pl.lit(float("inf")).alias("estimate"))
            ),
            lambda: select_study_effects(
                valid.with_columns(pl.lit(0.0).alias("standard_error"))
            ),
            lambda: select_study_effects(
                valid.with_columns(pl.lit(-0.1).alias("standard_error"))
            ),
            lambda: select_study_effects(valid.head(2)),
            lambda: select_study_effects(valid, maximum_studies=2),
            lambda: select_study_effects(valid, maximum_studies=1_001),
            lambda: select_study_effects(
                valid.with_columns(pl.lit(0.1).alias("p_value"))
            ),
        )
        for operation in cases:
            with (
                self.subTest(operation=operation),
                self.assertRaises((TypeError, ValueError)),
            ):
                operation()

    def test_record_rejects_invalid_owned_states(self) -> None:
        cases = (
            lambda: StudyEffectTable(("a", "b"), np.array([1.0, 2.0]), np.ones(2)),
            lambda: StudyEffectTable(("a", "a", "c"), np.ones(3), np.ones(3)),
            lambda: StudyEffectTable(("a", "", "c"), np.ones(3), np.ones(3)),
            lambda: StudyEffectTable(cast(Any, ("a", 2, "c")), np.ones(3), np.ones(3)),
            lambda: StudyEffectTable(("a", "b", "c"), np.ones((1, 3)), np.ones(3)),
            lambda: StudyEffectTable(("a", "b", "c"), np.ones(3), np.ones(2)),
            lambda: StudyEffectTable(
                ("a", "b", "c"), np.array([1.0, np.nan, 3.0]), np.ones(3)
            ),
        )
        for operation in cases:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()


if __name__ == "__main__":
    unittest.main()
