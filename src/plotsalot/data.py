"""Validated Polars-to-NumPy boundaries for statistical analyses."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import polars as pl
from numpy.typing import NDArray

from plotsalot.result import SampleAudit

FloatArray = NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class NumericSample:
    """An owned, read-only numeric column and its reconciliation audit."""

    column: str
    values: FloatArray
    audit: SampleAudit

    def __post_init__(self) -> None:
        if not self.column:
            raise ValueError("column must be non-empty")

        candidate = np.asarray(self.values, dtype=np.float64)
        if candidate.ndim != 1:
            raise ValueError("numeric sample must be one-dimensional")
        if candidate.size != self.audit.analyzed_rows:
            raise ValueError("numeric sample size must match its sample audit")
        if not bool(np.isfinite(candidate).all()):
            raise ValueError("numeric sample values must be finite")
        immutable_buffer = candidate.tobytes(order="C")
        owned: FloatArray = np.ndarray(
            candidate.shape, dtype=np.float64, buffer=immutable_buffer
        )
        object.__setattr__(self, "values", owned)


def select_numeric_sample(
    data: object,
    column: str,
    *,
    minimum_size: int = 1,
    require_variation: bool = False,
) -> NumericSample:
    """Select and own one finite float64 sample from a Polars dataframe.

    Null rows are dropped and counted. Non-finite values fail rather than being
    silently omitted. The returned array is a copy, so later caller mutations of
    the dataframe cannot change the analyzed or rendered sample.
    """

    if minimum_size < 1:
        raise ValueError("minimum_size must be at least one")
    if not isinstance(data, pl.DataFrame):
        raise TypeError("data must be a polars.DataFrame")
    if not column:
        raise ValueError("column must be non-empty")
    if column not in data.columns:
        raise ValueError(f"column not found: {column!r}")

    series = data.get_column(column)
    if not series.dtype.is_numeric():
        raise TypeError(f"column {column!r} must have a numeric dtype")

    dropped_null_rows = series.null_count()
    values: FloatArray = series.drop_nulls().to_numpy().astype(np.float64, copy=True)
    if values.ndim != 1:
        raise ValueError("selected column must convert to a one-dimensional array")
    if values.size < minimum_size:
        raise ValueError(
            f"selected column requires at least {minimum_size} non-null value(s)"
        )
    if not bool(np.isfinite(values).all()):
        raise ValueError("selected column contains NaN or infinite values")
    if require_variation and (values.size < 2 or float(np.std(values, ddof=1)) <= 0.0):
        raise ValueError("selected column requires nonzero sample variation")

    return NumericSample(
        column=column,
        values=values,
        audit=SampleAudit(
            input_rows=data.height,
            analyzed_rows=int(values.size),
            dropped_null_rows=dropped_null_rows,
        ),
    )
