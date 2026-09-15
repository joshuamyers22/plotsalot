"""Approved M5B frequentist random-effects meta-analysis."""

from __future__ import annotations

from builtins import type as builtin_type
from collections.abc import Callable
from dataclasses import dataclass
from importlib import import_module
from math import sqrt
from typing import Literal, Protocol, cast, overload

import numpy as np

from plotsalot.coefficient_data import (
    DEFAULT_MAX_STUDIES,
    StudyEffectTable,
    select_study_effects,
)
from plotsalot.coefficient_meta_analysis import (
    DEFAULT_MAXIMUM_WORK,
    BayesianMetaAnalysis,
    RobustMetaAnalysis,
    analyze_bayesian_meta,
    analyze_robust_meta,
)
from plotsalot.coefficient_result import (
    CoefficientInferenceResult,
    CoefficientResourceLimits,
    CoefficientResult,
    CoefficientTermResult,
    HeterogeneityResult,
    MetaAnalysisResult,
    MetaConvergenceResult,
    PooledEffectResult,
    PredictionResult,
)
from plotsalot.coefficient_summary_analysis import (
    ReportedCoefficientAnalysis,
    analyze_reported_coefficients,
)
from plotsalot.coefficient_table_analysis import (
    DEFAULT_MAX_LABELS as DEFAULT_MAX_COEFFICIENT_LABELS,
)
from plotsalot.coefficient_table_analysis import (
    DEFAULT_MAX_RENDERED_POINTS as DEFAULT_MAX_COEFFICIENT_POINTS,
)
from plotsalot.coefficient_table_analysis import (
    TableCoefficientAnalysis,
    analyze_coefficients,
)
from plotsalot.result import IntervalResult

DEFAULT_MAX_LABELS = 200
DEFAULT_MAX_RENDERED_POINTS = 500
HARD_MAX_LABELS = 1_000
HARD_MAX_RENDERED_POINTS = 1_000
_SCORE_FACTOR = 1e-12
_ROOT_ABSOLUTE_TOLERANCE = 1e-12
_ROOT_RELATIVE_TOLERANCE = float(8.0 * np.finfo(np.float64).eps)
_MAX_BRACKET_EXPANSIONS = 60
_MAX_ROOT_ITERATIONS = 100


class _ContinuousDistribution(Protocol):
    def ppf(self, probability: float, *parameters: float) -> float: ...

    def sf(self, value: float, *parameters: float) -> float: ...


class _ScipyStats(Protocol):
    norm: _ContinuousDistribution
    t: _ContinuousDistribution
    chi2: _ContinuousDistribution


class _RootResult(Protocol):
    converged: bool
    iterations: int


class _ScipyOptimize(Protocol):
    def brentq(
        self,
        function: Callable[[float], float],
        low: float,
        high: float,
        *,
        xtol: float,
        rtol: float,
        maxiter: int,
        full_output: bool,
        disp: bool,
    ) -> tuple[float, _RootResult]: ...


scipy_stats = cast(_ScipyStats, import_module("scipy.stats"))
scipy_optimize = cast(_ScipyOptimize, import_module("scipy.optimize"))


@dataclass(frozen=True, slots=True)
class CoefficientAnalysis:
    table: StudyEffectTable
    result: CoefficientResult

    def __post_init__(self) -> None:
        if self.table.terms != self.result.source_order:
            raise ValueError("coefficient analysis table and result terms must match")
        if tuple(float(value) for value in self.table.estimates) != tuple(
            term.estimate for term in self.result.terms
        ):
            raise ValueError("coefficient analysis estimates must match")
        if tuple(float(value) for value in self.table.standard_errors) != tuple(
            term.inference.standard_error for term in self.result.terms
        ):
            raise ValueError("coefficient analysis standard errors must match")


def _string_option(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a nonempty string")
    return value


def _numeric_option(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be finite")
    numeric = float(value)
    if not np.isfinite(numeric):
        raise ValueError(f"{label} must be finite")
    return numeric


def _validate_m6c_study_identities(terms: tuple[str, ...]) -> None:
    if any(not 1 <= len(term) <= 200 or not term.isprintable() for term in terms):
        raise ValueError(
            "M6C study identities must be renderable strings of length 1-200"
        )


def _score(y: np.ndarray, variances: np.ndarray, tau_squared: float) -> float:
    weights = 1.0 / (variances + tau_squared)
    total = float(np.sum(weights))
    mean = float(np.sum(weights * y) / total)
    residual = y - mean
    return float(
        np.sum(weights * weights * residual * residual)
        - total
        + np.sum(weights * weights) / total
    )


def _restricted_log_likelihood(
    y: np.ndarray, variances: np.ndarray, tau_squared: float
) -> float:
    weights = 1.0 / (variances + tau_squared)
    total = float(np.sum(weights))
    mean = float(np.sum(weights * y) / total)
    return float(
        -0.5
        * (
            np.sum(np.log(variances + tau_squared))
            + np.log(total)
            + np.sum(weights * (y - mean) ** 2)
        )
    )


def _reml(
    estimates: np.ndarray,
    standard_errors: np.ndarray,
    null_value: float,
) -> tuple[float, MetaConvergenceResult]:
    centered = estimates - null_value
    scale_factor = max(float(np.max(np.abs(centered))), float(np.max(standard_errors)))
    y = centered / scale_factor
    errors = standard_errors / scale_factor
    variances = errors * errors
    score_at_zero = _score(y, variances, 0.0)
    score_tolerance = _SCORE_FACTOR * max(1.0, float(np.sum(1.0 / variances)))
    if score_at_zero <= score_tolerance:
        return 0.0, MetaConvergenceResult(
            method="reml_intercept_only",
            converged=True,
            boundary=True,
            scale_factor=scale_factor,
            score_at_zero=score_at_zero,
            score_at_solution=score_at_zero,
            bracket_low=0.0,
            bracket_high=0.0,
            bracket_expansions=0,
            iterations=0,
            score_tolerance=score_tolerance,
            absolute_tolerance=_ROOT_ABSOLUTE_TOLERANCE,
            relative_tolerance=_ROOT_RELATIVE_TOLERANCE,
        )

    upper = max(
        1.0,
        float(np.var(y, ddof=1)),
        float(np.max(variances)),
    )
    expansions = 0
    upper_score = _score(y, variances, upper)
    while upper_score >= 0.0 and expansions < _MAX_BRACKET_EXPANSIONS:
        upper *= 2.0
        expansions += 1
        upper_score = _score(y, variances, upper)
    if not np.isfinite(upper_score) or upper_score >= 0.0:
        raise ValueError("REML score root could not be bracketed")

    def objective(value: float) -> float:
        return _score(y, variances, value)

    root, details = scipy_optimize.brentq(
        objective,
        0.0,
        upper,
        xtol=_ROOT_ABSOLUTE_TOLERANCE,
        rtol=_ROOT_RELATIVE_TOLERANCE,
        maxiter=_MAX_ROOT_ITERATIONS,
        full_output=True,
        disp=False,
    )
    root = float(root)
    score_at_solution = _score(y, variances, root)
    if not details.converged or not np.isfinite(root) or root < 0.0:
        raise ValueError("REML score root did not converge")
    if abs(score_at_solution) > score_tolerance:
        raise ValueError("REML score root exceeds its convergence tolerance")
    if _restricted_log_likelihood(y, variances, root) <= _restricted_log_likelihood(
        y, variances, 0.0
    ):
        raise ValueError("REML solution does not improve restricted likelihood")

    tau_squared = root * scale_factor * scale_factor
    if not np.isfinite(tau_squared) or tau_squared < 0.0:
        raise ValueError("REML produced an inadmissible between-study variance")
    return tau_squared, MetaConvergenceResult(
        method="reml_intercept_only",
        converged=True,
        boundary=False,
        scale_factor=scale_factor,
        score_at_zero=score_at_zero,
        score_at_solution=score_at_solution,
        bracket_low=0.0,
        bracket_high=upper,
        bracket_expansions=expansions,
        iterations=int(details.iterations),
        score_tolerance=score_tolerance,
        absolute_tolerance=_ROOT_ABSOLUTE_TOLERANCE,
        relative_tolerance=_ROOT_RELATIVE_TOLERANCE,
    )


@overload
def analyze_ggcoefstats(
    data: object,
    *,
    meta_analytic_effect: Literal[True],
    type: Literal["parametric"] = "parametric",
    estimate_label: str = "",
    estimand: str = "",
    effect_scale: str = "",
    effect_direction: str = "",
    effect_units: str = "",
    dependence: str = "independent",
    null_value: float = 0.0,
    conf_level: float = 0.95,
    credible_level: float = 0.95,
    alpha: float = 0.05,
    stats_labels: bool = True,
    only_significant: bool = False,
    exclude_intercept: bool = False,
    sort: str = "none",
    maximum_coefficients: int = 500,
    maximum_studies: int = DEFAULT_MAX_STUDIES,
    maximum_rendered_points: int = DEFAULT_MAX_COEFFICIENT_POINTS,
    maximum_labels: int = DEFAULT_MAX_COEFFICIENT_LABELS,
    robust_method: str = "",
    robust_tuning: str = "",
    interval_method: str = "",
    posterior_model: str = "",
    likelihood: str = "",
    prior_description: str = "",
    computation_method: str = "",
    prior_mean_scale: float | None = None,
    prior_tau_scale: float | None = None,
    maximum_work: int = DEFAULT_MAXIMUM_WORK,
) -> CoefficientAnalysis: ...


@overload
def analyze_ggcoefstats(
    data: object,
    *,
    meta_analytic_effect: Literal[False] = False,
    type: Literal["parametric"] = "parametric",
    estimate_label: str = "",
    estimand: str = "",
    effect_scale: str = "",
    effect_direction: str = "",
    effect_units: str = "",
    dependence: str = "independent",
    null_value: float = 0.0,
    conf_level: float = 0.95,
    credible_level: float = 0.95,
    alpha: float = 0.05,
    stats_labels: bool = True,
    only_significant: bool = False,
    exclude_intercept: bool = False,
    sort: str = "none",
    maximum_coefficients: int = 500,
    maximum_studies: int = DEFAULT_MAX_STUDIES,
    maximum_rendered_points: int = DEFAULT_MAX_COEFFICIENT_POINTS,
    maximum_labels: int = DEFAULT_MAX_COEFFICIENT_LABELS,
    robust_method: str = "",
    robust_tuning: str = "",
    interval_method: str = "",
    posterior_model: str = "",
    likelihood: str = "",
    prior_description: str = "",
    computation_method: str = "",
    prior_mean_scale: float | None = None,
    prior_tau_scale: float | None = None,
    maximum_work: int = DEFAULT_MAXIMUM_WORK,
) -> TableCoefficientAnalysis: ...


@overload
def analyze_ggcoefstats(
    data: object,
    *,
    meta_analytic_effect: Literal[False] = False,
    type: Literal["robust", "bayes"],
    estimate_label: str = "",
    estimand: str = "",
    effect_scale: str = "",
    effect_direction: str = "",
    effect_units: str = "",
    dependence: str = "independent",
    null_value: float = 0.0,
    conf_level: float = 0.95,
    credible_level: float = 0.95,
    alpha: float = 0.05,
    stats_labels: bool = True,
    only_significant: bool = False,
    exclude_intercept: bool = False,
    sort: str = "none",
    maximum_coefficients: int = 500,
    maximum_studies: int = DEFAULT_MAX_STUDIES,
    maximum_rendered_points: int = DEFAULT_MAX_COEFFICIENT_POINTS,
    maximum_labels: int = DEFAULT_MAX_COEFFICIENT_LABELS,
    robust_method: str = "",
    robust_tuning: str = "",
    interval_method: str = "",
    posterior_model: str = "",
    likelihood: str = "",
    prior_description: str = "",
    computation_method: str = "",
    prior_mean_scale: float | None = None,
    prior_tau_scale: float | None = None,
    maximum_work: int = DEFAULT_MAXIMUM_WORK,
) -> ReportedCoefficientAnalysis: ...


@overload
def analyze_ggcoefstats(
    data: object,
    *,
    meta_analytic_effect: bool,
    type: Literal["parametric", "robust", "bayes"] = "parametric",
    estimate_label: str = "",
    estimand: str = "",
    effect_scale: str = "",
    effect_direction: str = "",
    effect_units: str = "",
    dependence: str = "independent",
    null_value: float = 0.0,
    conf_level: float = 0.95,
    credible_level: float = 0.95,
    alpha: float = 0.05,
    stats_labels: bool = True,
    only_significant: bool = False,
    exclude_intercept: bool = False,
    sort: str = "none",
    maximum_coefficients: int = 500,
    maximum_studies: int = DEFAULT_MAX_STUDIES,
    maximum_rendered_points: int = DEFAULT_MAX_COEFFICIENT_POINTS,
    maximum_labels: int = DEFAULT_MAX_COEFFICIENT_LABELS,
    robust_method: str = "",
    robust_tuning: str = "",
    interval_method: str = "",
    posterior_model: str = "",
    likelihood: str = "",
    prior_description: str = "",
    computation_method: str = "",
    prior_mean_scale: float | None = None,
    prior_tau_scale: float | None = None,
    maximum_work: int = DEFAULT_MAXIMUM_WORK,
) -> (
    CoefficientAnalysis
    | TableCoefficientAnalysis
    | ReportedCoefficientAnalysis
    | RobustMetaAnalysis
    | BayesianMetaAnalysis
): ...


def analyze_ggcoefstats(
    data: object,
    *,
    meta_analytic_effect: bool = False,
    type: Literal["parametric", "robust", "bayes"] = "parametric",
    estimate_label: str = "",
    estimand: str = "",
    effect_scale: str = "",
    effect_direction: str = "",
    effect_units: str = "",
    dependence: str = "independent",
    null_value: float = 0.0,
    conf_level: float = 0.95,
    credible_level: float = 0.95,
    alpha: float = 0.05,
    stats_labels: bool = True,
    only_significant: bool = False,
    exclude_intercept: bool = False,
    sort: str = "none",
    maximum_coefficients: int = 500,
    maximum_studies: int = DEFAULT_MAX_STUDIES,
    maximum_rendered_points: int = DEFAULT_MAX_COEFFICIENT_POINTS,
    maximum_labels: int = DEFAULT_MAX_COEFFICIENT_LABELS,
    robust_method: str = "",
    robust_tuning: str = "",
    interval_method: str = "",
    posterior_model: str = "",
    likelihood: str = "",
    prior_description: str = "",
    computation_method: str = "",
    prior_mean_scale: float | None = None,
    prior_tau_scale: float | None = None,
    maximum_work: int = DEFAULT_MAXIMUM_WORK,
) -> (
    CoefficientAnalysis
    | TableCoefficientAnalysis
    | ReportedCoefficientAnalysis
    | RobustMetaAnalysis
    | BayesianMetaAnalysis
):
    """Analyze an approved coefficient or explicit meta-analysis input."""

    if type not in {"parametric", "robust", "bayes"}:
        raise ValueError("type must be 'parametric', 'robust', or 'bayes'")
    if builtin_type(meta_analytic_effect) is not bool:
        raise TypeError("meta_analytic_effect must be boolean")
    if not meta_analytic_effect:
        if (
            estimand
            or dependence != "independent"
            or maximum_studies != DEFAULT_MAX_STUDIES
            or prior_mean_scale is not None
            or prior_tau_scale is not None
            or maximum_work != DEFAULT_MAXIMUM_WORK
        ):
            raise ValueError(
                "meta-analysis-only options cannot be used in coefficient mode"
            )
        if type != "parametric":
            if alpha != 0.05:
                raise ValueError("alpha is unavailable for reported summaries")
            return analyze_reported_coefficients(
                data,
                mode=type,
                estimate_label=estimate_label,
                effect_scale=effect_scale,
                effect_direction=effect_direction,
                effect_units=effect_units,
                null_value=null_value,
                conf_level=conf_level,
                credible_level=credible_level,
                stats_labels=stats_labels,
                only_significant=only_significant,
                exclude_intercept=exclude_intercept,
                sort=sort,
                maximum_coefficients=maximum_coefficients,
                maximum_rendered_points=maximum_rendered_points,
                maximum_labels=maximum_labels,
                robust_method=robust_method,
                robust_tuning=robust_tuning,
                interval_method=interval_method,
                posterior_model=posterior_model,
                likelihood=likelihood,
                prior_description=prior_description,
                computation_method=computation_method,
            )
        if credible_level != 0.95 or any(
            (
                robust_method,
                robust_tuning,
                interval_method,
                posterior_model,
                likelihood,
                prior_description,
                computation_method,
            )
        ):
            raise ValueError(
                "reported-summary options require type='robust' or 'bayes'"
            )
        return analyze_coefficients(
            data,
            estimate_label=estimate_label,
            effect_scale=effect_scale,
            effect_direction=effect_direction,
            effect_units=effect_units,
            null_value=null_value,
            conf_level=conf_level,
            alpha=alpha,
            stats_labels=stats_labels,
            only_significant=only_significant,
            exclude_intercept=exclude_intercept,
            sort=sort,
            maximum_coefficients=maximum_coefficients,
            maximum_rendered_points=maximum_rendered_points,
            maximum_labels=maximum_labels,
        )
    if any(
        (
            robust_method,
            robust_tuning,
            interval_method,
            posterior_model,
            likelihood,
            prior_description,
            computation_method,
        )
    ):
        raise ValueError(
            "reported-summary options cannot be used in meta-analysis mode"
        )
    if (
        estimate_label
        or alpha != 0.05
        or exclude_intercept
        or sort != "none"
        or maximum_coefficients != 500
    ):
        raise ValueError(
            "coefficient-only options cannot be used in meta-analysis mode"
        )
    declarations = (
        _string_option(estimand, "estimand"),
        _string_option(effect_scale, "effect_scale"),
        _string_option(effect_direction, "effect_direction"),
        _string_option(effect_units, "effect_units"),
    )
    if dependence != "independent":
        raise ValueError("meta-analysis supports only dependence='independent'")
    null = _numeric_option(null_value, "null_value")
    if type == "bayes":
        if conf_level != 0.95:
            raise ValueError("conf_level is unavailable in Bayesian meta-analysis")
        confidence = _numeric_option(credible_level, "credible_level")
        if not 0.80 <= confidence <= 0.99:
            raise ValueError("credible_level must lie within [0.80, 0.99]")
    else:
        if type == "robust" and credible_level != 0.95:
            raise ValueError("credible_level is unavailable in robust meta-analysis")
        if type == "parametric" and credible_level != 0.95:
            raise ValueError("credible_level requires type='bayes'")
        confidence = _numeric_option(conf_level, "conf_level")
        if type == "robust" and not 0.80 <= confidence <= 0.99:
            raise ValueError("conf_level must lie within [0.80, 0.99]")
        if type == "parametric" and not 0.0 < confidence < 1.0:
            raise ValueError("conf_level must lie within (0, 1)")
    if (
        builtin_type(stats_labels) is not bool
        or builtin_type(only_significant) is not bool
    ):
        raise TypeError("stats_labels and only_significant must be booleans")
    for value, label in (
        (maximum_rendered_points, "maximum_rendered_points"),
        (maximum_labels, "maximum_labels"),
    ):
        if builtin_type(value) is not int or value < 1:
            raise ValueError(f"{label} must be a positive integer")
    if maximum_rendered_points > HARD_MAX_RENDERED_POINTS:
        raise ValueError(
            f"maximum_rendered_points cannot exceed {HARD_MAX_RENDERED_POINTS}"
        )
    if maximum_labels > HARD_MAX_LABELS:
        raise ValueError(f"maximum_labels cannot exceed {HARD_MAX_LABELS}")

    table = select_study_effects(data, maximum_studies=maximum_studies)
    if type in {"robust", "bayes"}:
        _validate_m6c_study_identities(table.terms)
    if len(table.terms) > maximum_rendered_points:
        raise ValueError(
            f"study count exceeds maximum_rendered_points={maximum_rendered_points}"
        )
    if stats_labels and len(table.terms) > maximum_labels:
        raise ValueError(f"study count exceeds maximum_labels={maximum_labels}")
    if type == "robust":
        if prior_mean_scale is not None or prior_tau_scale is not None:
            raise ValueError("Bayesian prior scales cannot be used in robust mode")
        if only_significant:
            raise ValueError("only_significant=True is unavailable in robust meta mode")
        return analyze_robust_meta(
            table,
            declarations=declarations,
            null_value=null,
            conf_level=confidence,
            stats_labels=stats_labels,
            maximum_studies=maximum_studies,
            maximum_rendered_points=maximum_rendered_points,
            maximum_labels=maximum_labels,
            maximum_work=maximum_work,
        )
    if type == "bayes":
        if prior_mean_scale is None or prior_tau_scale is None:
            raise ValueError(
                "Bayesian meta-analysis requires prior_mean_scale and prior_tau_scale"
            )
        if only_significant:
            raise ValueError(
                "only_significant=True is unavailable in Bayesian meta mode"
            )
        return analyze_bayesian_meta(
            table,
            declarations=declarations,
            null_value=null,
            credible_level=confidence,
            prior_mean_scale=_numeric_option(prior_mean_scale, "prior_mean_scale"),
            prior_tau_scale=_numeric_option(prior_tau_scale, "prior_tau_scale"),
            stats_labels=stats_labels,
            maximum_studies=maximum_studies,
            maximum_rendered_points=maximum_rendered_points,
            maximum_labels=maximum_labels,
            maximum_work=maximum_work,
        )
    if (
        prior_mean_scale is not None
        or prior_tau_scale is not None
        or maximum_work != DEFAULT_MAXIMUM_WORK
    ):
        raise ValueError("M6C prior/work options require type='robust' or 'bayes'")
    alpha = 1.0 - confidence
    z_critical = float(scipy_stats.norm.ppf(1.0 - alpha / 2.0))
    if not np.isfinite(z_critical):
        raise ValueError("normal confidence critical value is not finite")

    estimates = np.asarray(table.estimates)
    standard_errors = np.asarray(table.standard_errors)
    variances = standard_errors * standard_errors
    if not bool(np.isfinite(variances).all()) or bool((variances <= 0.0).any()):
        raise ValueError("study sampling variances are not representable")
    tau_squared, convergence = _reml(estimates, standard_errors, null)
    weights = 1.0 / (variances + tau_squared)
    total_weight = float(np.sum(weights))
    if not np.isfinite(total_weight) or total_weight <= 0.0:
        raise ValueError("random-effects total weight must be finite and positive")
    normalized_weights = weights / total_weight
    contributions = normalized_weights * estimates
    pooled_estimate = float(np.sum(contributions))

    k = len(table.terms)
    df = k - 1
    q_hk = float(np.sum(weights * (estimates - pooled_estimate) ** 2) / df)
    if q_hk < 0.0 and q_hk > -1e-15:
        q_hk = 0.0
    if not np.isfinite(q_hk) or q_hk < 0.0:
        raise ValueError("Hartung-Knapp scale is inadmissible")
    q_star = max(1.0, q_hk)
    conventional_variance = 1.0 / total_weight
    adjusted_variance = q_star / total_weight
    pooled_standard_error = sqrt(adjusted_variance)
    pooled_statistic = (pooled_estimate - null) / pooled_standard_error
    pooled_p = float(scipy_stats.t.sf(abs(pooled_statistic), df) * 2.0)
    t_critical = float(scipy_stats.t.ppf(1.0 - alpha / 2.0, df))
    pooled_interval = IntervalResult(
        "mean_of_true_effect_distribution",
        "modified_hartung_knapp_random_effects_mean",
        confidence,
        pooled_estimate - t_critical * pooled_standard_error,
        pooled_estimate + t_critical * pooled_standard_error,
    )
    pooled = PooledEffectResult(
        "modified_hartung_knapp_random_effects_mean",
        pooled_estimate,
        pooled_standard_error,
        conventional_variance,
        adjusted_variance,
        q_hk,
        q_star,
        "t",
        pooled_statistic,
        df,
        pooled_p,
        pooled_interval,
    )

    prediction_interval: IntervalResult | None = None
    if k >= 5:
        prediction_standard_error = sqrt(tau_squared + adjusted_variance)
        prediction_interval = IntervalResult(
            "true_effect_in_new_study",
            "modified_hartung_knapp_normal_random_effects_prediction_interval",
            confidence,
            pooled_estimate - t_critical * prediction_standard_error,
            pooled_estimate + t_critical * prediction_standard_error,
        )
    prediction = PredictionResult(
        prediction_interval,
        "fewer_than_five_studies" if prediction_interval is None else None,
    )

    fixed_weights = 1.0 / variances
    fixed_mean = float(np.sum(fixed_weights * estimates) / np.sum(fixed_weights))
    q = float(np.sum(fixed_weights * (estimates - fixed_mean) ** 2))
    if q < 0.0 and q > -1e-15:
        q = 0.0
    if not np.isfinite(q) or q < 0.0:
        raise ValueError("Cochran Q is inadmissible")
    q_p = float(scipy_stats.chi2.sf(q, df))
    i_squared = max(0.0, (q - df) / q) if q > 0.0 else 0.0
    heterogeneity = HeterogeneityResult(
        q,
        df,
        q_p,
        fixed_mean,
        i_squared,
        tau_squared,
        sqrt(tau_squared),
        None,
        "not_in_m5b",
    )

    terms: list[CoefficientTermResult] = []
    for index, term in enumerate(table.terms):
        estimate = float(estimates[index])
        standard_error = float(standard_errors[index])
        statistic = (estimate - null) / standard_error
        p_value = float(scipy_stats.norm.sf(abs(statistic)) * 2.0)
        interval = IntervalResult(
            "study_effect",
            "normal_approximation_from_reported_standard_error",
            confidence,
            estimate - z_critical * standard_error,
            estimate + z_critical * standard_error,
        )
        inference = CoefficientInferenceResult(
            "study_normal_approximation_from_reported_standard_error",
            standard_error,
            interval,
            "z",
            statistic,
            None,
            p_value,
            p_value < alpha,
        )
        terms.append(
            CoefficientTermResult(
                term,
                index,
                index,
                estimate,
                inference,
                float(variances[index]),
                float(weights[index]),
                float(normalized_weights[index]),
                float(contributions[index]),
            )
        )

    warnings: list[str] = []
    if k < 5:
        warnings.append("prediction interval unavailable: fewer than five studies")
    if tau_squared == 0.0:
        warnings.append("between-study variance estimate is on the zero boundary")
    if (
        prediction_interval is not None
        and prediction_interval.low <= null <= prediction_interval.high
    ):
        warnings.append("prediction interval crosses the declared null")

    result = CoefficientResult(
        schema_version=1,
        analysis="ggcoefstats_meta_analysis",
        source_kind="table",
        inference_profile="study_effect_standard_error",
        term_column="term",
        estimate_column="estimate",
        standard_error_column="standard_error",
        input_rows=k,
        retained_rows=k,
        source_order=table.terms,
        display_order=table.terms,
        terms=tuple(terms),
        meta_analysis=MetaAnalysisResult(
            declarations[0],
            declarations[1],
            declarations[2],
            declarations[3],
            "independent",
            null,
            "normal_normal_random_effects",
            "reml_intercept_only",
            pooled,
            prediction,
            heterogeneity,
            convergence,
        ),
        conf_level=confidence,
        alpha=alpha,
        stats_labels=stats_labels,
        only_significant=only_significant,
        limits=CoefficientResourceLimits(
            maximum_studies,
            maximum_rendered_points,
            maximum_labels,
        ),
        warnings=tuple(warnings),
    )
    return CoefficientAnalysis(table, result)
