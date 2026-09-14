"""Owned data boundaries for between- and within-group comparisons."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

import numpy as np
import polars as pl
from numpy.typing import NDArray

from plotsalot.comparison_result import RepeatedSampleAudit
from plotsalot.data import DEFAULT_MAX_ROWS, FloatArray
from plotsalot.result import SampleAudit, ScalarIdentity


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


def _resolved_identities(series: pl.Series, label: str) -> tuple[ScalarIdentity, ...]:
    values = tuple(_identity(value, label) for value in series.unique().to_list())
    seen = {(type(value), value): value for value in values}
    if isinstance(series.dtype, pl.Enum):
        ordered = tuple(
            _identity(value, label)
            for value in series.dtype.categories.to_list()
            if (str, value) in seen
        )
        if len(ordered) != len(values):
            raise ValueError(f"{label} enum categories do not resolve uniquely")
        return ordered
    return tuple(sorted(values, key=_identity_key))


def _owned_float_array(values: object, *, dimensions: int) -> NDArray[np.float64]:
    candidate = np.asarray(values, dtype=np.float64)
    if candidate.ndim != dimensions:
        raise ValueError(f"comparison values must be {dimensions}-dimensional")
    if not bool(np.isfinite(candidate).all()):
        raise ValueError("comparison values must be finite")
    buffer = candidate.tobytes(order="C")
    return np.ndarray(candidate.shape, dtype=np.float64, buffer=buffer)


@dataclass(frozen=True, slots=True)
class ComparisonSample:
    """Resolved independent levels and owned values used for analysis/rendering."""

    x: str
    y: str
    levels: tuple[ScalarIdentity, ...]
    values: tuple[FloatArray, ...]
    audit: SampleAudit

    def __post_init__(self) -> None:
        if not self.x or not self.y or self.x == self.y:
            raise ValueError("comparison sample columns must be distinct")
        if not 2 <= len(self.levels) <= 20 or len(self.values) != len(self.levels):
            raise ValueError("comparison sample requires matching 2-20 levels")
        keys = tuple((type(level), level) for level in self.levels)
        if len(set(keys)) != len(keys):
            raise ValueError("comparison sample levels must be unique")
        owned: list[FloatArray] = []
        for values in self.values:
            array = _owned_float_array(values, dimensions=1)
            if array.size < 2 or float(np.std(array, ddof=1)) <= 0.0:
                raise ValueError(
                    "independent comparison levels require two values and variation"
                )
            owned.append(array)
        if sum(values.size for values in owned) != self.audit.analyzed_rows:
            raise ValueError("comparison sample values must match its audit")
        object.__setattr__(self, "values", tuple(owned))


@dataclass(frozen=True, slots=True)
class RepeatedSample:
    """Resolved complete subject block used for repeated analysis/rendering."""

    x: str
    y: str
    subject_id: str
    conditions: tuple[ScalarIdentity, ...]
    subjects: tuple[ScalarIdentity, ...]
    values: NDArray[np.float64]
    audit: RepeatedSampleAudit

    def __post_init__(self) -> None:
        if (
            not self.x
            or not self.y
            or not self.subject_id
            or len({self.x, self.y, self.subject_id}) != 3
        ):
            raise ValueError("repeated sample columns must be distinct and non-empty")
        if not 2 <= len(self.conditions) <= 20:
            raise ValueError("repeated sample requires 2-20 conditions")
        if len(self.subjects) != self.audit.analyzed_subjects:
            raise ValueError("repeated subject identities must match the audit")
        condition_keys = tuple((type(value), value) for value in self.conditions)
        subject_keys = tuple((type(value), value) for value in self.subjects)
        if len(set(condition_keys)) != len(condition_keys):
            raise ValueError("repeated conditions must be unique")
        if len(set(subject_keys)) != len(subject_keys):
            raise ValueError("repeated subjects must be unique")
        owned = _owned_float_array(self.values, dimensions=2)
        if owned.shape != (len(self.subjects), len(self.conditions)):
            raise ValueError("repeated values must form the declared complete block")
        if owned.size != self.audit.analyzed_rows:
            raise ValueError("repeated values must match the sample audit")
        object.__setattr__(self, "values", owned)


def _validate_frame_and_columns(
    data: object,
    columns: tuple[str, ...],
    *,
    maximum_rows: int,
) -> pl.DataFrame:
    if not isinstance(data, pl.DataFrame):
        raise TypeError("data must be a polars.DataFrame")
    if type(maximum_rows) is not int or maximum_rows < 1:
        raise ValueError("maximum_rows must be a positive integer")
    if data.height > maximum_rows:
        raise ValueError(f"data exceeds maximum_rows={maximum_rows}")
    if any(not column for column in columns) or len(set(columns)) != len(columns):
        raise ValueError("selected columns must be distinct and non-empty")
    for column in columns:
        if column not in data.columns:
            raise ValueError(f"column not found: {column!r}")
    return data


def select_comparison_sample(
    data: object,
    x: str,
    y: str,
    *,
    maximum_rows: int = DEFAULT_MAX_ROWS,
    maximum_levels: int = 20,
) -> ComparisonSample:
    """Select deterministic independent groups and own their finite values."""

    frame = _validate_frame_and_columns(data, (x, y), maximum_rows=maximum_rows)
    if type(maximum_levels) is not int or not 2 <= maximum_levels <= 20:
        raise ValueError("maximum_levels must be an integer between 2 and 20")
    if not frame.get_column(y).dtype.is_numeric():
        raise TypeError(f"column {y!r} must have a numeric dtype")
    retained = frame.select(x, y).drop_nulls()
    if retained.is_empty():
        raise ValueError("comparison requires non-null level and response values")
    levels = _resolved_identities(retained.get_column(x), "comparison level")
    if not 2 <= len(levels) <= maximum_levels:
        raise ValueError(f"comparison requires 2-{maximum_levels} retained levels")

    values: list[FloatArray] = []
    for level in levels:
        level_values = (
            retained.filter(pl.col(x) == level)
            .get_column(y)
            .to_numpy()
            .astype(np.float64, copy=True)
        )
        if not bool(np.isfinite(level_values).all()):
            raise ValueError(f"comparison level {level!r} contains NaN or infinity")
        if level_values.size < 2:
            raise ValueError(f"comparison level {level!r} requires two observations")
        if float(np.std(level_values, ddof=1)) <= 0.0:
            raise ValueError(f"comparison level {level!r} requires sample variation")
        values.append(level_values)

    return ComparisonSample(
        x=x,
        y=y,
        levels=levels,
        values=tuple(values),
        audit=SampleAudit(
            input_rows=frame.height,
            analyzed_rows=retained.height,
            dropped_null_rows=frame.height - retained.height,
        ),
    )


def select_repeated_sample(
    data: object,
    x: str,
    y: str,
    subject_id: str,
    *,
    maximum_rows: int = DEFAULT_MAX_ROWS,
    maximum_levels: int = 20,
    minimum_subjects: int = 3,
) -> RepeatedSample:
    """Select an explicit, duplicate-free, complete repeated-measures block."""

    frame = _validate_frame_and_columns(
        data, (x, y, subject_id), maximum_rows=maximum_rows
    )
    if type(maximum_levels) is not int or not 2 <= maximum_levels <= 20:
        raise ValueError("maximum_levels must be an integer between 2 and 20")
    if type(minimum_subjects) is not int or minimum_subjects < 3:
        raise ValueError("minimum_subjects must be an integer of at least three")
    if not frame.get_column(y).dtype.is_numeric():
        raise TypeError(f"column {y!r} must have a numeric dtype")

    selected = frame.select(subject_id, x, y)
    identity_valid = selected.filter(
        pl.col(subject_id).is_not_null() & pl.col(x).is_not_null()
    )
    dropped_identity = selected.height - identity_valid.height
    if identity_valid.is_empty():
        raise ValueError("repeated analysis requires subject and condition identities")

    duplicates = (
        identity_valid.group_by(subject_id, x, maintain_order=True)
        .len()
        .filter(pl.col("len") > 1)
    )
    if not duplicates.is_empty():
        duplicate = duplicates.row(0, named=True)
        raise ValueError(
            "duplicate subject-condition cell: "
            f"subject={duplicate[subject_id]!r}, condition={duplicate[x]!r}"
        )

    conditions = _resolved_identities(identity_valid.get_column(x), "condition")
    if not 2 <= len(conditions) <= maximum_levels:
        raise ValueError(f"repeated analysis requires 2-{maximum_levels} conditions")
    all_subjects = _resolved_identities(
        identity_valid.get_column(subject_id), "subject identity"
    )

    rows: dict[
        tuple[type[object], ScalarIdentity],
        dict[tuple[type[object], ScalarIdentity], float | None],
    ] = {}
    for row in identity_valid.iter_rows(named=True):
        subject = _identity(row[subject_id], "subject identity")
        condition = _identity(row[x], "condition")
        raw_value = row[y]
        value = None if raw_value is None else float(raw_value)
        if value is not None and not isfinite(value):
            raise ValueError("repeated response contains NaN or infinite values")
        rows.setdefault((type(subject), subject), {})[(type(condition), condition)] = (
            value
        )

    condition_keys = tuple((type(condition), condition) for condition in conditions)
    complete_subjects: list[ScalarIdentity] = []
    complete_rows: list[list[float]] = []
    incomplete_subjects = 0
    excluded_incomplete_rows = 0
    dropped_values = identity_valid.get_column(y).null_count()
    for subject in all_subjects:
        subject_values = rows[(type(subject), subject)]
        complete = all(
            key in subject_values and subject_values[key] is not None
            for key in condition_keys
        )
        if complete:
            complete_subjects.append(subject)
            complete_row: list[float] = []
            for key in condition_keys:
                value = subject_values[key]
                if value is None:
                    raise RuntimeError("complete repeated row lost a value")
                complete_row.append(value)
            complete_rows.append(complete_row)
        else:
            incomplete_subjects += 1
            excluded_incomplete_rows += sum(
                value is not None for value in subject_values.values()
            )

    if len(complete_subjects) < minimum_subjects:
        raise ValueError(
            f"repeated analysis requires at least {minimum_subjects} complete subjects"
        )
    matrix = np.asarray(complete_rows, dtype=np.float64)
    audit = RepeatedSampleAudit(
        input_rows=selected.height,
        analyzed_rows=int(matrix.size),
        analyzed_subjects=len(complete_subjects),
        dropped_null_identity_rows=dropped_identity,
        dropped_null_value_rows=dropped_values,
        excluded_incomplete_rows=excluded_incomplete_rows,
        excluded_incomplete_subjects=incomplete_subjects,
    )
    return RepeatedSample(
        x=x,
        y=y,
        subject_id=subject_id,
        conditions=conditions,
        subjects=tuple(complete_subjects),
        values=matrix,
        audit=audit,
    )
