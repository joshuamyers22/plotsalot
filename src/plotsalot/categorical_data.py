"""Owned raw and count-weighted categorical table boundary."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

import numpy as np
import polars as pl
from numpy.typing import NDArray

from plotsalot.categorical_result import CategoricalSampleAudit
from plotsalot.data import DEFAULT_MAX_ROWS
from plotsalot.result import ScalarIdentity

DEFAULT_MAX_LEVELS = 20
DEFAULT_MAX_CELLS = 400
DEFAULT_MAX_TOTAL_COUNT = 1_000_000_000


def _identity(value: object, label: str) -> ScalarIdentity:
    if isinstance(value, bool):
        return value
    if isinstance(value, (str, int)):
        if isinstance(value, str) and not value:
            raise ValueError(f"{label} must not be empty")
        return value
    if isinstance(value, float) and isfinite(value):
        return value
    raise TypeError(
        f"{label} values must be finite strings, integers, floats, or booleans"
    )


def _identity_key(value: ScalarIdentity) -> tuple[int, str | float]:
    if isinstance(value, bool):
        return (0, float(value))
    if isinstance(value, (int, float)):
        return (1, float(value))
    return (2, value)


def _categorical_identities(
    series: pl.Series, label: str
) -> tuple[ScalarIdentity, ...]:
    if isinstance(series.dtype, pl.Enum):
        return tuple(_identity(value, label) for value in series.dtype.categories)
    values = tuple(_identity(value, label) for value in series.unique().to_list())
    return tuple(sorted(values, key=_identity_key))


@dataclass(frozen=True, slots=True)
class CategoricalTable:
    x: str
    y: str | None
    counts_column: str | None
    x_levels: tuple[ScalarIdentity, ...]
    y_levels: tuple[ScalarIdentity, ...]
    observed: NDArray[np.int64]
    audit: CategoricalSampleAudit

    def __post_init__(self) -> None:
        if not self.x or self.y == self.x or self.counts_column in {self.x, self.y}:
            raise ValueError("categorical table columns must be distinct")
        if not 2 <= len(self.x_levels) <= 20:
            raise ValueError("categorical table requires 2-20 x levels")
        if self.y is None and self.y_levels:
            raise ValueError("one-way table cannot contain y levels")
        if self.y is not None and not 2 <= len(self.y_levels) <= 20:
            raise ValueError("two-way table requires 2-20 y levels")
        candidate = np.asarray(self.observed)
        shape = (len(self.x_levels), max(1, len(self.y_levels)))
        if candidate.shape != shape or not np.issubdtype(candidate.dtype, np.integer):
            raise ValueError("categorical observed table has invalid shape or dtype")
        if (
            bool((candidate < 0).any())
            or sum(int(value) for value in candidate.flat) != self.audit.weighted_total
        ):
            raise ValueError("categorical observed counts must reconcile")
        owned = np.ndarray(
            shape,
            dtype=np.int64,
            buffer=candidate.astype(np.int64, copy=False).tobytes(order="C"),
        )
        object.__setattr__(self, "observed", owned)


def select_categorical_table(
    data: object,
    x: str,
    y: str | None = None,
    *,
    counts: str | None = None,
    maximum_rows: int = DEFAULT_MAX_ROWS,
    maximum_levels: int = DEFAULT_MAX_LEVELS,
    maximum_cells: int = DEFAULT_MAX_CELLS,
    maximum_total_count: int = DEFAULT_MAX_TOTAL_COUNT,
) -> CategoricalTable:
    if not isinstance(data, pl.DataFrame):
        raise TypeError("data must be a polars.DataFrame")
    columns = tuple(column for column in (x, y, counts) if column is not None)
    if any(not column for column in columns) or len(set(columns)) != len(columns):
        raise ValueError("categorical columns must be distinct and non-empty")
    for column in columns:
        if column not in data.columns:
            raise ValueError(f"column not found: {column!r}")
    limits = (maximum_rows, maximum_levels, maximum_cells, maximum_total_count)
    if any(type(value) is not int or value < 1 for value in limits):
        raise ValueError("categorical resource limits must be positive integers")
    if maximum_levels > 20:
        raise ValueError("maximum_levels cannot exceed 20")
    if maximum_total_count > np.iinfo(np.int64).max:
        raise ValueError("maximum_total_count cannot exceed int64")
    if data.height > maximum_rows:
        raise ValueError(f"data exceeds maximum_rows={maximum_rows}")
    if counts is not None:
        dtype = data.get_column(counts).dtype
        if dtype == pl.Boolean or not dtype.is_integer():
            raise TypeError("counts column must have an integer dtype")

    selected = data.select(columns)
    x_null = selected.get_column(x).is_null()
    y_null = (
        pl.Series([False] * selected.height)
        if y is None
        else selected.get_column(y).is_null() & ~x_null
    )
    count_null = (
        pl.Series([False] * selected.height)
        if counts is None
        else selected.get_column(counts).is_null() & ~x_null & ~y_null
    )
    valid = ~(x_null | y_null | count_null)
    retained = selected.filter(valid)
    if retained.is_empty():
        raise ValueError("categorical analysis requires retained observations")
    x_levels = _categorical_identities(retained.get_column(x), "x category")
    y_levels = (
        ()
        if y is None
        else _categorical_identities(retained.get_column(y), "y category")
    )
    if not 2 <= len(x_levels) <= maximum_levels:
        raise ValueError(f"x category count must be between 2 and {maximum_levels}")
    if y is not None and not 2 <= len(y_levels) <= maximum_levels:
        raise ValueError(f"y category count must be between 2 and {maximum_levels}")
    cell_count = len(x_levels) * max(1, len(y_levels))
    if cell_count > maximum_cells:
        raise ValueError(f"categorical table exceeds maximum_cells={maximum_cells}")

    observed = np.zeros((len(x_levels), max(1, len(y_levels))), dtype=np.int64)
    x_index = {(type(value), value): index for index, value in enumerate(x_levels)}
    y_index = {(type(value), value): index for index, value in enumerate(y_levels)}
    aggregated = (
        retained.group_by([x] if y is None else [x, y]).len(name="_weight")
        if counts is None
        else retained
    )
    running_total = 0
    for row in aggregated.iter_rows(named=True):
        x_value = _identity(row[x], "x category")
        x_key = (type(x_value), x_value)
        if y is None:
            y_position = 0
        else:
            y_value = _identity(row[y], "y category")
            y_position = y_index[(type(y_value), y_value)]
        weight = row["_weight"] if counts is None else row[counts]
        if isinstance(weight, bool) or not isinstance(weight, int) or weight < 0:
            raise ValueError("counts values must be nonnegative integers")
        if running_total > maximum_total_count - weight:
            raise ValueError(f"weighted total must be within 1-{maximum_total_count}")
        current = int(observed[x_index[x_key], y_position])
        observed[x_index[x_key], y_position] = current + weight
        running_total += weight
    total = running_total
    if total < 1 or total > maximum_total_count:
        raise ValueError(f"weighted total must be within 1-{maximum_total_count}")
    return CategoricalTable(
        x=x,
        y=y,
        counts_column=counts,
        x_levels=x_levels,
        y_levels=y_levels,
        observed=observed,
        audit=CategoricalSampleAudit(
            input_rows=selected.height,
            analyzed_rows=retained.height,
            weighted_total=total,
            dropped_null_x_rows=int(x_null.sum()),
            dropped_null_y_rows=int(y_null.sum()),
            dropped_null_count_rows=int(count_null.sum()),
        ),
    )
