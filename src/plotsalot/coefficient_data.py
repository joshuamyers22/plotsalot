"""Owned Polars-to-NumPy boundary for M5 study-effect tables."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import polars as pl
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]

DEFAULT_MAX_STUDIES = 500
HARD_MAX_STUDIES = 1_000
MINIMUM_STUDIES = 3

REQUIRED_META_COLUMNS = ("term", "estimate", "standard_error")
FORBIDDEN_META_COLUMNS = frozenset(
    {
        "conf_low",
        "conf_high",
        "ci_low",
        "ci_high",
        "statistic",
        "df",
        "p_value",
        "is_intercept",
        "component",
        "group",
        "model",
        "response",
        "statistic_kind",
    }
)


def _is_nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _owned_float_array(values: object) -> FloatArray:
    candidate = np.asarray(values, dtype=np.float64)
    if candidate.ndim != 1 or not bool(np.isfinite(candidate).all()):
        raise ValueError("study-effect values must be one-dimensional and finite")
    return np.ndarray(
        candidate.shape,
        dtype=np.float64,
        buffer=candidate.tobytes(order="C"),
    )


@dataclass(frozen=True, slots=True)
class StudyEffectTable:
    """Unique study identities with owned estimates and standard errors."""

    terms: tuple[str, ...]
    estimates: FloatArray
    standard_errors: FloatArray

    def __post_init__(self) -> None:
        if len(self.terms) < MINIMUM_STUDIES:
            raise ValueError("meta-analysis requires at least three studies")
        if any(not _is_nonempty_string(term) for term in self.terms):
            raise ValueError("study identities must be nonempty strings")
        if len(set(self.terms)) != len(self.terms):
            raise ValueError("study identities must be unique")
        estimates = _owned_float_array(self.estimates)
        standard_errors = _owned_float_array(self.standard_errors)
        if estimates.shape != standard_errors.shape or estimates.size != len(
            self.terms
        ):
            raise ValueError("study identities, estimates, and errors must align")
        if bool((standard_errors <= 0.0).any()):
            raise ValueError("study standard errors must be strictly positive")
        object.__setattr__(self, "estimates", estimates)
        object.__setattr__(self, "standard_errors", standard_errors)


def select_study_effects(
    data: object,
    *,
    maximum_studies: int = DEFAULT_MAX_STUDIES,
) -> StudyEffectTable:
    """Validate and own the explicit M5B aggregate study-effect columns."""

    if not isinstance(data, pl.DataFrame):
        raise TypeError("data must be a polars.DataFrame")
    if (
        type(maximum_studies) is not int
        or maximum_studies < MINIMUM_STUDIES
        or maximum_studies > HARD_MAX_STUDIES
    ):
        raise ValueError(
            f"maximum_studies must be an integer from {MINIMUM_STUDIES} "
            f"through {HARD_MAX_STUDIES}"
        )
    missing = tuple(column for column in REQUIRED_META_COLUMNS if column not in data)
    if missing:
        raise ValueError(f"missing required meta-analysis column(s): {missing!r}")
    forbidden = tuple(sorted(FORBIDDEN_META_COLUMNS.intersection(data.columns)))
    if forbidden:
        raise ValueError(
            "meta-analysis input contains coefficient-inference column(s): "
            f"{forbidden!r}"
        )
    if not MINIMUM_STUDIES <= data.height <= maximum_studies:
        raise ValueError(
            f"meta-analysis requires {MINIMUM_STUDIES}-{maximum_studies} studies"
        )

    selected = data.select(*REQUIRED_META_COLUMNS)
    if any(
        selected.get_column(column).null_count() for column in REQUIRED_META_COLUMNS
    ):
        raise ValueError("meta-analysis columns cannot contain null values")
    term_series = selected.get_column("term")
    if term_series.dtype != pl.String:
        raise TypeError("column 'term' must have a String dtype")
    for column in ("estimate", "standard_error"):
        if not selected.get_column(column).dtype.is_numeric():
            raise TypeError(f"column {column!r} must have a numeric dtype")

    terms = tuple(term_series.to_list())
    estimates = selected.get_column("estimate").to_numpy().astype(np.float64, copy=True)
    standard_errors = (
        selected.get_column("standard_error").to_numpy().astype(np.float64, copy=True)
    )
    return StudyEffectTable(terms, estimates, standard_errors)
