"""Deterministic M6C pass-2 robust and Bayesian aggregate meta-analysis."""

from __future__ import annotations

import warnings
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from importlib import import_module
from importlib.metadata import version
from math import exp, isfinite, lgamma, log, pi, sqrt
from typing import Any, Literal, Protocol, cast

import numpy as np

from plotsalot.bayesian_result import BayesianPosteriorSummary, bounded_bf10_text
from plotsalot.coefficient_data import StudyEffectTable
from plotsalot.coefficient_meta_result import (
    BayesianMetaEvidenceResult,
    BayesianMetaFitResult,
    BayesianMetaPriorResult,
    BayesianMetaQuadratureResult,
    BayesianMetaResult,
    BayesianMetaStudyResult,
    M6CMetaResourceLimits,
    M6CWorkResult,
    MetaStudyIdentityResult,
    RobustMetaAnalysisResult,
    RobustMetaConvergenceResult,
    RobustMetaPooledResult,
    RobustMetaResult,
    RobustMetaStartResult,
    RobustMetaStudyResult,
)
from plotsalot.result import IntervalResult

DEFAULT_MAXIMUM_WORK = 100_000_000
HARD_MAXIMUM_WORK = 500_000_000
ROBUST_RESERVED_WORK = 20_000_000
BAYESIAN_RESERVED_WORK = 25_000_000
_NU = 4.0
_MAX_CYCLES = 10_000
_LOG_TOLERANCE = 1e-10
_PARAMETER_TOLERANCE = 1e-8
_SCORE_TOLERANCE = 1e-8
_AMBIGUITY_LIKELIHOOD_TOLERANCE = 1e-8
_AMBIGUITY_PARAMETER_TOLERANCE = 1e-7
_ROOT_ITERATIONS = 100
_ROOT_XTOL = 1e-10
_EPSABS = 1e-12
_EPSREL = 1e-10
_QUAD_LIMIT = 200


class _RootDetails(Protocol):
    converged: bool
    iterations: int


class _OptimizeResult(Protocol):
    success: bool
    fun: float


_integrate_module = cast(Any, import_module("scipy.integrate"))
_optimize_module = cast(Any, import_module("scipy.optimize"))
_special_module = cast(Any, import_module("scipy.special"))
_stats_module = cast(Any, import_module("scipy.stats"))
IntegrationWarning = cast(type[Warning], _integrate_module.IntegrationWarning)
_quad = cast(Callable[..., tuple[float, float]], _integrate_module.quad)
_minimize_scalar = cast(
    Callable[..., _OptimizeResult], _optimize_module.minimize_scalar
)
_ndtr = cast(Callable[[float], float], _special_module.ndtr)


def _brent_root(function: Callable[[float], float], low: float, high: float) -> float:
    root = _optimize_module.brentq(
        function,
        low,
        high,
        xtol=_ROOT_XTOL,
        rtol=4.0 * np.finfo(np.float64).eps,
        maxiter=_ROOT_ITERATIONS,
    )
    return float(root)


def _brent_root_details(
    function: Callable[[float], float], low: float, high: float
) -> tuple[float, _RootDetails]:
    root, details = _optimize_module.brentq(
        function,
        low,
        high,
        xtol=_ROOT_XTOL,
        rtol=4.0 * np.finfo(np.float64).eps,
        maxiter=_ROOT_ITERATIONS,
        full_output=True,
        disp=False,
    )
    return float(root), cast(_RootDetails, details)


def _normal_ppf(probability: float) -> float:
    return float(_stats_module.norm.ppf(probability))


def _chi_squared_ppf(probability: float) -> float:
    return float(_stats_module.chi2.ppf(probability, 1))


def _chi_squared_sf(value: float) -> float:
    return float(_stats_module.chi2.sf(value, 1))


def _root_difference(
    value: float, *, cdf: Callable[[float], float], probability: float
) -> float:
    return cdf(value) - probability


class M6CMetaError(ValueError):
    """Stable coded failure for an M6C numerical or resource boundary."""

    code: str

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(slots=True)
class _WorkMeter:
    maximum: int
    actual: int = 0

    def bump(self) -> None:
        self.actual += 1
        if self.actual > self.maximum:
            raise M6CMetaError(
                "m6c_meta_work_exhausted",
                f"actual work exceeded maximum_work={self.maximum}",
            )


@dataclass(frozen=True, slots=True)
class _RobustCandidate:
    label: Literal["m5_reml", "median_mad", "fixed_effect"]
    mu: float
    tau_squared: float
    log_likelihood: float
    score_norm: float
    cycles: int
    successive: int
    converged: bool


@dataclass(frozen=True, slots=True)
class RobustMetaAnalysis:
    table: StudyEffectTable
    result: RobustMetaResult

    def __post_init__(self) -> None:
        if self.table.terms != self.result.source_order:
            raise ValueError("robust meta table and result identities must match")
        if tuple(float(value) for value in self.table.estimates) != tuple(
            item.estimate for item in self.result.studies
        ) or tuple(float(value) for value in self.table.standard_errors) != tuple(
            item.standard_error for item in self.result.studies
        ):
            raise ValueError("robust meta table and result values must match")


@dataclass(frozen=True, slots=True)
class BayesianMetaAnalysis:
    table: StudyEffectTable
    result: BayesianMetaResult

    def __post_init__(self) -> None:
        if self.table.terms != self.result.source_order:
            raise ValueError("Bayesian meta table and result identities must match")
        if tuple(float(value) for value in self.table.estimates) != tuple(
            item.estimate for item in self.result.studies
        ) or tuple(float(value) for value in self.table.standard_errors) != tuple(
            item.standard_error for item in self.result.studies
        ):
            raise ValueError("Bayesian meta table and result values must match")


def _preflight(maximum_work: int, reserved: int) -> None:
    if (
        type(maximum_work) is not int
        or maximum_work < 1
        or maximum_work > HARD_MAXIMUM_WORK
    ):
        raise M6CMetaError(
            "m6c_meta_invalid_maximum_work",
            f"maximum_work must be an integer from 1 through {HARD_MAXIMUM_WORK}",
        )
    if reserved > maximum_work:
        raise M6CMetaError(
            "m6c_meta_work_preflight_failed",
            f"reserved_work={reserved} exceeds maximum_work={maximum_work}",
        )


def _robust_scale(
    y: np.ndarray[Any, np.dtype[np.float64]],
    se: np.ndarray[Any, np.dtype[np.float64]],
    null: float,
) -> float:
    median = float(np.median(y))
    mad = float(np.median(np.abs(y - median)))
    return max(
        float(np.median(se)),
        1.4826 * mad,
        float(np.max(np.abs(y - null))) * sqrt(np.finfo(np.float64).eps),
        sqrt(np.finfo(np.float64).tiny),
    )


def _t_evaluate(
    y: np.ndarray[Any, np.dtype[np.float64]],
    variances: np.ndarray[Any, np.dtype[np.float64]],
    mu: float,
    tau_squared: float,
    meter: _WorkMeter,
) -> tuple[float, np.ndarray[Any, np.dtype[np.float64]], float, float]:
    meter.bump()
    d = variances + tau_squared
    residual = y - mu
    squared = residual * residual
    if tau_squared < 0.0 or not bool(np.isfinite(d).all()) or bool((d <= 0.0).any()):
        return -float("inf"), np.zeros_like(y), float("nan"), float("nan")
    lambdas = (_NU + 1.0) / (_NU + squared / d)
    constant = lgamma((_NU + 1.0) / 2.0) - lgamma(_NU / 2.0) - 0.5 * log(_NU * pi)
    likelihood = float(
        np.sum(
            constant
            - 0.5 * np.log(d)
            - ((_NU + 1.0) / 2.0) * np.log1p(squared / (_NU * d))
        )
    )
    mu_score = float(np.sum(lambdas * residual / d))
    tau_score = float(0.5 * np.sum((lambdas * squared - d) / (d * d)))
    return likelihood, lambdas, mu_score, tau_score


def _score_norm(
    variances: np.ndarray[Any, np.dtype[np.float64]],
    tau_squared: float,
    lambdas: np.ndarray[Any, np.dtype[np.float64]],
    mu_score: float,
    tau_score: float,
) -> float:
    del variances, lambdas
    tau_component = abs(tau_score) if tau_squared > 0.0 else max(0.0, tau_score)
    return max(abs(mu_score), tau_component)


def _run_robust_start(
    y: np.ndarray[Any, np.dtype[np.float64]],
    variances: np.ndarray[Any, np.dtype[np.float64]],
    label: Literal["m5_reml", "median_mad", "fixed_effect"],
    initial_mu: float,
    initial_tau_squared: float,
    meter: _WorkMeter,
    *,
    fixed_mu: float | None,
) -> _RobustCandidate:
    mu = fixed_mu if fixed_mu is not None else initial_mu
    tau_squared = max(0.0, initial_tau_squared)
    likelihood, lambdas, mu_score, tau_score = _t_evaluate(
        y, variances, mu, tau_squared, meter
    )
    successive = 0
    cycles = 0
    if not isfinite(likelihood):
        return _RobustCandidate(
            label, mu, tau_squared, likelihood, float("inf"), 0, 0, False
        )
    for cycle in range(1, _MAX_CYCLES + 1):
        d = variances + tau_squared
        next_mu = (
            fixed_mu
            if fixed_mu is not None
            else float(np.sum(lambdas * y / d) / np.sum(lambdas / d))
        )
        numerator = float(np.sum((lambdas * (y - next_mu) ** 2 - variances) / (d * d)))
        denominator = float(np.sum(1.0 / (d * d)))
        next_tau_squared = max(0.0, numerator / denominator)
        next_likelihood, next_lambdas, next_mu_score, next_tau_score = _t_evaluate(
            y, variances, next_mu, next_tau_squared, meter
        )
        decrease_tolerance = 64.0 * np.finfo(np.float64).eps * (1.0 + abs(likelihood))
        if (
            not isfinite(next_likelihood)
            or next_likelihood < likelihood - decrease_tolerance
        ):
            break
        relative_change = abs(next_likelihood - likelihood) / (1.0 + abs(likelihood))
        parameter_change = max(abs(next_mu - mu), abs(next_tau_squared - tau_squared))
        successive = (
            min(3, successive + 1)
            if relative_change <= _LOG_TOLERANCE
            and parameter_change <= _PARAMETER_TOLERANCE
            else 0
        )
        mu = next_mu
        tau_squared = next_tau_squared
        likelihood = next_likelihood
        lambdas = next_lambdas
        mu_score = next_mu_score
        tau_score = next_tau_score
        cycles = cycle
        score = _score_norm(
            variances,
            tau_squared,
            lambdas,
            0.0 if fixed_mu is not None else mu_score,
            tau_score,
        )
        if successive == 3 and score <= _SCORE_TOLERANCE:
            break
    score = _score_norm(
        variances,
        tau_squared,
        lambdas,
        0.0 if fixed_mu is not None else mu_score,
        tau_score,
    )
    converged = successive == 3 and score <= _SCORE_TOLERANCE
    return _RobustCandidate(
        label,
        mu,
        tau_squared,
        likelihood,
        score,
        cycles,
        successive,
        converged,
    )


def _select_robust_candidate(
    candidates: tuple[_RobustCandidate, ...], *, context: str
) -> _RobustCandidate:
    converged = tuple(item for item in candidates if item.converged)
    if not converged:
        raise M6CMetaError(
            "robust_meta_no_converged_start", f"no start converged for {context}"
        )
    best = max(converged, key=lambda item: item.log_likelihood)
    likelihood_tolerance = _AMBIGUITY_LIKELIHOOD_TOLERANCE * (
        1.0 + abs(best.log_likelihood)
    )
    for item in converged:
        if (
            abs(item.log_likelihood - best.log_likelihood) <= likelihood_tolerance
            and max(
                abs(item.mu - best.mu),
                abs(item.tau_squared - best.tau_squared),
            )
            > _AMBIGUITY_PARAMETER_TOLERANCE
        ):
            raise M6CMetaError(
                "robust_meta_ambiguous_optimum",
                f"agreeing likelihoods have different parameters for {context}",
            )
    return best


def _fit_robust(
    y: np.ndarray[Any, np.dtype[np.float64]],
    variances: np.ndarray[Any, np.dtype[np.float64]],
    starts: tuple[
        tuple[Literal["m5_reml", "median_mad", "fixed_effect"], float, float], ...
    ],
    meter: _WorkMeter,
    *,
    fixed_mu: float | None = None,
    context: str,
) -> tuple[_RobustCandidate, tuple[_RobustCandidate, ...]]:
    candidates = tuple(
        _run_robust_start(
            y,
            variances,
            label,
            mu,
            tau_squared,
            meter,
            fixed_mu=fixed_mu,
        )
        for label, mu, tau_squared in starts
    )
    return _select_robust_candidate(candidates, context=context), candidates


def _robust_starts(
    table: StudyEffectTable,
    scaled_y: np.ndarray[Any, np.dtype[np.float64]],
    scaled_variances: np.ndarray[Any, np.dtype[np.float64]],
    center: float,
    scale: float,
) -> tuple[tuple[Literal["m5_reml", "median_mad", "fixed_effect"], float, float], ...]:
    original_y = np.asarray(table.estimates)
    original_se = np.asarray(table.standard_errors)
    reml_scale = max(
        float(np.max(np.abs(original_y - center))), float(np.max(original_se))
    )
    reml_y = (original_y - center) / reml_scale
    reml_variances = (original_se / reml_scale) ** 2

    def reml_score(tau_squared: float) -> float:
        weights = 1.0 / (reml_variances + tau_squared)
        weighted_mean = float(np.sum(weights * reml_y) / np.sum(weights))
        residuals = reml_y - weighted_mean
        return float(
            0.5
            * (
                np.sum(weights * weights * residuals * residuals)
                - np.sum(weights)
                + np.sum(weights * weights) / np.sum(weights)
            )
        )

    if reml_score(0.0) <= 0.0:
        reml_tau_squared = 0.0
    else:
        upper = max(
            1.0,
            float(np.var(reml_y, ddof=1)),
            float(np.max(reml_variances)),
        )
        expansions = 0
        while reml_score(upper) >= 0.0 and expansions < 60:
            upper *= 2.0
            expansions += 1
        if not isfinite(reml_score(upper)) or reml_score(upper) >= 0.0:
            raise M6CMetaError(
                "robust_meta_reml_start_failed", "M5 REML start could not be bracketed"
            )
        reml_root = _optimize_module.brentq(
            reml_score,
            0.0,
            upper,
            xtol=np.finfo(np.float64).tiny,
            rtol=4.0 * np.finfo(np.float64).eps,
            maxiter=100,
        )
        reml_tau_squared = float(reml_root) * reml_scale * reml_scale
    reml_weights = 1.0 / (original_se * original_se + reml_tau_squared)
    reml_mu = float(np.sum(reml_weights * original_y) / np.sum(reml_weights))
    median = float(np.median(scaled_y))
    mad = 1.4826 * float(np.median(np.abs(scaled_y - median)))
    median_q = max(0.0, mad * mad - float(np.median(scaled_variances)))
    fixed_weights = 1.0 / scaled_variances
    fixed_mu = float(np.sum(fixed_weights * scaled_y) / np.sum(fixed_weights))
    return (
        ("m5_reml", (reml_mu - center) / scale, reml_tau_squared / (scale * scale)),
        ("median_mad", median, median_q),
        ("fixed_effect", fixed_mu, 0.0),
    )


def analyze_robust_meta(
    table: StudyEffectTable,
    *,
    declarations: tuple[str, str, str, str],
    null_value: float,
    conf_level: float,
    stats_labels: bool,
    maximum_studies: int,
    maximum_rendered_points: int,
    maximum_labels: int,
    maximum_work: int,
) -> RobustMetaAnalysis:
    """Fit the approved fixed-Student-t4 marginal ML sensitivity model."""

    if len(table.terms) < 10:
        raise M6CMetaError(
            "robust_meta_requires_at_least_10_studies",
            f"received {len(table.terms)} studies",
        )
    _preflight(maximum_work, ROBUST_RESERVED_WORK)
    meter = _WorkMeter(maximum_work)
    original_y = np.asarray(table.estimates)
    original_se = np.asarray(table.standard_errors)
    scale = _robust_scale(original_y, original_se, null_value)
    y = (original_y - null_value) / scale
    se = original_se / scale
    variances = se * se
    starts = _robust_starts(table, y, variances, null_value, scale)
    best, candidates = _fit_robust(
        y, variances, starts, meter, context="unconstrained fit"
    )
    critical = _chi_squared_ppf(conf_level)
    profile_evaluations = 0

    def profile(mu: float, context: str) -> float:
        nonlocal profile_evaluations
        profile_evaluations += 1
        fitted, _ = _fit_robust(
            y, variances, starts, meter, fixed_mu=mu, context=context
        )
        return fitted.log_likelihood

    def root_value(mu: float, context: str) -> float:
        return 2.0 * (best.log_likelihood - profile(mu, context)) - critical

    step = max(
        float(np.median(se)), sqrt(best.tau_squared + float(np.median(variances)))
    )
    root_iterations = 0
    endpoints: list[float] = []
    for direction, name in ((-1.0, "lower"), (1.0, "upper")):
        inner = best.mu
        outer = best.mu + direction * step
        value = root_value(outer, f"{name} endpoint bracket")
        expansions = 0
        while value <= 0.0 and expansions < 60:
            outer = best.mu + direction * step * (2.0 ** (expansions + 1))
            value = root_value(outer, f"{name} endpoint bracket")
            expansions += 1
        if not isfinite(value) or value <= 0.0:
            raise M6CMetaError(
                "robust_meta_profile_endpoint_missing",
                f"no finite {name} profile-likelihood endpoint",
            )
        low, high = sorted((inner, outer))
        root, details = _brent_root_details(
            partial(root_value, context=f"{name} endpoint root"),
            low,
            high,
        )
        if not details.converged:
            raise M6CMetaError(
                "robust_meta_profile_root_failed", f"{name} endpoint did not converge"
            )
        root_iterations += int(details.iterations)
        endpoints.append(float(root))
    null_profile = profile(0.0, "null hypothesis")
    statistic = max(0.0, 2.0 * (best.log_likelihood - null_profile))
    p_value = _chi_squared_sf(statistic)
    estimate = null_value + scale * best.mu
    tau_squared = scale * scale * best.tau_squared
    tau = sqrt(tau_squared)
    interval = IntervalResult(
        "population_student_t4_location",
        "student_t4_profile_likelihood",
        conf_level,
        null_value + scale * endpoints[0],
        null_value + scale * endpoints[1],
    )
    _, lambdas, _, _ = _t_evaluate(y, variances, best.mu, best.tau_squared, meter)
    d = variances + best.tau_squared
    effective = lambdas / d
    shares = effective / float(np.sum(effective))
    z = _normal_ppf(0.5 + conf_level / 2.0)
    studies = tuple(
        RobustMetaStudyResult(
            MetaStudyIdentityResult(term, index, index),
            float(original_y[index]),
            float(original_se[index]),
            IntervalResult(
                "study_effect",
                "normal_approximation_from_reported_standard_error",
                conf_level,
                float(original_y[index] - z * original_se[index]),
                float(original_y[index] + z * original_se[index]),
            ),
            float((y[index] - best.mu) / sqrt(d[index])),
            float(lambdas[index]),
            float(effective[index] / (scale * scale)),
            float(shares[index]),
            float(shares[index] * original_y[index]),
        )
        for index, term in enumerate(table.terms)
    )
    start_results = tuple(
        RobustMetaStartResult(
            item.label,
            item.converged,
            item.cycles,
            item.successive,
            item.mu,
            item.tau_squared,
            item.log_likelihood,
            item.score_norm,
            item.tau_squared == 0.0,
        )
        for item in candidates
    )
    convergence = RobustMetaConvergenceResult(
        "three_start_ecme_fixed_point",
        4,
        10_000,
        _LOG_TOLERANCE,
        _PARAMETER_TOLERANCE,
        _SCORE_TOLERANCE,
        _AMBIGUITY_LIKELIHOOD_TOLERANCE,
        _AMBIGUITY_PARAMETER_TOLERANCE,
        best.label,
        start_results,
        null_value,
        scale,
        root_iterations,
        profile_evaluations,
        True,
    )
    pooled = RobustMetaPooledResult(
        "student_t4_marginal_ml_profile_likelihood",
        estimate,
        tau_squared,
        tau,
        "profile_likelihood_ratio_chi_squared_1",
        statistic,
        p_value,
        interval,
        "not_defined_for_student_t4_working_model",
        "robust_meta_prediction_method_not_approved",
    )
    limits = M6CMetaResourceLimits(
        maximum_studies,
        maximum_rendered_points,
        maximum_labels,
        maximum_work,
    )
    result = RobustMetaResult(
        2,
        "ggcoefstats_meta_analysis",
        "robust",
        "student_t4_marginal_ml_profile_likelihood",
        "adapted",
        "table",
        "study_effect_standard_error",
        len(table.terms),
        len(table.terms),
        table.terms,
        table.terms,
        studies,
        RobustMetaAnalysisResult(
            declarations[0],
            declarations[1],
            declarations[2],
            declarations[3],
            "independent",
            null_value,
            "student_t4_random_effects",
            pooled,
            convergence,
        ),
        conf_level,
        stats_labels,
        False,
        convergence,
        M6CWorkResult(
            ROBUST_RESERVED_WORK,
            meter.actual,
            maximum_work,
            "integrand_or_likelihood_evaluation",
        ),
        limits,
        ("few_studies_robust_profile_likelihood",) if len(table.terms) < 20 else (),
    )
    return RobustMetaAnalysis(table, result)


@dataclass(slots=True)
class _BayesianFitEngine:
    y: np.ndarray[Any, np.dtype[np.float64]]
    variances: np.ndarray[Any, np.dtype[np.float64]]
    null: float
    mean_scale: float
    tau_scale: float
    level: float
    meter: _WorkMeter
    evaluations_at_start: int
    root_brackets: list[tuple[str, float, float]]

    def conditional(self, tau: float) -> tuple[float, float]:
        d = self.variances + tau * tau
        precision = 1.0 / (self.mean_scale * self.mean_scale) + float(np.sum(1.0 / d))
        variance = 1.0 / precision
        mean = variance * (
            self.null / (self.mean_scale * self.mean_scale) + float(np.sum(self.y / d))
        )
        return mean, variance

    def log_kernel(self, x: float, hypothesis: Literal["h1", "h0"]) -> float:
        self.meter.bump()
        if x < 0.0 or x >= 1.0:
            return -float("inf")
        tau = self.tau_scale * x / (1.0 - x)
        d = self.variances + tau * tau
        if not bool(np.isfinite(d).all()) or bool((d <= 0.0).any()):
            return -float("inf")
        centered = self.y - self.null
        base = -0.5 * (self.y.size * log(2.0 * pi) + float(np.sum(np.log(d))))
        if hypothesis == "h0":
            log_likelihood = base - 0.5 * float(np.sum(centered * centered / d))
        else:
            precision = 1.0 / (self.mean_scale * self.mean_scale) + float(
                np.sum(1.0 / d)
            )
            b = float(np.sum(centered / d))
            c = float(np.sum(centered * centered / d))
            log_likelihood = (
                base
                - log(self.mean_scale)
                - 0.5 * log(precision)
                - 0.5 * (c - b * b / precision)
            )
        log_prior = (
            0.5 * log(2.0 / pi)
            - log(self.tau_scale)
            - 0.5 * (tau / self.tau_scale) ** 2
        )
        log_jacobian = log(self.tau_scale) - 2.0 * log(1.0 - x)
        result = log_likelihood + log_prior + log_jacobian
        return result if isfinite(result) else -float("inf")

    def peak(self, hypothesis: Literal["h1", "h0"]) -> float:
        def objective(x: float) -> float:
            return -self.log_kernel(float(x), hypothesis)

        result = _minimize_scalar(
            objective,
            bounds=(0.0, 1.0 - 1e-12),
            method="bounded",
            options={"xatol": 1e-12, "maxiter": 500},
        )
        if not result.success or not isfinite(float(result.fun)):
            raise M6CMetaError(
                "bayesian_meta_quadrature_peak_failed",
                f"could not scale the {hypothesis} integrand",
            )
        endpoint = self.log_kernel(0.0, hypothesis)
        return max(-float(result.fun), endpoint)

    def integrate(
        self,
        function: Any,
        low: float,
        high: float,
    ) -> tuple[float, float]:
        with warnings.catch_warnings():
            warnings.simplefilter("error", IntegrationWarning)
            try:
                value, error = _quad(
                    function,
                    low,
                    high,
                    epsabs=_EPSABS,
                    epsrel=_EPSREL,
                    limit=_QUAD_LIMIT,
                )
            except (IntegrationWarning, ValueError, OverflowError) as exc:
                raise M6CMetaError("bayesian_meta_quadrature_failed", str(exc)) from exc
        numeric, estimated = float(value), float(error)
        if (
            not isfinite(numeric)
            or not isfinite(estimated)
            or numeric < 0.0
            or estimated > max(_EPSABS, _EPSREL * abs(numeric))
        ):
            raise M6CMetaError(
                "bayesian_meta_quadrature_tolerance_failed",
                f"integral={numeric!r}, estimated_error={estimated!r}",
            )
        return numeric, estimated


def _bayesian_prior(
    null: float, mean_scale: float, tau_scale: float
) -> BayesianMetaPriorResult:
    z95 = _normal_ppf(0.975)
    return BayesianMetaPriorResult(
        "normal",
        null,
        mean_scale,
        IntervalResult(
            "prior_population_mean",
            "normal_prior",
            0.95,
            null - z95 * mean_scale,
            null + z95 * mean_scale,
        ),
        "half_normal",
        tau_scale,
        _normal_ppf(0.75) * tau_scale,
        z95 * tau_scale,
        sqrt(mean_scale * mean_scale + tau_scale * tau_scale),
        True,
    )


def _fit_bayesian(
    table: StudyEffectTable,
    *,
    label: Literal[
        "primary",
        "mean_scale_half",
        "mean_scale_double",
        "tau_scale_half",
        "tau_scale_double",
    ],
    null: float,
    mean_scale: float,
    tau_scale: float,
    level: float,
    meter: _WorkMeter,
) -> BayesianMetaFitResult:
    engine = _BayesianFitEngine(
        np.asarray(table.estimates),
        np.asarray(table.standard_errors) ** 2,
        null,
        mean_scale,
        tau_scale,
        level,
        meter,
        meter.actual,
        [],
    )
    h1_peak = engine.peak("h1")
    h0_peak = engine.peak("h0")

    def h1_integrand(x: float) -> float:
        return exp(engine.log_kernel(float(x), "h1") - h1_peak)

    def h0_integrand(x: float) -> float:
        return exp(engine.log_kernel(float(x), "h0") - h0_peak)

    h1_integral, h1_error = engine.integrate(h1_integrand, 0.0, 1.0)
    h0_integral, h0_error = engine.integrate(h0_integrand, 0.0, 1.0)
    if h1_integral <= 0.0 or h0_integral <= 0.0:
        raise M6CMetaError(
            "bayesian_meta_lost_tail_mass", "marginal likelihood integral is zero"
        )
    log_h1 = h1_peak + log(h1_integral)
    log_h0 = h0_peak + log(h0_integral)

    def posterior_weight(x: float) -> float:
        return exp(engine.log_kernel(float(x), "h1") - h1_peak) / h1_integral

    normalization, normalization_error = engine.integrate(posterior_weight, 0.0, 1.0)
    normalization_deviation = abs(normalization - 1.0)
    if normalization_deviation > max(_EPSABS, normalization_error):
        raise M6CMetaError(
            "bayesian_meta_normalization_failed",
            f"posterior mass={normalization!r}",
        )

    def tau_cdf_x(x: float) -> float:
        value, _ = engine.integrate(posterior_weight, 0.0, x)
        return min(1.0, max(0.0, value))

    checks = tuple(tau_cdf_x(x) for x in (0.25, 0.5, 0.75))
    if any(
        right + 1e-10 < left for left, right in zip(checks, checks[1:], strict=False)
    ):
        raise M6CMetaError(
            "bayesian_meta_nonmonotone_cdf", "tau posterior CDF is non-monotone"
        )

    def mixture_cdf(value: float, target: Literal["mu", "theta"]) -> float:
        def integrand(x: float) -> float:
            if x >= 1.0:
                return 0.0
            tau = tau_scale * x / (1.0 - x)
            mean, variance = engine.conditional(tau)
            target_variance = variance if target == "mu" else variance + tau * tau
            return posterior_weight(x) * float(
                _ndtr((value - mean) / sqrt(target_variance))
            )

        result, _ = engine.integrate(integrand, 0.0, 1.0)
        return min(1.0, max(0.0, result))

    alpha = 1.0 - level
    probabilities = (alpha / 2.0, 0.5, 1.0 - alpha / 2.0)

    def mixture_quantiles(target: Literal["mu", "theta"]) -> tuple[float, float, float]:
        spread = max(
            mean_scale,
            tau_scale,
            float(np.max(np.abs(engine.y - null))),
            float(np.max(np.sqrt(engine.variances))),
        )
        low = min(float(np.min(engine.y)), null) - 8.0 * spread
        high = max(float(np.max(engine.y)), null) + 8.0 * spread
        while mixture_cdf(low, target) > probabilities[0]:
            low -= 2.0 * spread
        while mixture_cdf(high, target) < probabilities[2]:
            high += 2.0 * spread
        roots: list[float] = []
        for suffix, probability in zip(
            ("low", "median", "high"), probabilities, strict=True
        ):
            engine.root_brackets.append((f"{target}_{suffix}", low, high))
            cdf = partial(mixture_cdf, target=target)
            root = _brent_root(
                partial(_root_difference, cdf=cdf, probability=probability),
                low,
                high,
            )
            roots.append(float(root))
        return roots[0], roots[1], roots[2]

    mu_low, mu_median, mu_high = mixture_quantiles("mu")
    theta_low, theta_median, theta_high = mixture_quantiles("theta")
    x_high = 1.0 - 1e-12
    tau_roots: list[float] = []
    for suffix, probability in zip(
        ("low", "median", "high"), probabilities, strict=True
    ):
        engine.root_brackets.append(
            (f"tau_{suffix}", 0.0, tau_scale * x_high / (1.0 - x_high))
        )
        x_root = _brent_root(
            partial(_root_difference, cdf=tau_cdf_x, probability=probability),
            0.0,
            x_high,
        )
        tau_roots.append(tau_scale * float(x_root) / (1.0 - float(x_root)))
    tau_low, tau_median, tau_high = tau_roots
    mu_below = mixture_cdf(null, "mu")
    theta_below = mixture_cdf(null, "theta")

    def summary(
        target: str,
        median: float,
        low: float,
        high: float,
        null_value: float,
        below: float,
        interval_method: str = "bayesian_equal_tail",
    ) -> BayesianPosteriorSummary:
        below = min(1.0, max(0.0, below))
        return BayesianPosteriorSummary(
            target,
            median,
            null_value,
            IntervalResult(target, interval_method, level, low, high),
            1.0 - below,
            below,
            0.0,
        )

    tau_summary = summary("between_study_tau", tau_median, tau_low, tau_high, 0.0, 0.0)
    evaluations = meter.actual - engine.evaluations_at_start
    quadrature = BayesianMetaQuadratureResult(
        "adaptive_gauss_kronrod",
        "tau=prior_tau_scale*x/(1-x)",
        _EPSABS,
        _EPSREL,
        _QUAD_LIMIT,
        evaluations,
        log_h1,
        log_h0,
        h1_error / h1_integral,
        h0_error / h0_integral,
        normalization_deviation,
        True,
        tuple(engine.root_brackets),
        np.__version__,
        version("scipy"),
        True,
    )
    log_bf10 = log_h1 - log_h0
    return BayesianMetaFitResult(
        label,
        _bayesian_prior(null, mean_scale, tau_scale),
        summary("population_mean", mu_median, mu_low, mu_high, null, mu_below),
        tau_summary,
        summary(
            "between_study_tau_squared",
            tau_median * tau_median,
            tau_low * tau_low,
            tau_high * tau_high,
            0.0,
            0.0,
        ),
        summary(
            "true_effect_in_new_exchangeable_study",
            theta_median,
            theta_low,
            theta_high,
            null,
            theta_below,
        ),
        BayesianMetaEvidenceResult(
            "mu_equals_null_value",
            "mu_normal_prior_centered_at_null_value",
            log_bf10,
            bounded_bf10_text(log_bf10),
            1.0,
        ),
        quadrature,
    )


def analyze_bayesian_meta(
    table: StudyEffectTable,
    *,
    declarations: tuple[str, str, str, str],
    null_value: float,
    credible_level: float,
    prior_mean_scale: float,
    prior_tau_scale: float,
    stats_labels: bool,
    maximum_studies: int,
    maximum_rendered_points: int,
    maximum_labels: int,
    maximum_work: int,
) -> BayesianMetaAnalysis:
    """Fit the approved proper-prior normal-normal hierarchy by quadrature."""

    _preflight(maximum_work, BAYESIAN_RESERVED_WORK)
    for value, label in (
        (prior_mean_scale, "prior_mean_scale"),
        (prior_tau_scale, "prior_tau_scale"),
    ):
        if not isfinite(value) or value <= 0.0:
            raise M6CMetaError(
                "bayesian_meta_invalid_prior_scale",
                f"{label} must be finite and positive",
            )
    meter = _WorkMeter(maximum_work)
    fit_specs: tuple[
        tuple[
            Literal[
                "primary",
                "mean_scale_half",
                "mean_scale_double",
                "tau_scale_half",
                "tau_scale_double",
            ],
            float,
            float,
        ],
        ...,
    ] = (
        ("primary", prior_mean_scale, prior_tau_scale),
        ("mean_scale_half", 0.5 * prior_mean_scale, prior_tau_scale),
        ("mean_scale_double", 2.0 * prior_mean_scale, prior_tau_scale),
        ("tau_scale_half", prior_mean_scale, 0.5 * prior_tau_scale),
        ("tau_scale_double", prior_mean_scale, 2.0 * prior_tau_scale),
    )
    fits = tuple(
        _fit_bayesian(
            table,
            label=label,
            null=null_value,
            mean_scale=mean_scale,
            tau_scale=tau_scale,
            level=credible_level,
            meter=meter,
        )
        for label, mean_scale, tau_scale in fit_specs
    )
    z = _normal_ppf(0.5 + credible_level / 2.0)
    studies = tuple(
        BayesianMetaStudyResult(
            MetaStudyIdentityResult(term, index, index),
            float(table.estimates[index]),
            float(table.standard_errors[index]),
            IntervalResult(
                "study_effect",
                "normal_approximation_from_reported_standard_error",
                credible_level,
                float(table.estimates[index] - z * table.standard_errors[index]),
                float(table.estimates[index] + z * table.standard_errors[index]),
            ),
        )
        for index, term in enumerate(table.terms)
    )
    limits = M6CMetaResourceLimits(
        maximum_studies,
        maximum_rendered_points,
        maximum_labels,
        maximum_work,
    )
    result = BayesianMetaResult(
        3,
        "ggcoefstats_meta_analysis",
        "bayes",
        "proper_prior_normal_normal_quadrature",
        "adapted",
        "table",
        "study_effect_standard_error",
        declarations[0],
        declarations[1],
        declarations[2],
        declarations[3],
        "independent",
        null_value,
        len(table.terms),
        len(table.terms),
        table.terms,
        table.terms,
        studies,
        credible_level,
        fits[0],
        fits[1:],
        stats_labels,
        False,
        M6CWorkResult(
            BAYESIAN_RESERVED_WORK,
            meter.actual,
            maximum_work,
            "integrand_or_likelihood_evaluation",
        ),
        limits,
        ("few_studies_prior_sensitive",) if len(table.terms) < 5 else (),
    )
    return BayesianMetaAnalysis(table, result)
