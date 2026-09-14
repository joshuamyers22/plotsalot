"""Validated Polars-to-NumPy boundaries for statistical analyses."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import polars as pl
from numpy.typing import NDArray

from plotsalot.result import SampleAudit

FloatArray = NDArray[np.float64]
DEFAULT_MAX_ROWS = 1_000_000


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


@dataclass(frozen=True, slots=True)
class PairedNumericSample:
    """Two aligned, owned numeric columns and their reconciliation audit."""

    x: str
    y: str
    x_values: FloatArray
    y_values: FloatArray
    audit: SampleAudit

    def __post_init__(self) -> None:
        if not self.x or not self.y or self.x == self.y:
            raise ValueError("paired columns must be distinct and non-empty")
        x_candidate = np.asarray(self.x_values, dtype=np.float64)
        y_candidate = np.asarray(self.y_values, dtype=np.float64)
        if x_candidate.ndim != 1 or y_candidate.ndim != 1:
            raise ValueError("paired samples must be one-dimensional")
        if x_candidate.shape != y_candidate.shape:
            raise ValueError("paired samples must have equal shapes")
        if x_candidate.size != self.audit.analyzed_rows:
            raise ValueError("paired sample size must match its audit")
        if not bool(np.isfinite(x_candidate).all()) or not bool(
            np.isfinite(y_candidate).all()
        ):
            raise ValueError("paired sample values must be finite")
        x_buffer = x_candidate.tobytes(order="C")
        y_buffer = y_candidate.tobytes(order="C")
        object.__setattr__(
            self,
            "x_values",
            np.ndarray(x_candidate.shape, dtype=np.float64, buffer=x_buffer),
        )
        object.__setattr__(
            self,
            "y_values",
            np.ndarray(y_candidate.shape, dtype=np.float64, buffer=y_buffer),
        )


def select_numeric_sample(
    data: object,
    column: str,
    *,
    minimum_size: int = 1,
    require_variation: bool = False,
    maximum_rows: int = DEFAULT_MAX_ROWS,
) -> NumericSample:
    """Select and own one finite float64 sample from a Polars dataframe.

    Null rows are dropped and counted. Non-finite values fail rather than being
    silently omitted. The returned array is a copy, so later caller mutations of
    the dataframe cannot change the analyzed or rendered sample.
    """

    if minimum_size < 1:
        raise ValueError("minimum_size must be at least one")
    if maximum_rows < minimum_size:
        raise ValueError("maximum_rows must be at least minimum_size")
    if not isinstance(data, pl.DataFrame):
        raise TypeError("data must be a polars.DataFrame")
    if data.height > maximum_rows:
        raise ValueError(f"data exceeds maximum_rows={maximum_rows}")
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


def select_numeric_pair(
    data: object,
    x: str,
    y: str,
    *,
    minimum_size: int = 4,
    require_variation: bool = True,
    maximum_rows: int = DEFAULT_MAX_ROWS,
) -> PairedNumericSample:
    """Select pairwise-complete finite float64 arrays from a Polars dataframe."""

    if minimum_size < 1:
        raise ValueError("minimum_size must be at least one")
    if maximum_rows < minimum_size:
        raise ValueError("maximum_rows must be at least minimum_size")
    if not isinstance(data, pl.DataFrame):
        raise TypeError("data must be a polars.DataFrame")
    if data.height > maximum_rows:
        raise ValueError(f"data exceeds maximum_rows={maximum_rows}")
    if not x or not y or x == y:
        raise ValueError("paired columns must be distinct and non-empty")
    for column in (x, y):
        if column not in data.columns:
            raise ValueError(f"column not found: {column!r}")
        if not data.get_column(column).dtype.is_numeric():
            raise TypeError(f"column {column!r} must have a numeric dtype")

    pair = data.select(x, y).drop_nulls()
    if pair.height < minimum_size:
        raise ValueError(
            f"paired columns require at least {minimum_size} complete row(s)"
        )
    x_values = pair.get_column(x).to_numpy().astype(np.float64, copy=True)
    y_values = pair.get_column(y).to_numpy().astype(np.float64, copy=True)
    if not bool(np.isfinite(x_values).all()) or not bool(np.isfinite(y_values).all()):
        raise ValueError("paired columns contain NaN or infinite values")
    if require_variation and (
        float(np.std(x_values, ddof=1)) <= 0.0 or float(np.std(y_values, ddof=1)) <= 0.0
    ):
        raise ValueError("paired columns require nonzero sample variation")

    return PairedNumericSample(
        x=x,
        y=y,
        x_values=x_values,
        y_values=y_values,
        audit=SampleAudit(
            input_rows=data.height,
            analyzed_rows=pair.height,
            dropped_null_rows=data.height - pair.height,
        ),
    )
