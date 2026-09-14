"""Approved M5A coefficient-table selection and fitted-OLS adaptation."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from importlib.metadata import version
from math import isfinite
from typing import Any, Protocol, cast

import numpy as np
import polars as pl

from plotsalot.coefficient_data import (
    DEFAULT_MAX_COEFFICIENTS,
    HARD_MAX_COEFFICIENTS,
    CoefficientTable,
    select_coefficients,
)
from plotsalot.coefficient_result import (
    CoefficientIdentityResult,
    CoefficientModelSummaryResult,
    CoefficientTableResourceLimits,
    CoefficientTableResult,
    ReportedCoefficientInferenceResult,
    ReportedCoefficientTermResult,
)
from plotsalot.result import IntervalResult

DEFAULT_MAX_RENDERED_POINTS = 500
DEFAULT_MAX_LABELS = 200
HARD_MAX_RENDERED_POINTS = 1_000
HARD_MAX_LABELS = 1_000


class _ModelData(Protocol):
    const_idx: object


class _OLSModel(Protocol):
    exog_names: object
    rank: object
    k_constant: object
    data: _ModelData


class _OLSWrapper(Protocol):
    model: _OLSModel
    params: object
    bse: object
    tvalues: object
    pvalues: object
    nobs: object
    df_model: object
    df_resid: object
    cov_type: object
    use_t: object
    aic: object
    bic: object

    def conf_int(self, *, alpha: float) -> object: ...


@dataclass(frozen=True, slots=True)
class TableCoefficientAnalysis:
    table: CoefficientTable
    result: CoefficientTableResult

    def __post_init__(self) -> None:
        source = tuple(
            term.identity.key
            for term in sorted(self.result.terms, key=lambda item: item.source_position)
        )
        retained_keys = tuple(
            key
            for key in self.table.keys
            if key in {item.key for item in self.result.source_order}
        )
        if source != retained_keys:
            raise ValueError(
                "coefficient analysis table and result identities must match"
            )
        expected = {
            index: float(value) for index, value in enumerate(self.table.estimates)
        }
        if any(
            expected[term.source_position] != term.estimate
            for term in self.result.terms
        ):
            raise ValueError("coefficient analysis estimates must match")


def _string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a nonempty string")
    return value


def _number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(
        value, (int, float, np.integer, np.floating)
    ):
        raise ValueError(f"{label} must be finite")
    result = float(cast(Any, value))
    if not isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def _vector(
    value: object, name: str, count: int
) -> np.ndarray[Any, np.dtype[np.float64]]:
    try:
        result = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Statsmodels {name} must be numeric") from error
    if result.ndim != 1 or result.size != count or not bool(np.isfinite(result).all()):
        raise ValueError(f"Statsmodels {name} must be a finite aligned vector")
    return result


def _adapt_ols(
    value: object, conf_level: float, maximum_coefficients: int
) -> tuple[CoefficientTable, CoefficientModelSummaryResult]:
    linear_model = import_module("statsmodels.regression.linear_model")
    wrapper_type = linear_model.RegressionResultsWrapper
    ols_type = linear_model.OLS
    if type(value) is not wrapper_type:
        raise TypeError("model input must be an exact RegressionResultsWrapper")
    wrapped = cast(_OLSWrapper, value)
    if type(wrapped.model) is not ols_type:
        raise TypeError("only an exact fitted Statsmodels OLS model is supported")
    names_value = wrapped.model.exog_names
    if not isinstance(names_value, list):
        raise ValueError("Statsmodels coefficient names must be a list")
    raw_names = cast(list[object], names_value)
    if any(not isinstance(name, str) or not name for name in raw_names):
        raise ValueError(
            "Statsmodels coefficient names must be unique nonempty strings"
        )
    names = [cast(str, name) for name in raw_names]
    if len(set(names)) != len(names):
        raise ValueError(
            "Statsmodels coefficient names must be unique nonempty strings"
        )
    count = len(names)
    if count < 1 or count > maximum_coefficients:
        raise ValueError("Statsmodels parameter count exceeds the configured boundary")
    params = _vector(wrapped.params, "params", count)
    errors = _vector(wrapped.bse, "bse", count)
    statistics = _vector(wrapped.tvalues, "tvalues", count)
    p_values = _vector(wrapped.pvalues, "pvalues", count)
    if bool((errors <= 0.0).any()) or bool(((p_values < 0.0) | (p_values > 1.0)).any()):
        raise ValueError("Statsmodels standard errors or p-values are invalid")
    intervals = np.asarray(wrapped.conf_int(alpha=1.0 - conf_level), dtype=np.float64)
    if intervals.shape != (count, 2) or not bool(np.isfinite(intervals).all()):
        raise ValueError("Statsmodels confidence intervals must be finite and aligned")
    if bool(
        (
            (intervals[:, 0] > intervals[:, 1])
            | (params < intervals[:, 0])
            | (params > intervals[:, 1])
        ).any()
    ):
        raise ValueError("Statsmodels intervals must contain their estimates")
    cov_type = wrapped.cov_type
    if cov_type not in {"nonrobust", "HC3"}:
        raise ValueError("Statsmodels cov_type must be 'nonrobust' or 'HC3'")
    use_t = wrapped.use_t
    if type(use_t) is not bool:
        raise ValueError("Statsmodels use_t must be boolean")
    nobs_float = _number(wrapped.nobs, "Statsmodels nobs")
    if not nobs_float.is_integer() or not 1 <= nobs_float <= 2**53:
        raise ValueError(
            "Statsmodels nobs must be an exactly representable positive integer"
        )
    df_model = _number(wrapped.df_model, "Statsmodels df_model")
    df_resid = _number(wrapped.df_resid, "Statsmodels df_resid")
    if df_resid <= 0.0:
        raise ValueError("Statsmodels df_resid must be positive")
    rank_value = _number(wrapped.model.rank, "Statsmodels rank")
    if not rank_value.is_integer() or rank_value != count:
        raise ValueError("Statsmodels OLS design must have full reported column rank")
    rank = int(rank_value)
    k_constant = wrapped.model.k_constant
    const_idx = wrapped.model.data.const_idx
    if type(k_constant) is not int or k_constant not in {0, 1}:
        raise ValueError("Statsmodels constant metadata is ambiguous")
    if k_constant == 0:
        if const_idx is not None:
            raise ValueError("Statsmodels constant metadata disagrees")
        intercepts = [False] * count
    else:
        if type(const_idx) is not int or not 0 <= const_idx < count:
            raise ValueError("Statsmodels constant index is invalid")
        intercepts = [index == const_idx for index in range(count)]
    aic = _number(wrapped.aic, "Statsmodels AIC")
    bic = _number(wrapped.bic, "Statsmodels BIC")
    kind = "t" if use_t else "z"
    frame_data: dict[str, object] = {
        "term": names,
        "estimate": params,
        "conf_low": intervals[:, 0],
        "conf_high": intervals[:, 1],
        "standard_error": errors,
        "statistic_kind": [kind] * count,
        "statistic": statistics,
        "p_value": p_values,
        "is_intercept": intercepts,
    }
    if use_t:
        frame_data["df"] = [df_resid] * count
    table = select_coefficients(
        pl.DataFrame(frame_data), maximum_coefficients=maximum_coefficients
    )
    summary = CoefficientModelSummaryResult(
        "statsmodels.regression.linear_model.OLS",
        "statsmodels.regression.linear_model.RegressionResultsWrapper",
        version("statsmodels"),
        cast(Any, cov_type),
        use_t,
        int(nobs_float),
        df_model,
        df_resid,
        rank,
        count,
        aic,
        bic,
    )
    return table, summary


def analyze_coefficients(
    data: object,
    *,
    estimate_label: str,
    effect_scale: str,
    effect_direction: str,
    effect_units: str,
    null_value: float,
    conf_level: float,
    alpha: float,
    stats_labels: bool,
    only_significant: bool,
    exclude_intercept: bool,
    sort: str,
    maximum_coefficients: int = DEFAULT_MAX_COEFFICIENTS,
    maximum_rendered_points: int = DEFAULT_MAX_RENDERED_POINTS,
    maximum_labels: int = DEFAULT_MAX_LABELS,
) -> TableCoefficientAnalysis:
    """Create the approved renderer-independent M5A coefficient result."""

    declarations = tuple(
        _string(value, label)
        for value, label in (
            (estimate_label, "estimate_label"),
            (effect_scale, "effect_scale"),
            (effect_direction, "effect_direction"),
            (effect_units, "effect_units"),
        )
    )
    null = _number(null_value, "null_value")
    confidence = _number(conf_level, "conf_level")
    significance = _number(alpha, "alpha")
    if not 0.0 < confidence < 1.0 or not 0.0 < significance < 1.0:
        raise ValueError("conf_level and alpha must lie within (0, 1)")
    if any(
        type(value) is not bool
        for value in (stats_labels, only_significant, exclude_intercept)
    ):
        raise TypeError("coefficient label and intercept options must be boolean")
    if only_significant and not stats_labels:
        raise ValueError("only_significant requires stats_labels=True")
    if sort not in {"none", "ascending", "descending"}:
        raise ValueError("sort must be 'none', 'ascending', or 'descending'")
    for value, label, hard in (
        (maximum_coefficients, "maximum_coefficients", HARD_MAX_COEFFICIENTS),
        (maximum_rendered_points, "maximum_rendered_points", HARD_MAX_RENDERED_POINTS),
        (maximum_labels, "maximum_labels", HARD_MAX_LABELS),
    ):
        if type(value) is not int or not 1 <= value <= hard:
            raise ValueError(f"{label} must be an integer from 1 through {hard}")

    model_summary: CoefficientModelSummaryResult | None = None
    if isinstance(data, pl.DataFrame):
        table = select_coefficients(data, maximum_coefficients=maximum_coefficients)
        source_kind = "table"
        inference_source = "reported"
    else:
        if null != 0.0:
            raise ValueError("the Statsmodels OLS adapter requires null_value=0")
        table, model_summary = _adapt_ols(data, confidence, maximum_coefficients)
        source_kind = "statsmodels_ols"
        inference_source = "statsmodels_ols"
    if stats_labels and table.profile not in {"full_t", "full_z"}:
        raise ValueError("stats_labels=True requires a full_t or full_z profile")

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
        for index, is_intercept in enumerate(table.is_intercepts)
        if not (exclude_intercept and is_intercept)
    ]
    if not retained_indices:
        raise ValueError("exclude_intercept removed every coefficient")
    if len(retained_indices) > maximum_rendered_points:
        raise ValueError("coefficient count exceeds maximum_rendered_points")
    if sort != "none":
        retained_indices.sort(
            key=lambda index: (
                float(table.estimates[index])
                if sort == "ascending"
                else -float(table.estimates[index]),
                index,
            ),
        )

    terms: list[ReportedCoefficientTermResult] = []
    for display_position, index in enumerate(retained_indices):
        inference: ReportedCoefficientInferenceResult | None = None
        if table.profile != "estimate_only":
            if table.conf_low is None or table.conf_high is None:
                raise AssertionError("resolved coefficient profile lost its interval")
            interval = IntervalResult(
                "coefficient",
                inference_source,
                confidence,
                float(table.conf_low[index]),
                float(table.conf_high[index]),
            )
            if table.profile == "interval":
                inference = ReportedCoefficientInferenceResult(
                    inference_source, interval, None, None, None, None, None, None
                )
            else:
                arrays = (table.standard_errors, table.statistics, table.p_values)
                if any(array is None for array in arrays):
                    raise AssertionError("resolved full profile lost inference fields")
                standard_errors = cast(
                    np.ndarray[Any, np.dtype[np.float64]], table.standard_errors
                )
                statistics = cast(
                    np.ndarray[Any, np.dtype[np.float64]], table.statistics
                )
                p_values = cast(np.ndarray[Any, np.dtype[np.float64]], table.p_values)
                p_value = float(p_values[index])
                df = float(table.dfs[index]) if table.dfs is not None else None
                inference = ReportedCoefficientInferenceResult(
                    inference_source,
                    interval,
                    float(standard_errors[index]),
                    "t" if table.profile == "full_t" else "z",
                    float(statistics[index]),
                    df,
                    p_value,
                    p_value < significance,
                )
        terms.append(
            ReportedCoefficientTermResult(
                all_identities[index],
                table.is_intercepts[index],
                index,
                display_position,
                float(table.estimates[index]),
                inference,
            )
        )
    excluded = tuple(
        identity
        for identity, marker in zip(all_identities, table.is_intercepts, strict=True)
        if exclude_intercept and marker
    )
    source_order = tuple(
        all_identities[index]
        for index in range(len(all_identities))
        if index in retained_indices
    )
    result = CoefficientTableResult(
        1,
        "ggcoefstats_coefficients",
        cast(Any, source_kind),
        cast(Any, table.profile),
        table.identity_columns,
        len(table.terms),
        len(terms),
        source_order,
        tuple(term.identity for term in terms),
        tuple(terms),
        excluded,
        model_summary,
        declarations[0],
        declarations[1],
        declarations[2],
        declarations[3],
        null,
        confidence,
        significance,
        stats_labels,
        only_significant,
        cast(Any, sort),
        CoefficientTableResourceLimits(
            maximum_coefficients, maximum_rendered_points, maximum_labels
        ),
        (),
    )
    return TableCoefficientAnalysis(table, result)
