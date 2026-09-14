"""Owned Polars-to-NumPy boundaries for M5 coefficient and study tables."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import polars as pl
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]

DEFAULT_MAX_STUDIES = 500
HARD_MAX_STUDIES = 1_000
MINIMUM_STUDIES = 3
DEFAULT_MAX_COEFFICIENTS = 500
HARD_MAX_COEFFICIENTS = 1_000
IDENTITY_COLUMNS = ("response", "component", "group")
INFERENCE_COLUMNS = frozenset(
    {
        "conf_low",
        "conf_high",
        "standard_error",
        "statistic_kind",
        "statistic",
        "df",
        "p_value",
    }
)

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


@dataclass(frozen=True, slots=True)
class CoefficientTable:
    """Owned coefficient rows with one resolved table-wide inference profile."""

    terms: tuple[str, ...]
    identities: tuple[tuple[str, ...], ...]
    identity_columns: tuple[str, ...]
    estimates: FloatArray
    is_intercepts: tuple[bool, ...]
    profile: str
    conf_low: FloatArray | None = None
    conf_high: FloatArray | None = None
    standard_errors: FloatArray | None = None
    statistics: FloatArray | None = None
    dfs: FloatArray | None = None
    p_values: FloatArray | None = None

    def __post_init__(self) -> None:
        count = len(self.terms)
        if count < 1 or any(not _is_nonempty_string(term) for term in self.terms):
            raise ValueError("coefficient terms must be nonempty strings")
        if self.identity_columns != tuple(
            column for column in IDENTITY_COLUMNS if column in self.identity_columns
        ):
            raise ValueError("coefficient identity columns are unsupported")
        if len(self.identities) != count or any(
            len(identity) != len(self.identity_columns)
            or any(not _is_nonempty_string(value) for value in identity)
            for identity in self.identities
        ):
            raise ValueError("coefficient structured identities are invalid")
        keys = tuple(
            (*identity, term)
            for identity, term in zip(self.identities, self.terms, strict=True)
        )
        if len(set(keys)) != count:
            raise ValueError("coefficient row identities must be unique")
        if len(self.is_intercepts) != count or any(
            type(value) is not bool for value in self.is_intercepts
        ):
            raise ValueError("coefficient intercept markers must be boolean")
        estimates = _owned_float_array(self.estimates)
        if estimates.size != count:
            raise ValueError("coefficient estimates and identities must align")
        object.__setattr__(self, "estimates", estimates)
        optional_names = (
            "conf_low",
            "conf_high",
            "standard_errors",
            "statistics",
            "dfs",
            "p_values",
        )
        for name in optional_names:
            value = getattr(self, name)
            if value is not None:
                owned = _owned_float_array(value)
                if owned.size != count:
                    raise ValueError("coefficient inference arrays must align")
                object.__setattr__(self, name, owned)
        expected = {
            "estimate_only": (False, False, False, False, False, False),
            "interval": (True, True, False, False, False, False),
            "full_t": (True, True, True, True, True, True),
            "full_z": (True, True, True, True, False, True),
        }
        presence = tuple(getattr(self, name) is not None for name in optional_names)
        if self.profile not in expected or presence != expected[self.profile]:
            raise ValueError("coefficient inference profile is inconsistent")

    @property
    def keys(self) -> tuple[tuple[str, ...], ...]:
        return tuple(
            (*identity, term)
            for identity, term in zip(self.identities, self.terms, strict=True)
        )


def _numeric_column(frame: pl.DataFrame, name: str) -> FloatArray:
    series = frame.get_column(name)
    if not series.dtype.is_numeric():
        raise TypeError(f"column {name!r} must have a numeric dtype")
    return _owned_float_array(series.to_numpy())


def select_coefficients(
    data: object, *, maximum_coefficients: int = DEFAULT_MAX_COEFFICIENTS
) -> CoefficientTable:
    """Validate and own the approved M5A Polars coefficient-table profile."""

    if not isinstance(data, pl.DataFrame):
        raise TypeError("data must be a polars.DataFrame")
    if (
        type(maximum_coefficients) is not int
        or maximum_coefficients < 1
        or maximum_coefficients > HARD_MAX_COEFFICIENTS
    ):
        raise ValueError(
            "maximum_coefficients must be an integer from 1 through "
            f"{HARD_MAX_COEFFICIENTS}"
        )
    if not 1 <= data.height <= maximum_coefficients:
        raise ValueError(f"coefficient table requires 1-{maximum_coefficients} rows")
    missing = tuple(column for column in ("term", "estimate") if column not in data)
    if missing:
        raise ValueError(f"missing required coefficient column(s): {missing!r}")

    identity_columns = tuple(column for column in IDENTITY_COLUMNS if column in data)
    participating = ("term", *identity_columns, "estimate")
    inference_present = frozenset(INFERENCE_COLUMNS.intersection(data.columns))
    profile_fields: dict[str, frozenset[str]] = {
        "estimate_only": frozenset[str](),
        "interval": frozenset(("conf_low", "conf_high")),
        "full_t": INFERENCE_COLUMNS,
        "full_z": INFERENCE_COLUMNS - {"df"},
    }
    matches = tuple(
        name for name, fields in profile_fields.items() if fields == inference_present
    )
    if len(matches) != 1:
        raise ValueError(
            "coefficient inference columns do not form one approved table-wide profile"
        )
    profile = matches[0]
    selected_names = (*participating, *sorted(inference_present))
    if "is_intercept" in data:
        selected_names = (*selected_names, "is_intercept")
    selected = data.select(*selected_names)
    if any(selected.get_column(name).null_count() for name in selected_names):
        raise ValueError("coefficient participating columns cannot contain null values")
    for name in ("term", *identity_columns):
        if selected.get_column(name).dtype != pl.String:
            raise TypeError(f"column {name!r} must have a String dtype")
    if (
        "is_intercept" in data
        and selected.get_column("is_intercept").dtype != pl.Boolean
    ):
        raise TypeError("column 'is_intercept' must have a Boolean dtype")

    terms = tuple(selected.get_column("term").to_list())
    identities = tuple(
        tuple(selected.get_column(column)[index] for column in identity_columns)
        for index in range(data.height)
    )
    estimates = _numeric_column(selected, "estimate")
    is_intercepts = (
        tuple(selected.get_column("is_intercept").to_list())
        if "is_intercept" in selected
        else (False,) * data.height
    )
    arrays: dict[str, FloatArray | None] = {
        name: _numeric_column(selected, name) if name in inference_present else None
        for name in (
            "conf_low",
            "conf_high",
            "standard_error",
            "statistic",
            "df",
            "p_value",
        )
    }
    if profile in {"full_t", "full_z"}:
        kinds = selected.get_column("statistic_kind")
        expected_kind = "t" if profile == "full_t" else "z"
        if kinds.dtype != pl.String or any(value != expected_kind for value in kinds):
            raise ValueError(f"statistic_kind must be {expected_kind!r} for {profile}")
    low, high = arrays["conf_low"], arrays["conf_high"]
    if (
        low is not None
        and high is not None
        and bool(((low > high) | (estimates < low) | (estimates > high)).any())
    ):
        raise ValueError("coefficient intervals must be ordered and contain estimates")
    errors = arrays["standard_error"]
    if errors is not None and bool((errors <= 0.0).any()):
        raise ValueError("coefficient standard errors must be strictly positive")
    dfs = arrays["df"]
    if dfs is not None and bool((dfs <= 0.0).any()):
        raise ValueError("coefficient degrees of freedom must be strictly positive")
    p_values = arrays["p_value"]
    if p_values is not None and bool(((p_values < 0.0) | (p_values > 1.0)).any()):
        raise ValueError("coefficient p-values must lie within [0, 1]")
    return CoefficientTable(
        terms,
        identities,
        identity_columns,
        estimates,
        is_intercepts,
        profile,
        arrays["conf_low"],
        arrays["conf_high"],
        arrays["standard_error"],
        arrays["statistic"],
        arrays["df"],
        arrays["p_value"],
    )


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
