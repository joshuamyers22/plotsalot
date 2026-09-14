from __future__ import annotations

import unittest

import numpy as np
import polars as pl

from plotsalot import NumericSample, select_numeric_sample
from plotsalot.core import SampleAudit


class NumericDataBoundaryTests(unittest.TestCase):
    def test_selection_is_owned_read_only_float64_and_reconciled(self) -> None:
        frame = pl.DataFrame({"value": pl.Series([1, None, 3], dtype=pl.Int64)})
        source_values = frame.get_column("value").drop_nulls().to_numpy()

        sample = select_numeric_sample(frame, "value", minimum_size=2)

        self.assertEqual(sample.values.dtype, np.dtype(np.float64))
        np.testing.assert_array_equal(sample.values, np.array([1.0, 3.0]))
        self.assertFalse(sample.values.flags.writeable)
        self.assertFalse(np.shares_memory(sample.values, source_values))
        self.assertEqual(sample.audit.input_rows, 3)
        self.assertEqual(sample.audit.analyzed_rows, 2)
        self.assertEqual(sample.audit.dropped_null_rows, 1)
        with self.assertRaises(ValueError):
            sample.values[0] = 99.0
        with self.assertRaises(ValueError):
            sample.values.setflags(write=True)

    def test_boundary_rejects_unsupported_or_unsafe_inputs(self) -> None:
        valid = pl.DataFrame({"value": [1.0, 2.0]})
        cases = (
            lambda: select_numeric_sample(object(), "value"),
            lambda: select_numeric_sample(valid, ""),
            lambda: select_numeric_sample(valid, "missing"),
            lambda: select_numeric_sample(pl.DataFrame({"value": ["a"]}), "value"),
            lambda: select_numeric_sample(valid, "value", minimum_size=3),
            lambda: select_numeric_sample(valid, "value", minimum_size=0),
            lambda: select_numeric_sample(
                pl.DataFrame({"value": [1.0, np.nan]}), "value"
            ),
            lambda: select_numeric_sample(
                pl.DataFrame({"value": [1.0, np.inf]}), "value"
            ),
            lambda: select_numeric_sample(
                pl.DataFrame({"value": [1.0, 1.0]}),
                "value",
                require_variation=True,
            ),
            lambda: select_numeric_sample(
                pl.DataFrame({"value": [1.0]}),
                "value",
                require_variation=True,
            ),
        )

        for operation in cases:
            with (
                self.subTest(operation=operation),
                self.assertRaises((TypeError, ValueError)),
            ):
                operation()

    def test_numeric_sample_validates_shape_size_and_finiteness(self) -> None:
        audit = SampleAudit(input_rows=2, analyzed_rows=2, dropped_null_rows=0)
        cases = (
            lambda: NumericSample("", np.array([1.0, 2.0]), audit),
            lambda: NumericSample("value", np.array([[1.0, 2.0]]), audit),
            lambda: NumericSample("value", np.array([1.0]), audit),
            lambda: NumericSample("value", np.array([1.0, np.nan]), audit),
        )

        for operation in cases:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

    def test_sample_audit_rejects_impossible_counts(self) -> None:
        with self.assertRaises(ValueError):
            SampleAudit(input_rows=-1, analyzed_rows=0, dropped_null_rows=0)
        with self.assertRaises(ValueError):
            SampleAudit(input_rows=4, analyzed_rows=2, dropped_null_rows=1)


if __name__ == "__main__":
    unittest.main()
