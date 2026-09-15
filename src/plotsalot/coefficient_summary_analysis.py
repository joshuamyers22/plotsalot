"""Strict caller-reported coefficient summaries for M6C pass 1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any, Literal, cast
from unicodedata import category

import numpy as np
import polars as pl
from numpy.typing import NDArray

from plotsalot.coefficient_data import (
    DEFAULT_MAX_COEFFICIENTS,
    HARD_MAX_COEFFICIENTS,
    IDENTITY_COLUMNS,
)
from plotsalot.coefficient_result import (
    CoefficientIdentityResult,
    CoefficientTableResourceLimits,
)
from plotsalot.result import IntervalResult

FloatArray = NDArray[np.float64]
DEFAULT_MAX_RENDERED_POINTS = 500
DEFAULT_MAX_LABELS = 200
HARD_MAX_RENDERED_POINTS = 1_000
HARD_MAX_LABELS = 1_000
PROBABILITY_TOLERANCE = 1e-12
ROBUST_INTERVAL_METHOD = "caller_reported_robust_confidence_interval"
POSTERIOR_INTERVAL_METHOD = "caller_reported_equal_tail_credible_interval"

_ROBUST_REQUIRED = ("term", "estimate", "conf_low", "conf_high")
_POSTERIOR_REQUIRED = (
    "term",
    "posterior_median",
    "credible_low",
    "credible_high",
    "probability_above_null",
    "probability_below_null",
    "probability_at_null",
)
_CLASSICAL_INFERENCE = frozenset(
    {
        "standard_error",
        "statistic_kind",
        "statistic",
        "df",
        "p_value",
        "ci_low",
        "ci_high",
    }
)
_BAYESIAN_FIELDS = frozenset(
    {
        "posterior_median",
        "credible_low",
        "credible_high",
        "probability_above_null",
        "probability_below_null",
        "probability_at_null",
        "credible_level",
        "log_bf10",
        "bf10",
        "model",
        "posterior",
        "draw",
        "draws",
        "chain",
        "artifact",
        "artifact_reference",
    }
)
_ROBUST_FORBIDDEN = _CLASSICAL_INFERENCE | _BAYESIAN_FIELDS
_POSTERIOR_FORBIDDEN = _CLASSICAL_INFERENCE | frozenset(
    {
        "estimate",
        "conf_low",
        "conf_high",
        "conf_level",
        "model",
        "posterior",
        "draw",
        "draws",
        "chain",
        "artifact",
        "artifact_reference",
    }
)


def _is_nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _is_renderable_identity(value: object) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= 200 and value.isprintable()


def _has_runtime_type(value: object, expected: type[object]) -> bool:
    return isinstance(value, expected)


def _owned_float_array(values: object) -> FloatArray:
    candidate = np.asarray(values, dtype=np.float64)
    if candidate.ndim != 1 or not bool(np.isfinite(candidate).all()):
        raise ValueError(
            "reported coefficient values must be one-dimensional and finite"
        )
    return np.ndarray(
        candidate.shape,
        dtype=np.float64,
        buffer=candidate.tobytes(order="C"),
    )


def _validate_identity(
    terms: tuple[str, ...],
    identities: tuple[tuple[str, ...], ...],
    identity_columns: tuple[str, ...],
    is_intercepts: tuple[bool, ...],
) -> None:
    count = len(terms)
    if count < 1 or any(not _is_renderable_identity(term) for term in terms):
        raise ValueError("coefficient terms must be renderable strings of length 1-200")
    if identity_columns != tuple(
        column for column in IDENTITY_COLUMNS if column in identity_columns
    ):
        raise ValueError("coefficient identity columns are unsupported")
    if len(identities) != count or any(
        len(identity) != len(identity_columns)
        or any(not _is_renderable_identity(value) for value in identity)
        for identity in identities
    ):
        raise ValueError("coefficient structured identities are invalid")
    keys = tuple(
        (*identity, term) for identity, term in zip(identities, terms, strict=True)
    )
    if len(set(keys)) != count:
        raise ValueError("coefficient row identities must be unique")
    if len(is_intercepts) != count or any(
        type(value) is not bool for value in is_intercepts
    ):
        raise ValueError("coefficient intercept markers must be boolean")


@dataclass(frozen=True, slots=True)
class RobustCoefficientSummaryTable:
    """Owned rows for the approved R4-C ``robust_interval`` profile."""

    terms: tuple[str, ...]
    identities: tuple[tuple[str, ...], ...]
    identity_columns: tuple[str, ...]
    estimates: FloatArray
    conf_low: FloatArray
    conf_high: FloatArray
    is_intercepts: tuple[bool, ...]
    profile: Literal["robust_interval"] = "robust_interval"

    def __post_init__(self) -> None:
        _validate_identity(
            self.terms, self.identities, self.identity_columns, self.is_intercepts
        )
        arrays = tuple(
            _owned_float_array(value)
            for value in (self.estimates, self.conf_low, self.conf_high)
        )
        if any(array.size != len(self.terms) for array in arrays):
            raise ValueError("robust coefficient arrays must align")
        estimates, low, high = arrays
        if bool(((low > high) | (estimates < low) | (estimates > high)).any()):
            raise ValueError("robust intervals must be ordered and contain estimates")
        if self.profile != "robust_interval":
            raise ValueError("robust coefficient profile is unsupported")
        object.__setattr__(self, "estimates", estimates)
        object.__setattr__(self, "conf_low", low)
        object.__setattr__(self, "conf_high", high)

    @property
    def keys(self) -> tuple[tuple[str, ...], ...]:
        return tuple(
            (*identity, term)
            for identity, term in zip(self.identities, self.terms, strict=True)
        )


@dataclass(frozen=True, slots=True)
class PosteriorCoefficientSummaryTable:
    """Owned rows for the approved B5-C ``posterior_summary`` profile."""

    terms: tuple[str, ...]
    identities: tuple[tuple[str, ...], ...]
    identity_columns: tuple[str, ...]
    posterior_medians: FloatArray
    credible_low: FloatArray
    credible_high: FloatArray
    probability_above_null: FloatArray
    probability_below_null: FloatArray
    probability_at_null: FloatArray
    is_intercepts: tuple[bool, ...]
    profile: Literal["posterior_summary"] = "posterior_summary"

    def __post_init__(self) -> None:
        _validate_identity(
            self.terms, self.identities, self.identity_columns, self.is_intercepts
        )
        arrays = tuple(
            _owned_float_array(value)
            for value in (
                self.posterior_medians,
                self.credible_low,
                self.credible_high,
                self.probability_above_null,
                self.probability_below_null,
                self.probability_at_null,
            )
        )
        if any(array.size != len(self.terms) for array in arrays):
            raise ValueError("posterior coefficient arrays must align")
        median, low, high, above, below, at = arrays
        if bool(((low > high) | (median < low) | (median > high)).any()):
            raise ValueError(
                "credible intervals must be ordered and contain posterior medians"
            )
        if any(
            bool(((values < 0.0) | (values > 1.0)).any())
            for values in (above, below, at)
        ) or bool((np.abs(above + below + at - 1.0) > PROBABILITY_TOLERANCE).any()):
            raise ValueError("posterior directional probabilities must partition one")
        if self.profile != "posterior_summary":
            raise ValueError("posterior coefficient profile is unsupported")
        for name, value in zip(
            (
                "posterior_medians",
                "credible_low",
                "credible_high",
                "probability_above_null",
                "probability_below_null",
                "probability_at_null",
            ),
            arrays,
            strict=True,
        ):
            object.__setattr__(self, name, value)

    @property
    def keys(self) -> tuple[tuple[str, ...], ...]:
        return tuple(
            (*identity, term)
            for identity, term in zip(self.identities, self.terms, strict=True)
        )


def _validate_maximum(maximum_coefficients: int) -> None:
    if (
        type(maximum_coefficients) is not int
        or maximum_coefficients < 1
        or maximum_coefficients > HARD_MAX_COEFFICIENTS
    ):
        raise ValueError(
            "maximum_coefficients must be an integer from 1 through "
            f"{HARD_MAX_COEFFICIENTS}"
        )


def _select_frame(
    data: object,
    *,
    required: tuple[str, ...],
    forbidden: frozenset[str],
    maximum_coefficients: int,
    profile: str,
) -> tuple[pl.DataFrame, tuple[str, ...]]:
    if not isinstance(data, pl.DataFrame):
        raise TypeError(f"{profile} data must be a polars.DataFrame")
    _validate_maximum(maximum_coefficients)
    if not 1 <= data.height <= maximum_coefficients:
        raise ValueError(f"coefficient table requires 1-{maximum_coefficients} rows")
    missing = tuple(column for column in required if column not in data)
    if missing:
        raise ValueError(f"missing required {profile} column(s): {missing!r}")
    mixed = tuple(sorted(forbidden.intersection(data.columns)))
    if mixed:
        raise ValueError(f"{profile} input contains reserved column(s): {mixed!r}")
    identity_columns = tuple(column for column in IDENTITY_COLUMNS if column in data)
    selected_names = (*required, *identity_columns)
    if "is_intercept" in data:
        selected_names = (*selected_names, "is_intercept")
    selected = data.select(*selected_names)
    if any(selected.get_column(name).null_count() for name in selected_names):
        raise ValueError(f"{profile} participating columns cannot contain null values")
    for name in ("term", *identity_columns):
        if selected.get_column(name).dtype != pl.String:
            raise TypeError(f"column {name!r} must have a String dtype")
    if (
        "is_intercept" in selected
        and selected.get_column("is_intercept").dtype != pl.Boolean
    ):
        raise TypeError("column 'is_intercept' must have a Boolean dtype")
    for name in required:
        if name != "term" and not selected.get_column(name).dtype.is_numeric():
            raise TypeError(f"column {name!r} must have a numeric dtype")
    return selected, identity_columns


def _identity_values(
    selected: pl.DataFrame, identity_columns: tuple[str, ...]
) -> tuple[tuple[str, ...], ...]:
    return tuple(
        tuple(
            cast(str, selected.get_column(column)[index]) for column in identity_columns
        )
        for index in range(selected.height)
    )


def _intercepts(selected: pl.DataFrame) -> tuple[bool, ...]:
    if "is_intercept" not in selected:
        return (False,) * selected.height
    return tuple(cast(list[bool], selected.get_column("is_intercept").to_list()))


def _numeric(selected: pl.DataFrame, name: str) -> FloatArray:
    return _owned_float_array(selected.get_column(name).to_numpy())


def select_robust_coefficient_summaries(
    data: object, *, maximum_coefficients: int = DEFAULT_MAX_COEFFICIENTS
) -> RobustCoefficientSummaryTable:
    """Validate and own one strict R4-C reported robust table."""

    selected, identities = _select_frame(
        data,
        required=_ROBUST_REQUIRED,
        forbidden=_ROBUST_FORBIDDEN,
        maximum_coefficients=maximum_coefficients,
        profile="robust_interval",
    )
    return RobustCoefficientSummaryTable(
        tuple(cast(list[str], selected.get_column("term").to_list())),
        _identity_values(selected, identities),
        identities,
        _numeric(selected, "estimate"),
        _numeric(selected, "conf_low"),
        _numeric(selected, "conf_high"),
        _intercepts(selected),
    )


def select_posterior_coefficient_summaries(
    data: object, *, maximum_coefficients: int = DEFAULT_MAX_COEFFICIENTS
) -> PosteriorCoefficientSummaryTable:
    """Validate and own one strict B5-C reported posterior table."""

    selected, identities = _select_frame(
        data,
        required=_POSTERIOR_REQUIRED,
        forbidden=_POSTERIOR_FORBIDDEN,
        maximum_coefficients=maximum_coefficients,
        profile="posterior_summary",
    )
    return PosteriorCoefficientSummaryTable(
        tuple(cast(list[str], selected.get_column("term").to_list())),
        _identity_values(selected, identities),
        identities,
        _numeric(selected, "posterior_median"),
        _numeric(selected, "credible_low"),
        _numeric(selected, "credible_high"),
        _numeric(selected, "probability_above_null"),
        _numeric(selected, "probability_below_null"),
        _numeric(selected, "probability_at_null"),
        _intercepts(selected),
    )


def normalize_reported_text(value: object, label: str) -> str:
    """Normalize opaque provenance without interpreting the caller assertion."""

    if not isinstance(value, str):
        raise ValueError(f"{label} must be a nonempty string")
    if any(category(character).startswith("C") for character in value):
        raise ValueError(f"{label} cannot contain control characters")
    normalized = " ".join(value.split())
    if not normalized or len(normalized) > 200:
        raise ValueError(f"{label} must contain 1-200 Unicode scalar values")
    return normalized


@dataclass(frozen=True, slots=True)
class RobustCoefficientProvenanceResult:
    robust_method: str
    robust_tuning: str
    interval_method: str
    source: Literal["caller_reported_unverified"] = "caller_reported_unverified"

    def __post_init__(self) -> None:
        for value, label in (
            (self.robust_method, "robust_method"),
            (self.robust_tuning, "robust_tuning"),
            (self.interval_method, "interval_method"),
        ):
            if normalize_reported_text(value, label) != value:
                raise ValueError("robust provenance must already be normalized")
        if self.source != "caller_reported_unverified":
            raise ValueError("robust provenance source is unsupported")


@dataclass(frozen=True, slots=True)
class PosteriorCoefficientProvenanceResult:
    posterior_model: str
    likelihood: str
    prior_description: str
    computation_method: str
    source: Literal["caller_reported_unverified"] = "caller_reported_unverified"

    def __post_init__(self) -> None:
        for value, label in (
            (self.posterior_model, "posterior_model"),
            (self.likelihood, "likelihood"),
            (self.prior_description, "prior_description"),
            (self.computation_method, "computation_method"),
        ):
            if normalize_reported_text(value, label) != value:
                raise ValueError("posterior provenance must already be normalized")
        if self.source != "caller_reported_unverified":
            raise ValueError("posterior provenance source is unsupported")


@dataclass(frozen=True, slots=True)
class RobustCoefficientTermResult:
    identity: CoefficientIdentityResult
    is_intercept: bool
    source_position: int
    display_position: int
    estimate: float
    interval: IntervalResult

    def __post_init__(self) -> None:
        _validate_term_fields(
            self.is_intercept,
            self.source_position,
            self.display_position,
            self.estimate,
            self.interval,
            ROBUST_INTERVAL_METHOD,
        )


@dataclass(frozen=True, slots=True)
class PosteriorCoefficientSummaryResult:
    median: float
    interval: IntervalResult
    null_value: float
    probability_above_null: float
    probability_below_null: float
    probability_at_null: float

    def __post_init__(self) -> None:
        if not isfinite(self.median) or not isfinite(self.null_value):
            raise ValueError("posterior coefficient values must be finite")
        if (
            self.interval.target != "coefficient"
            or self.interval.method != POSTERIOR_INTERVAL_METHOD
            or not self.interval.low <= self.median <= self.interval.high
        ):
            raise ValueError("posterior credible interval is inconsistent")
        probabilities = (
            self.probability_above_null,
            self.probability_below_null,
            self.probability_at_null,
        )
        if any(
            not isfinite(value) or not 0.0 <= value <= 1.0 for value in probabilities
        ):
            raise ValueError("posterior directional probabilities must lie in [0, 1]")
        if abs(sum(probabilities) - 1.0) > PROBABILITY_TOLERANCE:
            raise ValueError("posterior directional probabilities must partition one")


@dataclass(frozen=True, slots=True)
class PosteriorCoefficientTermResult:
    identity: CoefficientIdentityResult
    is_intercept: bool
    source_position: int
    display_position: int
    summary: PosteriorCoefficientSummaryResult

    def __post_init__(self) -> None:
        _validate_term_fields(
            self.is_intercept,
            self.source_position,
            self.display_position,
            self.summary.median,
            self.summary.interval,
            POSTERIOR_INTERVAL_METHOD,
        )


def _validate_term_fields(
    is_intercept: bool,
    source_position: int,
    display_position: int,
    point: float,
    interval: IntervalResult,
    method: str,
) -> None:
    if type(is_intercept) is not bool:
        raise ValueError("coefficient intercept marker must be boolean")
    if any(
        type(value) is not int or value < 0
        for value in (source_position, display_position)
    ):
        raise ValueError("coefficient positions must be nonnegative integers")
    if not isfinite(point):
        raise ValueError("coefficient point must be finite")
    if (
        interval.target != "coefficient"
        or interval.method != method
        or not interval.low <= point <= interval.high
    ):
        raise ValueError("coefficient interval is inconsistent")


def _validate_result_common(
    *,
    identity_columns: tuple[str, ...],
    input_rows: int,
    retained_rows: int,
    source_order: tuple[CoefficientIdentityResult, ...],
    display_order: tuple[CoefficientIdentityResult, ...],
    term_identities: tuple[CoefficientIdentityResult, ...],
    term_source_positions: tuple[int, ...],
    term_display_positions: tuple[int, ...],
    excluded_intercepts: tuple[CoefficientIdentityResult, ...],
    declarations: tuple[str, str, str, str],
    null_value: float,
    level: float,
    stats_labels: bool,
    only_significant: bool,
    sort: str,
    limits: CoefficientTableResourceLimits,
    warnings: tuple[str, ...],
) -> None:
    if identity_columns != tuple(
        name for name in IDENTITY_COLUMNS if name in identity_columns
    ):
        raise ValueError("coefficient identity columns are unsupported")
    if any(not _is_nonempty_string(value) for value in declarations):
        raise ValueError("coefficient scale declarations are invalid")
    if not isfinite(null_value):
        raise ValueError("null_value must be finite")
    if type(input_rows) is not int or type(retained_rows) is not int:
        raise ValueError("coefficient row counts must be integers")
    if input_rows != retained_rows + len(excluded_intercepts) or retained_rows < 1:
        raise ValueError("coefficient row audit does not reconcile")
    if len(term_identities) != retained_rows or display_order != term_identities:
        raise ValueError("coefficient display order does not reconcile")
    source_terms = tuple(
        identity
        for _, identity in sorted(
            zip(term_source_positions, term_identities, strict=True),
            key=lambda item: item[0],
        )
    )
    if source_order != source_terms:
        raise ValueError("coefficient source order does not reconcile")
    if len({item.key for item in (*source_order, *excluded_intercepts)}) != input_rows:
        raise ValueError("coefficient identities must be unique")
    if term_display_positions != tuple(range(retained_rows)):
        raise ValueError("coefficient display positions must be complete")
    if len(set(term_source_positions)) != retained_rows or any(
        position < 0 or position >= input_rows for position in term_source_positions
    ):
        raise ValueError("coefficient source positions must be unique and in range")
    if not isfinite(level) or not 0.80 <= level <= 0.99:
        raise ValueError("reported interval level must lie within [0.80, 0.99]")
    if type(stats_labels) is not bool or type(only_significant) is not bool:
        raise ValueError("coefficient label policies must be boolean")
    if only_significant:
        raise ValueError("reported summaries do not support significance filtering")
    if sort not in {"none", "ascending", "descending"}:
        raise ValueError("coefficient sort is unsupported")
    if retained_rows > min(limits.maximum_coefficients, limits.maximum_rendered_points):
        raise ValueError("coefficient count exceeds resource limits")
    if stats_labels and retained_rows > limits.maximum_labels:
        raise ValueError("requested coefficient labels exceed maximum_labels")
    if any(not warning for warning in warnings):
        raise ValueError("coefficient warnings must be nonempty")


@dataclass(frozen=True, slots=True)
class RobustCoefficientTableResult:
    schema_version: Literal[2]
    analysis: Literal["ggcoefstats_coefficients"]
    mode: Literal["robust"]
    method: Literal["caller_reported_robust_interval"]
    compatibility_tier: Literal["adapted"]
    source_kind: Literal["table"]
    inference_profile: Literal["robust_interval"]
    identity_columns: tuple[str, ...]
    input_rows: int
    retained_rows: int
    source_order: tuple[CoefficientIdentityResult, ...]
    display_order: tuple[CoefficientIdentityResult, ...]
    terms: tuple[RobustCoefficientTermResult, ...]
    excluded_intercepts: tuple[CoefficientIdentityResult, ...]
    provenance: RobustCoefficientProvenanceResult
    estimate_label: str
    effect_scale: str
    effect_direction: str
    effect_units: str
    null_value: float
    conf_level: float
    interval_kind: Literal["confidence"]
    stats_labels: bool
    only_significant: bool
    sort: Literal["none", "ascending", "descending"]
    limits: CoefficientTableResourceLimits
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        if (
            self.schema_version != 2
            or self.analysis != "ggcoefstats_coefficients"
            or self.mode != "robust"
            or self.method != "caller_reported_robust_interval"
            or self.compatibility_tier != "adapted"
            or self.source_kind != "table"
            or self.inference_profile != "robust_interval"
            or self.interval_kind != "confidence"
            or not _has_runtime_type(self.provenance, RobustCoefficientProvenanceResult)
            or any(
                not _has_runtime_type(term, RobustCoefficientTermResult)
                for term in self.terms
            )
        ):
            raise ValueError("robust coefficient result identity is unsupported")
        _validate_result_common(
            identity_columns=self.identity_columns,
            input_rows=self.input_rows,
            retained_rows=self.retained_rows,
            source_order=self.source_order,
            display_order=self.display_order,
            term_identities=tuple(term.identity for term in self.terms),
            term_source_positions=tuple(term.source_position for term in self.terms),
            term_display_positions=tuple(term.display_position for term in self.terms),
            excluded_intercepts=self.excluded_intercepts,
            declarations=(
                self.estimate_label,
                self.effect_scale,
                self.effect_direction,
                self.effect_units,
            ),
            null_value=self.null_value,
            level=self.conf_level,
            stats_labels=self.stats_labels,
            only_significant=self.only_significant,
            sort=self.sort,
            limits=self.limits,
            warnings=self.warnings,
        )
        if any(
            abs(term.interval.level - self.conf_level) > 1e-15 for term in self.terms
        ):
            raise ValueError("robust interval levels must match conf_level")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PosteriorCoefficientTableResult:
    schema_version: Literal[3]
    analysis: Literal["ggcoefstats_coefficients"]
    mode: Literal["bayes"]
    method: Literal["caller_reported_posterior_summary"]
    compatibility_tier: Literal["adapted"]
    source_kind: Literal["table"]
    inference_profile: Literal["posterior_summary"]
    identity_columns: tuple[str, ...]
    input_rows: int
    retained_rows: int
    source_order: tuple[CoefficientIdentityResult, ...]
    display_order: tuple[CoefficientIdentityResult, ...]
    terms: tuple[PosteriorCoefficientTermResult, ...]
    excluded_intercepts: tuple[CoefficientIdentityResult, ...]
    provenance: PosteriorCoefficientProvenanceResult
    estimate_label: str
    effect_scale: str
    effect_direction: str
    effect_units: str
    null_value: float
    credible_level: float
    interval_kind: Literal["equal_tail_credible"]
    stats_labels: bool
    only_significant: bool
    sort: Literal["none", "ascending", "descending"]
    limits: CoefficientTableResourceLimits
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        if (
            self.schema_version != 3
            or self.analysis != "ggcoefstats_coefficients"
            or self.mode != "bayes"
            or self.method != "caller_reported_posterior_summary"
            or self.compatibility_tier != "adapted"
            or self.source_kind != "table"
            or self.inference_profile != "posterior_summary"
            or self.interval_kind != "equal_tail_credible"
            or not _has_runtime_type(
                self.provenance, PosteriorCoefficientProvenanceResult
            )
            or any(
                not _has_runtime_type(term, PosteriorCoefficientTermResult)
                for term in self.terms
            )
        ):
            raise ValueError("posterior coefficient result identity is unsupported")
        _validate_result_common(
            identity_columns=self.identity_columns,
            input_rows=self.input_rows,
            retained_rows=self.retained_rows,
            source_order=self.source_order,
            display_order=self.display_order,
            term_identities=tuple(term.identity for term in self.terms),
            term_source_positions=tuple(term.source_position for term in self.terms),
            term_display_positions=tuple(term.display_position for term in self.terms),
            excluded_intercepts=self.excluded_intercepts,
            declarations=(
                self.estimate_label,
                self.effect_scale,
                self.effect_direction,
                self.effect_units,
            ),
            null_value=self.null_value,
            level=self.credible_level,
            stats_labels=self.stats_labels,
            only_significant=self.only_significant,
            sort=self.sort,
            limits=self.limits,
            warnings=self.warnings,
        )
        if any(
            abs(term.summary.interval.level - self.credible_level) > 1e-15
            or term.summary.null_value != self.null_value
            for term in self.terms
        ):
            raise ValueError("posterior interval level or null does not match result")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


ReportedCoefficientTable = (
    RobustCoefficientSummaryTable | PosteriorCoefficientSummaryTable
)
ReportedCoefficientResult = (
    RobustCoefficientTableResult | PosteriorCoefficientTableResult
)


@dataclass(frozen=True, slots=True)
class ReportedCoefficientAnalysis:
    table: ReportedCoefficientTable
    result: ReportedCoefficientResult

    def __post_init__(self) -> None:
        if isinstance(self.table, RobustCoefficientSummaryTable):
            if not isinstance(self.result, RobustCoefficientTableResult):
                raise ValueError("robust coefficient table and result mode must match")
            points = self.table.estimates
            result_points = tuple(term.estimate for term in self.result.terms)
        else:
            if not isinstance(self.result, PosteriorCoefficientTableResult):
                raise ValueError(
                    "posterior coefficient table and result mode must match"
                )
            points = self.table.posterior_medians
            result_points = tuple(term.summary.median for term in self.result.terms)
        retained_keys = {item.key for item in self.result.source_order}
        expected_keys = tuple(key for key in self.table.keys if key in retained_keys)
        result_keys = tuple(item.key for item in self.result.source_order)
        if expected_keys != result_keys:
            raise ValueError(
                "reported coefficient table and result identities must match"
            )
        expected_points = {index: float(value) for index, value in enumerate(points)}
        result_terms = self.result.terms
        if any(
            expected_points[term.source_position] != point
            for term, point in zip(result_terms, result_points, strict=True)
        ):
            raise ValueError("reported coefficient table and result points must match")


def _number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(
        value, (int, float, np.integer, np.floating)
    ):
        raise ValueError(f"{label} must be finite")
    result = float(cast(Any, value))
    if not isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def analyze_reported_coefficients(
    data: object,
    *,
    mode: Literal["robust", "bayes"],
    estimate_label: str,
    effect_scale: str,
    effect_direction: str,
    effect_units: str,
    null_value: float,
    conf_level: float,
    credible_level: float,
    stats_labels: bool,
    only_significant: bool,
    exclude_intercept: bool,
    sort: str,
    maximum_coefficients: int,
    maximum_rendered_points: int,
    maximum_labels: int,
    robust_method: str,
    robust_tuning: str,
    interval_method: str,
    posterior_model: str,
    likelihood: str,
    prior_description: str,
    computation_method: str,
) -> ReportedCoefficientAnalysis:
    """Create one renderer-independent R4-C or B5-C result."""

    declarations = tuple(
        normalize_reported_text(value, label)
        for value, label in (
            (estimate_label, "estimate_label"),
            (effect_scale, "effect_scale"),
            (effect_direction, "effect_direction"),
            (effect_units, "effect_units"),
        )
    )
    null = _number(null_value, "null_value")
    if any(
        type(value) is not bool
        for value in (stats_labels, only_significant, exclude_intercept)
    ):
        raise TypeError("coefficient label and intercept options must be boolean")
    if only_significant:
        raise ValueError("only_significant=True is unavailable for reported summaries")
    if sort not in {"none", "ascending", "descending"}:
        raise ValueError("sort must be 'none', 'ascending', or 'descending'")
    for value, label, hard in (
        (maximum_coefficients, "maximum_coefficients", HARD_MAX_COEFFICIENTS),
        (maximum_rendered_points, "maximum_rendered_points", HARD_MAX_RENDERED_POINTS),
        (maximum_labels, "maximum_labels", HARD_MAX_LABELS),
    ):
        if type(value) is not int or not 1 <= value <= hard:
            raise ValueError(f"{label} must be an integer from 1 through {hard}")

    if mode == "robust":
        if credible_level != 0.95:
            raise ValueError("credible_level is unavailable in robust mode")
        confidence = _number(conf_level, "conf_level")
        if not 0.80 <= confidence <= 0.99:
            raise ValueError("conf_level must lie within [0.80, 0.99]")
        provenance: (
            RobustCoefficientProvenanceResult | PosteriorCoefficientProvenanceResult
        ) = RobustCoefficientProvenanceResult(
            normalize_reported_text(robust_method, "robust_method"),
            normalize_reported_text(robust_tuning, "robust_tuning"),
            normalize_reported_text(interval_method, "interval_method"),
        )
        if any((posterior_model, likelihood, prior_description, computation_method)):
            raise ValueError("Bayesian provenance cannot be used in robust mode")
        table: ReportedCoefficientTable = select_robust_coefficient_summaries(
            data, maximum_coefficients=maximum_coefficients
        )
        points = table.estimates
    else:
        if conf_level != 0.95:
            raise ValueError("conf_level is unavailable in Bayesian mode")
        confidence = _number(credible_level, "credible_level")
        if not 0.80 <= confidence <= 0.99:
            raise ValueError("credible_level must lie within [0.80, 0.99]")
        provenance = PosteriorCoefficientProvenanceResult(
            normalize_reported_text(posterior_model, "posterior_model"),
            normalize_reported_text(likelihood, "likelihood"),
            normalize_reported_text(prior_description, "prior_description"),
            normalize_reported_text(computation_method, "computation_method"),
        )
        if any((robust_method, robust_tuning, interval_method)):
            raise ValueError("robust provenance cannot be used in Bayesian mode")
        table = select_posterior_coefficient_summaries(
            data, maximum_coefficients=maximum_coefficients
        )
        points = table.posterior_medians

    all_identities = tuple(
        CoefficientIdentityResult(
            identity[table.identity_columns.index("response")]
            if "response" in table.identity_columns
            else None,
            identity[table.identity_columns.index("component")]
            if "component" in table.identity_columns
            else None,
            identity[table.identity_columns.index("group")]
            if "group" in table.identity_columns
            else None,
            term,
        )
        for identity, term in zip(table.identities, table.terms, strict=True)
    )
    retained_indices = [
        index
        for index, marker in enumerate(table.is_intercepts)
        if not (exclude_intercept and marker)
    ]
    if not retained_indices:
        raise ValueError("exclude_intercept removed every coefficient")
    if len(retained_indices) > maximum_rendered_points:
        raise ValueError("coefficient count exceeds maximum_rendered_points")
    if stats_labels and len(retained_indices) > maximum_labels:
        raise ValueError("requested coefficient labels exceed maximum_labels")
    if sort != "none":
        retained_indices.sort(
            key=lambda index: (
                float(points[index]) if sort == "ascending" else -float(points[index]),
                index,
            )
        )
    source_order = tuple(
        all_identities[index]
        for index in range(len(all_identities))
        if index in retained_indices
    )
    excluded = tuple(
        identity
        for identity, marker in zip(all_identities, table.is_intercepts, strict=True)
        if exclude_intercept and marker
    )
    limits = CoefficientTableResourceLimits(
        maximum_coefficients, maximum_rendered_points, maximum_labels
    )
    if isinstance(table, RobustCoefficientSummaryTable):
        robust_terms = tuple(
            RobustCoefficientTermResult(
                all_identities[index],
                table.is_intercepts[index],
                index,
                display_position,
                float(table.estimates[index]),
                IntervalResult(
                    "coefficient",
                    ROBUST_INTERVAL_METHOD,
                    confidence,
                    float(table.conf_low[index]),
                    float(table.conf_high[index]),
                ),
            )
            for display_position, index in enumerate(retained_indices)
        )
        if not isinstance(provenance, RobustCoefficientProvenanceResult):
            raise AssertionError("robust provenance mode was lost")
        result: ReportedCoefficientResult = RobustCoefficientTableResult(
            2,
            "ggcoefstats_coefficients",
            "robust",
            "caller_reported_robust_interval",
            "adapted",
            "table",
            "robust_interval",
            table.identity_columns,
            len(table.terms),
            len(robust_terms),
            source_order,
            tuple(term.identity for term in robust_terms),
            robust_terms,
            excluded,
            provenance,
            declarations[0],
            declarations[1],
            declarations[2],
            declarations[3],
            null,
            confidence,
            "confidence",
            stats_labels,
            False,
            cast(Any, sort),
            limits,
            (),
        )
    else:
        posterior_terms = tuple(
            PosteriorCoefficientTermResult(
                all_identities[index],
                table.is_intercepts[index],
                index,
                display_position,
                PosteriorCoefficientSummaryResult(
                    float(table.posterior_medians[index]),
                    IntervalResult(
                        "coefficient",
                        POSTERIOR_INTERVAL_METHOD,
                        confidence,
                        float(table.credible_low[index]),
                        float(table.credible_high[index]),
                    ),
                    null,
                    float(table.probability_above_null[index]),
                    float(table.probability_below_null[index]),
                    float(table.probability_at_null[index]),
                ),
            )
            for display_position, index in enumerate(retained_indices)
        )
        if not isinstance(provenance, PosteriorCoefficientProvenanceResult):
            raise AssertionError("posterior provenance mode was lost")
        result = PosteriorCoefficientTableResult(
            3,
            "ggcoefstats_coefficients",
            "bayes",
            "caller_reported_posterior_summary",
            "adapted",
            "table",
            "posterior_summary",
            table.identity_columns,
            len(table.terms),
            len(posterior_terms),
            source_order,
            tuple(term.identity for term in posterior_terms),
            posterior_terms,
            excluded,
            provenance,
            declarations[0],
            declarations[1],
            declarations[2],
            declarations[3],
            null,
            confidence,
            "equal_tail_credible",
            stats_labels,
            False,
            cast(Any, sort),
            limits,
            (),
        )
    return ReportedCoefficientAnalysis(table, result)
