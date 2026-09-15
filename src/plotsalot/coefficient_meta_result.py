"""Immutable M6C pass-2 robust and Bayesian meta-analysis results."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isclose, isfinite
from typing import Any, Literal

from plotsalot.bayesian_result import (
    BayesianPosteriorSummary,
    bounded_bf10_text,
)
from plotsalot.result import IntervalResult


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _finite(value: float, label: str) -> None:
    if not isfinite(value):
        raise ValueError(f"{label} must be finite")


@dataclass(frozen=True, slots=True)
class M6CMetaResourceLimits:
    maximum_studies: int
    maximum_rendered_points: int
    maximum_labels: int
    maximum_work: int
    hard_maximum_work: int = 500_000_000
    maximum_serialized_fields: int = 20_000

    def __post_init__(self) -> None:
        if (
            any(
                type(value) is not int or value < 1
                for value in (
                    self.maximum_studies,
                    self.maximum_rendered_points,
                    self.maximum_labels,
                    self.maximum_work,
                    self.hard_maximum_work,
                    self.maximum_serialized_fields,
                )
            )
            or self.maximum_work > self.hard_maximum_work
        ):
            raise ValueError("M6C meta-analysis resource limits are invalid")


@dataclass(frozen=True, slots=True)
class M6CWorkResult:
    reserved_work: int
    actual_work: int
    maximum_work: int
    work_unit: Literal["integrand_or_likelihood_evaluation"]

    def __post_init__(self) -> None:
        if (
            type(self.reserved_work) is not int
            or type(self.actual_work) is not int
            or type(self.maximum_work) is not int
            or not 0 <= self.actual_work <= self.reserved_work <= self.maximum_work
            or self.work_unit != "integrand_or_likelihood_evaluation"
        ):
            raise ValueError("M6C work accounting does not reconcile")


@dataclass(frozen=True, slots=True)
class MetaStudyIdentityResult:
    term: str
    source_position: int
    display_position: int

    def __post_init__(self) -> None:
        if not _text(self.term) or any(
            type(value) is not int or value < 0
            for value in (self.source_position, self.display_position)
        ):
            raise ValueError("meta-analysis study identity is invalid")


@dataclass(frozen=True, slots=True)
class RobustMetaStartResult:
    start: Literal["m5_reml", "median_mad", "fixed_effect"]
    converged: bool
    cycles: int
    successive_cycles: int
    scaled_mu: float
    scaled_tau_squared: float
    log_likelihood: float
    score_norm: float
    boundary: bool

    def __post_init__(self) -> None:
        if self.start not in {"m5_reml", "median_mad", "fixed_effect"}:
            raise ValueError("robust start identity is unsupported")
        if type(self.converged) is not bool or type(self.boundary) is not bool:
            raise ValueError("robust convergence flags must be boolean")
        if (
            type(self.cycles) is not int
            or type(self.successive_cycles) is not int
            or not 0 <= self.cycles <= 10_000
            or not 0 <= self.successive_cycles <= 3
        ):
            raise ValueError("robust convergence cycle counts are invalid")
        for value in (
            self.scaled_mu,
            self.scaled_tau_squared,
            self.log_likelihood,
            self.score_norm,
        ):
            _finite(value, "robust convergence value")
        if self.scaled_tau_squared < 0.0 or self.score_norm < 0.0:
            raise ValueError("robust convergence values are inadmissible")
        if self.converged != (self.successive_cycles == 3 and self.score_norm <= 1e-8):
            raise ValueError("robust convergence state does not meet tolerance")
        if self.boundary != (self.scaled_tau_squared == 0.0):
            raise ValueError("robust boundary flag must match tau_squared")


@dataclass(frozen=True, slots=True)
class RobustMetaConvergenceResult:
    algorithm: Literal["three_start_ecme_fixed_point"]
    degrees_of_freedom: Literal[4]
    maximum_cycles_per_start: Literal[10000]
    log_likelihood_relative_tolerance: float
    parameter_tolerance: float
    score_tolerance: float
    ambiguity_likelihood_tolerance: float
    ambiguity_parameter_tolerance: float
    selected_start: Literal["m5_reml", "median_mad", "fixed_effect"]
    starts: tuple[RobustMetaStartResult, ...]
    center: float
    scale: float
    profile_root_iterations: int
    profile_evaluations: int
    converged: bool

    def __post_init__(self) -> None:
        if (
            self.algorithm != "three_start_ecme_fixed_point"
            or self.degrees_of_freedom != 4
            or self.maximum_cycles_per_start != 10_000
            or self.log_likelihood_relative_tolerance != 1e-10
            or self.parameter_tolerance != 1e-8
            or self.score_tolerance != 1e-8
            or self.ambiguity_likelihood_tolerance != 1e-8
            or self.ambiguity_parameter_tolerance != 1e-7
            or len(self.starts) != 3
            or tuple(item.start for item in self.starts)
            != ("m5_reml", "median_mad", "fixed_effect")
            or self.selected_start not in {item.start for item in self.starts}
            or not self.converged
            or not any(item.converged for item in self.starts)
            or not next(
                item for item in self.starts if item.start == self.selected_start
            ).converged
        ):
            raise ValueError("robust meta-analysis convergence record is invalid")
        _finite(self.center, "robust center")
        _finite(self.scale, "robust scale")
        if self.scale <= 0.0 or any(
            type(value) is not int or value < 0
            for value in (self.profile_root_iterations, self.profile_evaluations)
        ):
            raise ValueError("robust scaling or profile counts are invalid")


@dataclass(frozen=True, slots=True)
class RobustMetaStudyResult:
    identity: MetaStudyIdentityResult
    estimate: float
    standard_error: float
    sampling_interval: IntervalResult
    standardized_residual: float
    latent_precision: float
    effective_precision: float
    normalized_share: float
    weighted_contribution: float

    def __post_init__(self) -> None:
        for value in (
            self.estimate,
            self.standard_error,
            self.standardized_residual,
            self.latent_precision,
            self.effective_precision,
            self.normalized_share,
            self.weighted_contribution,
        ):
            _finite(value, "robust study value")
        if (
            self.standard_error <= 0.0
            or not 0.0 < self.latent_precision <= 1.25
            or self.effective_precision <= 0.0
            or not 0.0 < self.normalized_share <= 1.0
            or self.sampling_interval.target != "study_effect"
            or self.sampling_interval.method
            != "normal_approximation_from_reported_standard_error"
            or not self.sampling_interval.low
            <= self.estimate
            <= self.sampling_interval.high
        ):
            raise ValueError("robust study record is inconsistent")
        if not isclose(
            self.weighted_contribution,
            self.normalized_share * self.estimate,
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            raise ValueError("robust study contribution does not reconcile")


@dataclass(frozen=True, slots=True)
class RobustMetaPooledResult:
    method: Literal["student_t4_marginal_ml_profile_likelihood"]
    estimate: float
    tau_squared: float
    tau: float
    statistic_name: Literal["profile_likelihood_ratio_chi_squared_1"]
    statistic: float
    p_value: float
    interval: IntervalResult
    heterogeneity_absence_reason: Literal["not_defined_for_student_t4_working_model"]
    prediction_absence_reason: Literal["robust_meta_prediction_method_not_approved"]

    def __post_init__(self) -> None:
        if (
            self.method != "student_t4_marginal_ml_profile_likelihood"
            or self.statistic_name != "profile_likelihood_ratio_chi_squared_1"
            or self.heterogeneity_absence_reason
            != "not_defined_for_student_t4_working_model"
            or self.prediction_absence_reason
            != "robust_meta_prediction_method_not_approved"
        ):
            raise ValueError("robust pooled method identity is unsupported")
        for value in (
            self.estimate,
            self.tau_squared,
            self.tau,
            self.statistic,
            self.p_value,
        ):
            _finite(value, "robust pooled value")
        if (
            self.tau_squared < 0.0
            or self.tau < 0.0
            or not isclose(
                self.tau * self.tau,
                self.tau_squared,
                rel_tol=1e-12,
                abs_tol=1e-15,
            )
            or self.statistic < 0.0
            or not 0.0 <= self.p_value <= 1.0
            or self.interval.target != "population_student_t4_location"
            or self.interval.method != "student_t4_profile_likelihood"
            or not self.interval.low <= self.estimate <= self.interval.high
        ):
            raise ValueError("robust pooled values are inconsistent")


@dataclass(frozen=True, slots=True)
class RobustMetaAnalysisResult:
    estimand: str
    effect_scale: str
    effect_direction: str
    effect_units: str
    dependence: Literal["independent"]
    null_value: float
    sampling_model: Literal["student_t4_random_effects"]
    pooled: RobustMetaPooledResult
    convergence: RobustMetaConvergenceResult

    def __post_init__(self) -> None:
        if any(
            not _text(value)
            for value in (
                self.estimand,
                self.effect_scale,
                self.effect_direction,
                self.effect_units,
            )
        ) or not isfinite(self.null_value):
            raise ValueError("robust meta-analysis declarations are invalid")
        if (
            self.dependence != "independent"
            or self.sampling_model != "student_t4_random_effects"
        ):
            raise ValueError("robust meta-analysis model identity is unsupported")


@dataclass(frozen=True, slots=True)
class RobustMetaResult:
    schema_version: Literal[2]
    analysis: Literal["ggcoefstats_meta_analysis"]
    mode: Literal["robust"]
    method: Literal["student_t4_marginal_ml_profile_likelihood"]
    compatibility_tier: Literal["adapted"]
    source_kind: Literal["table"]
    inference_profile: Literal["study_effect_standard_error"]
    input_rows: int
    retained_rows: int
    source_order: tuple[str, ...]
    display_order: tuple[str, ...]
    studies: tuple[RobustMetaStudyResult, ...]
    meta_analysis: RobustMetaAnalysisResult
    conf_level: float
    stats_labels: bool
    only_significant: bool
    convergence: RobustMetaConvergenceResult
    work: M6CWorkResult
    limits: M6CMetaResourceLimits
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        if (
            self.schema_version != 2
            or self.analysis != "ggcoefstats_meta_analysis"
            or self.mode != "robust"
            or self.method != "student_t4_marginal_ml_profile_likelihood"
            or self.compatibility_tier != "adapted"
            or self.source_kind != "table"
            or self.inference_profile != "study_effect_standard_error"
        ):
            raise ValueError("robust meta result identity is unsupported")
        if (
            type(self.input_rows) is not int
            or self.input_rows != self.retained_rows
            or self.retained_rows != len(self.studies)
            or not 10 <= self.retained_rows <= 500
            or self.source_order != tuple(item.identity.term for item in self.studies)
            or self.display_order != self.source_order
            or len(set(self.source_order)) != self.retained_rows
            or tuple(item.identity.source_position for item in self.studies)
            != tuple(range(self.retained_rows))
            or tuple(item.identity.display_position for item in self.studies)
            != tuple(range(self.retained_rows))
        ):
            raise ValueError("robust meta study audit does not reconcile")
        if (
            not 0.80 <= self.conf_level <= 0.99
            or type(self.stats_labels) is not bool
            or type(self.only_significant) is not bool
            or self.only_significant
            or self.convergence != self.meta_analysis.convergence
            or abs(self.meta_analysis.pooled.interval.level - self.conf_level) > 1e-15
        ):
            raise ValueError("robust meta reporting policy is inconsistent")
        if abs(sum(item.normalized_share for item in self.studies) - 1.0) > 1e-12:
            raise ValueError("robust study shares must sum to one")
        pooled = sum(item.weighted_contribution for item in self.studies)
        if not isclose(
            pooled,
            self.meta_analysis.pooled.estimate,
            rel_tol=1e-8,
            abs_tol=1e-8,
        ):
            raise ValueError("robust study contributions must reproduce the estimate")
        if self.retained_rows > min(
            self.limits.maximum_studies, self.limits.maximum_rendered_points
        ) or (self.stats_labels and self.retained_rows > self.limits.maximum_labels):
            raise ValueError("robust meta result exceeds retained limits")
        expected_warning = self.retained_rows < 20
        if expected_warning != (
            self.warnings == ("few_studies_robust_profile_likelihood",)
        ):
            raise ValueError("robust few-study warning is inconsistent")
        if self.work.maximum_work != self.limits.maximum_work:
            raise ValueError("robust work and limits disagree")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class BayesianMetaPriorResult:
    mean_family: Literal["normal"]
    mean_location: float
    mean_scale: float
    mean_prior_95_interval: IntervalResult
    tau_family: Literal["half_normal"]
    tau_scale: float
    tau_prior_median: float
    tau_prior_95_quantile: float
    prior_predictive_effect_standard_deviation: float
    proper: bool

    def __post_init__(self) -> None:
        for value in (
            self.mean_location,
            self.mean_scale,
            self.tau_scale,
            self.tau_prior_median,
            self.tau_prior_95_quantile,
            self.prior_predictive_effect_standard_deviation,
        ):
            _finite(value, "Bayesian meta prior value")
        if (
            self.mean_family != "normal"
            or self.tau_family != "half_normal"
            or not self.proper
            or min(
                self.mean_scale,
                self.tau_scale,
                self.tau_prior_median,
                self.tau_prior_95_quantile,
                self.prior_predictive_effect_standard_deviation,
            )
            <= 0.0
            or self.mean_prior_95_interval.target != "prior_population_mean"
            or self.mean_prior_95_interval.method != "normal_prior"
            or self.mean_prior_95_interval.level != 0.95
            or not self.mean_prior_95_interval.low
            < self.mean_location
            < self.mean_prior_95_interval.high
        ):
            raise ValueError("Bayesian meta prior record is inconsistent")


@dataclass(frozen=True, slots=True)
class BayesianMetaEvidenceResult:
    null_hypothesis: Literal["mu_equals_null_value"]
    alternative_hypothesis: Literal["mu_normal_prior_centered_at_null_value"]
    log_bf10: float
    display: str
    prior_model_odds: float

    def __post_init__(self) -> None:
        _finite(self.log_bf10, "Bayesian meta log BF10")
        if (
            self.null_hypothesis != "mu_equals_null_value"
            or self.alternative_hypothesis != "mu_normal_prior_centered_at_null_value"
            or self.display != bounded_bf10_text(self.log_bf10)
            or self.prior_model_odds != 1.0
        ):
            raise ValueError("Bayesian meta evidence identity is inconsistent")


@dataclass(frozen=True, slots=True)
class BayesianMetaQuadratureResult:
    algorithm: Literal["adaptive_gauss_kronrod"]
    transformation: Literal["tau=prior_tau_scale*x/(1-x)"]
    epsabs: float
    epsrel: float
    maximum_subdivisions: Literal[200]
    evaluations: int
    h1_log_marginal: float
    h0_log_marginal: float
    h1_relative_error: float
    h0_relative_error: float
    posterior_normalization_error: float
    cdf_monotonicity_checked: bool
    root_brackets: tuple[tuple[str, float, float], ...]
    numpy_version: str
    scipy_version: str
    converged: bool

    def __post_init__(self) -> None:
        if (
            self.algorithm != "adaptive_gauss_kronrod"
            or self.transformation != "tau=prior_tau_scale*x/(1-x)"
            or self.epsabs != 1e-12
            or self.epsrel != 1e-10
            or self.maximum_subdivisions != 200
            or type(self.evaluations) is not int
            or self.evaluations < 1
            or not self.cdf_monotonicity_checked
            or not self.converged
            or not self.numpy_version
            or not self.scipy_version
        ):
            raise ValueError("Bayesian meta quadrature identity is invalid")
        for value in (
            self.h1_log_marginal,
            self.h0_log_marginal,
            self.h1_relative_error,
            self.h0_relative_error,
            self.posterior_normalization_error,
        ):
            _finite(value, "Bayesian meta quadrature value")
        if (
            min(self.h1_relative_error, self.h0_relative_error) < 0.0
            or max(self.h1_relative_error, self.h0_relative_error) > 1e-10
            or not 0.0 <= self.posterior_normalization_error <= 1e-10
            or len(self.root_brackets) != 9
            or any(
                not name or not isfinite(low) or not isfinite(high) or low >= high
                for name, low, high in self.root_brackets
            )
        ):
            raise ValueError("Bayesian meta quadrature diagnostics failed")


@dataclass(frozen=True, slots=True)
class BayesianMetaFitResult:
    label: Literal[
        "primary",
        "mean_scale_half",
        "mean_scale_double",
        "tau_scale_half",
        "tau_scale_double",
    ]
    prior: BayesianMetaPriorResult
    population_mean: BayesianPosteriorSummary
    tau: BayesianPosteriorSummary
    tau_squared: BayesianPosteriorSummary
    true_effect_prediction: BayesianPosteriorSummary
    evidence: BayesianMetaEvidenceResult
    quadrature: BayesianMetaQuadratureResult

    def __post_init__(self) -> None:
        if self.label not in {
            "primary",
            "mean_scale_half",
            "mean_scale_double",
            "tau_scale_half",
            "tau_scale_double",
        }:
            raise ValueError("Bayesian meta fit label is unsupported")
        summaries = (
            (self.population_mean, "population_mean", self.prior.mean_location),
            (self.tau, "between_study_tau", 0.0),
            (self.tau_squared, "between_study_tau_squared", 0.0),
            (
                self.true_effect_prediction,
                "true_effect_in_new_exchangeable_study",
                self.prior.mean_location,
            ),
        )
        if any(
            summary.target != target or summary.null_value != null
            for summary, target, null in summaries
        ):
            raise ValueError("Bayesian meta posterior target is inconsistent")
        if (
            not isclose(
                self.tau_squared.median,
                self.tau.median * self.tau.median,
                rel_tol=1e-10,
                abs_tol=1e-12,
            )
            or not isclose(
                self.tau_squared.interval.low,
                self.tau.interval.low * self.tau.interval.low,
                rel_tol=1e-10,
                abs_tol=1e-12,
            )
            or not isclose(
                self.tau_squared.interval.high,
                self.tau.interval.high * self.tau.interval.high,
                rel_tol=1e-10,
                abs_tol=1e-12,
            )
        ):
            raise ValueError("Bayesian tau-squared summary must transform tau")


@dataclass(frozen=True, slots=True)
class BayesianMetaStudyResult:
    identity: MetaStudyIdentityResult
    estimate: float
    standard_error: float
    sampling_interval: IntervalResult

    def __post_init__(self) -> None:
        _finite(self.estimate, "Bayesian meta study estimate")
        _finite(self.standard_error, "Bayesian meta study standard error")
        if (
            self.standard_error <= 0.0
            or self.sampling_interval.target != "study_effect"
            or self.sampling_interval.method
            != "normal_approximation_from_reported_standard_error"
            or not self.sampling_interval.low
            <= self.estimate
            <= self.sampling_interval.high
        ):
            raise ValueError("Bayesian meta study record is inconsistent")


@dataclass(frozen=True, slots=True)
class BayesianMetaResult:
    schema_version: Literal[3]
    analysis: Literal["ggcoefstats_meta_analysis"]
    mode: Literal["bayes"]
    method: Literal["proper_prior_normal_normal_quadrature"]
    compatibility_tier: Literal["adapted"]
    source_kind: Literal["table"]
    inference_profile: Literal["study_effect_standard_error"]
    estimand: str
    effect_scale: str
    effect_direction: str
    effect_units: str
    dependence: Literal["independent"]
    null_value: float
    input_rows: int
    retained_rows: int
    source_order: tuple[str, ...]
    display_order: tuple[str, ...]
    studies: tuple[BayesianMetaStudyResult, ...]
    credible_level: float
    primary: BayesianMetaFitResult
    sensitivities: tuple[BayesianMetaFitResult, ...]
    stats_labels: bool
    only_significant: bool
    work: M6CWorkResult
    limits: M6CMetaResourceLimits
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        if (
            self.schema_version != 3
            or self.analysis != "ggcoefstats_meta_analysis"
            or self.mode != "bayes"
            or self.method != "proper_prior_normal_normal_quadrature"
            or self.compatibility_tier != "adapted"
            or self.source_kind != "table"
            or self.inference_profile != "study_effect_standard_error"
            or self.dependence != "independent"
        ):
            raise ValueError("Bayesian meta result identity is unsupported")
        if any(
            not _text(value)
            for value in (
                self.estimand,
                self.effect_scale,
                self.effect_direction,
                self.effect_units,
            )
        ) or not isfinite(self.null_value):
            raise ValueError("Bayesian meta declarations are invalid")
        if (
            type(self.input_rows) is not int
            or self.input_rows != self.retained_rows
            or self.retained_rows != len(self.studies)
            or not 3 <= self.retained_rows <= 500
            or self.source_order != tuple(item.identity.term for item in self.studies)
            or self.display_order != self.source_order
            or len(set(self.source_order)) != self.retained_rows
            or tuple(item.identity.source_position for item in self.studies)
            != tuple(range(self.retained_rows))
            or tuple(item.identity.display_position for item in self.studies)
            != tuple(range(self.retained_rows))
        ):
            raise ValueError("Bayesian meta study audit does not reconcile")
        if (
            not 0.80 <= self.credible_level <= 0.99
            or type(self.stats_labels) is not bool
            or type(self.only_significant) is not bool
            or self.only_significant
            or self.primary.label != "primary"
            or tuple(item.label for item in self.sensitivities)
            != (
                "mean_scale_half",
                "mean_scale_double",
                "tau_scale_half",
                "tau_scale_double",
            )
        ):
            raise ValueError("Bayesian meta reporting or sensitivity set is invalid")
        fits = (self.primary, *self.sensitivities)
        if any(
            summary.interval.level != self.credible_level
            for fit in fits
            for summary in (
                fit.population_mean,
                fit.tau,
                fit.tau_squared,
                fit.true_effect_prediction,
            )
        ):
            raise ValueError("Bayesian meta interval levels must match")
        primary_mean = self.primary.prior.mean_scale
        primary_tau = self.primary.prior.tau_scale
        expected_scales = (
            (0.5 * primary_mean, primary_tau),
            (2.0 * primary_mean, primary_tau),
            (primary_mean, 0.5 * primary_tau),
            (primary_mean, 2.0 * primary_tau),
        )
        if any(
            not isclose(fit.prior.mean_scale, mean_scale, rel_tol=0.0, abs_tol=0.0)
            or not isclose(fit.prior.tau_scale, tau_scale, rel_tol=0.0, abs_tol=0.0)
            for fit, (mean_scale, tau_scale) in zip(
                self.sensitivities, expected_scales, strict=True
            )
        ):
            raise ValueError("Bayesian meta sensitivity prior scales are incomplete")
        if self.retained_rows > min(
            self.limits.maximum_studies, self.limits.maximum_rendered_points
        ) or (self.stats_labels and self.retained_rows > self.limits.maximum_labels):
            raise ValueError("Bayesian meta result exceeds retained limits")
        expected_warning = self.retained_rows < 5
        if expected_warning != (self.warnings == ("few_studies_prior_sensitive",)):
            raise ValueError("Bayesian few-study warning is inconsistent")
        if (
            self.work.maximum_work != self.limits.maximum_work
            or self.work.actual_work != sum(fit.quadrature.evaluations for fit in fits)
        ):
            raise ValueError("Bayesian work accounting does not reconcile")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
