"""Typed schema-v1 results for coefficients and M5B meta-analysis."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isclose, isfinite
from typing import Any, Literal

from plotsalot.result import IntervalResult


def _probability(value: float, label: str) -> None:
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{label} must lie within [0, 1]")


def _is_nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value)


@dataclass(frozen=True, slots=True)
class CoefficientResourceLimits:
    maximum_studies: int
    maximum_rendered_points: int
    maximum_labels: int

    def __post_init__(self) -> None:
        if any(
            type(value) is not int or value < 1
            for value in (
                self.maximum_studies,
                self.maximum_rendered_points,
                self.maximum_labels,
            )
        ):
            raise ValueError("coefficient resource limits must be positive integers")


@dataclass(frozen=True, slots=True)
class CoefficientInferenceResult:
    source: str
    standard_error: float
    interval: IntervalResult
    statistic_name: Literal["z"]
    statistic: float
    df: None
    p_value: float
    significant: bool

    def __post_init__(self) -> None:
        if self.source != "study_normal_approximation_from_reported_standard_error":
            raise ValueError("study inference source is unsupported")
        if not isfinite(self.standard_error) or self.standard_error <= 0.0:
            raise ValueError("study standard error must be finite and positive")
        if not isfinite(self.statistic):
            raise ValueError("study statistic must be finite")
        if self.statistic_name != "z" or self.df is not None:
            raise ValueError("study inference must use z with no degrees of freedom")
        if type(self.significant) is not bool:
            raise ValueError("study significance must be boolean")
        _probability(self.p_value, "study p_value")
        if (
            self.interval.target != "study_effect"
            or self.interval.method
            != "normal_approximation_from_reported_standard_error"
        ):
            raise ValueError("study interval is unsupported")


@dataclass(frozen=True, slots=True)
class CoefficientTermResult:
    term: str
    source_position: int
    display_position: int
    estimate: float
    inference: CoefficientInferenceResult
    sampling_variance: float
    random_effects_weight: float
    normalized_weight: float
    weighted_contribution: float

    def __post_init__(self) -> None:
        if not _is_nonempty_string(self.term):
            raise ValueError("coefficient term must be nonempty")
        if type(self.source_position) is not int or self.source_position < 0:
            raise ValueError("source position must be a non-negative integer")
        if type(self.display_position) is not int or self.display_position < 0:
            raise ValueError("display position must be a non-negative integer")
        numeric = (
            self.estimate,
            self.sampling_variance,
            self.random_effects_weight,
            self.normalized_weight,
            self.weighted_contribution,
        )
        if not all(isfinite(value) for value in numeric):
            raise ValueError("coefficient term values must be finite")
        if self.sampling_variance <= 0.0 or self.random_effects_weight <= 0.0:
            raise ValueError("study variances and weights must be positive")
        if not 0.0 < self.normalized_weight <= 1.0:
            raise ValueError("normalized study weight must lie within (0, 1]")
        if (
            not self.inference.interval.low
            <= self.estimate
            <= self.inference.interval.high
        ):
            raise ValueError("study estimate must lie within its interval")
        if abs(self.sampling_variance - self.inference.standard_error**2) > max(
            1e-15, 1e-12 * self.sampling_variance
        ):
            raise ValueError("sampling variance must equal squared standard error")
        if not isclose(
            self.weighted_contribution,
            self.normalized_weight * self.estimate,
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            raise ValueError("weighted contribution must match estimate and weight")


@dataclass(frozen=True, slots=True)
class MetaConvergenceResult:
    method: Literal["reml_intercept_only"]
    converged: bool
    boundary: bool
    scale_factor: float
    score_at_zero: float
    score_at_solution: float
    bracket_low: float
    bracket_high: float
    bracket_expansions: int
    iterations: int
    score_tolerance: float
    absolute_tolerance: float
    relative_tolerance: float

    def __post_init__(self) -> None:
        if self.method != "reml_intercept_only":
            raise ValueError("REML convergence method is unsupported")
        if type(self.converged) is not bool or type(self.boundary) is not bool:
            raise ValueError("REML convergence flags must be boolean")
        numeric = (
            self.scale_factor,
            self.score_at_zero,
            self.score_at_solution,
            self.bracket_low,
            self.bracket_high,
            self.score_tolerance,
            self.absolute_tolerance,
            self.relative_tolerance,
        )
        if not all(isfinite(value) for value in numeric) or self.scale_factor <= 0.0:
            raise ValueError("REML convergence values must be finite")
        if not self.converged or self.bracket_low < 0.0 or self.bracket_high < 0.0:
            raise ValueError("REML result must be converged on a nonnegative bracket")
        if any(
            type(value) is not int or value < 0
            for value in (self.bracket_expansions, self.iterations)
        ):
            raise ValueError("REML iteration counts must be non-negative integers")
        if (
            min(
                self.score_tolerance,
                self.absolute_tolerance,
                self.relative_tolerance,
            )
            <= 0.0
        ):
            raise ValueError("REML tolerances must be positive")
        if self.boundary and (
            self.bracket_low != 0.0 or self.bracket_high != 0.0 or self.iterations != 0
        ):
            raise ValueError("boundary REML convergence must use the zero bracket")


@dataclass(frozen=True, slots=True)
class PooledEffectResult:
    method: Literal["modified_hartung_knapp_random_effects_mean"]
    estimate: float
    standard_error: float
    conventional_variance: float
    adjusted_variance: float
    q_hk: float
    q_star: float
    statistic_name: Literal["t"]
    statistic: float
    df: int
    p_value: float
    interval: IntervalResult

    def __post_init__(self) -> None:
        if (
            self.method != "modified_hartung_knapp_random_effects_mean"
            or self.statistic_name != "t"
        ):
            raise ValueError("pooled method or statistic is unsupported")
        numeric = (
            self.estimate,
            self.standard_error,
            self.conventional_variance,
            self.adjusted_variance,
            self.q_hk,
            self.q_star,
            self.statistic,
        )
        if not all(isfinite(value) for value in numeric):
            raise ValueError("pooled effect values must be finite")
        if (
            min(
                self.standard_error,
                self.conventional_variance,
                self.adjusted_variance,
            )
            <= 0.0
        ):
            raise ValueError("pooled uncertainty must be positive")
        if self.q_hk < 0.0 or self.q_star < 1.0 or self.q_star < self.q_hk:
            raise ValueError("Hartung-Knapp scale values are invalid")
        if self.q_star != max(1.0, self.q_hk):
            raise ValueError("q_star must be max(1, q_hk)")
        if not isclose(
            self.standard_error**2,
            self.adjusted_variance,
            rel_tol=1e-12,
            abs_tol=1e-15,
        ):
            raise ValueError("pooled standard error must match adjusted variance")
        if type(self.df) is not int or self.df < 2:
            raise ValueError("pooled test df must be an integer of at least two")
        _probability(self.p_value, "pooled p_value")
        if (
            self.interval.target != "mean_of_true_effect_distribution"
            or self.interval.method != "modified_hartung_knapp_random_effects_mean"
            or not self.interval.low <= self.estimate <= self.interval.high
        ):
            raise ValueError("pooled confidence interval is unsupported")


@dataclass(frozen=True, slots=True)
class PredictionResult:
    interval: IntervalResult | None
    absence_reason: Literal["fewer_than_five_studies"] | None

    def __post_init__(self) -> None:
        if (self.interval is None) == (self.absence_reason is None):
            raise ValueError(
                "prediction requires exactly one interval or absence reason"
            )
        if self.interval is not None and (
            self.interval.target != "true_effect_in_new_study"
            or self.interval.method
            != "modified_hartung_knapp_normal_random_effects_prediction_interval"
        ):
            raise ValueError("prediction interval is unsupported")
        if self.interval is None and self.absence_reason != "fewer_than_five_studies":
            raise ValueError("prediction absence reason is unsupported")


@dataclass(frozen=True, slots=True)
class HeterogeneityResult:
    q: float
    df: int
    p_value: float
    reference_mean: float
    i_squared: float
    tau_squared: float
    tau: float
    tau_squared_interval: None
    tau_squared_interval_absence_reason: Literal["not_in_m5b"]

    def __post_init__(self) -> None:
        numeric = (
            self.q,
            self.reference_mean,
            self.i_squared,
            self.tau_squared,
            self.tau,
        )
        if not all(isfinite(value) for value in numeric):
            raise ValueError("heterogeneity values must be finite")
        if self.q < 0.0 or type(self.df) is not int or self.df < 2:
            raise ValueError("heterogeneity Q and df are invalid")
        _probability(self.p_value, "heterogeneity p_value")
        if not 0.0 <= self.i_squared <= 1.0 or self.tau_squared < 0.0 or self.tau < 0.0:
            raise ValueError("heterogeneity scale values are invalid")
        if abs(self.tau**2 - self.tau_squared) > max(1e-15, 1e-12 * self.tau_squared):
            raise ValueError("tau must be the square root of tau_squared")
        if (
            self.tau_squared_interval is not None
            or self.tau_squared_interval_absence_reason != "not_in_m5b"
        ):
            raise ValueError("M5B must record the absent tau_squared interval")


@dataclass(frozen=True, slots=True)
class MetaAnalysisResult:
    estimand: str
    effect_scale: str
    effect_direction: str
    effect_units: str
    dependence: Literal["independent"]
    null_value: float
    sampling_model: Literal["normal_normal_random_effects"]
    estimator: Literal["reml_intercept_only"]
    pooled: PooledEffectResult
    prediction: PredictionResult
    heterogeneity: HeterogeneityResult
    convergence: MetaConvergenceResult

    def __post_init__(self) -> None:
        declarations = (
            self.estimand,
            self.effect_scale,
            self.effect_direction,
            self.effect_units,
        )
        if any(not _is_nonempty_string(value) for value in declarations):
            raise ValueError("meta-analysis declarations must be nonempty")
        if not isfinite(self.null_value):
            raise ValueError("meta-analysis null_value must be finite")
        if (
            self.dependence != "independent"
            or self.sampling_model != "normal_normal_random_effects"
            or self.estimator != "reml_intercept_only"
        ):
            raise ValueError("meta-analysis model identity is unsupported")
        if self.estimator != self.convergence.method:
            raise ValueError(
                "meta-analysis estimator and convergence method must match"
            )
        if self.heterogeneity.df != self.pooled.df:
            raise ValueError("pooled and heterogeneity degrees of freedom must match")


@dataclass(frozen=True, slots=True)
class CoefficientResult:
    schema_version: int
    analysis: Literal["ggcoefstats_meta_analysis"]
    source_kind: Literal["table"]
    inference_profile: Literal["study_effect_standard_error"]
    term_column: Literal["term"]
    estimate_column: Literal["estimate"]
    standard_error_column: Literal["standard_error"]
    input_rows: int
    retained_rows: int
    source_order: tuple[str, ...]
    display_order: tuple[str, ...]
    terms: tuple[CoefficientTermResult, ...]
    meta_analysis: MetaAnalysisResult
    conf_level: float
    alpha: float
    stats_labels: bool
    only_significant: bool
    limits: CoefficientResourceLimits
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("coefficient schema_version must be 1")
        if (
            self.analysis != "ggcoefstats_meta_analysis"
            or self.source_kind != "table"
            or self.inference_profile != "study_effect_standard_error"
            or (
                self.term_column,
                self.estimate_column,
                self.standard_error_column,
            )
            != ("term", "estimate", "standard_error")
        ):
            raise ValueError("coefficient result identity is unsupported")
        if type(self.input_rows) is not int or type(self.retained_rows) is not int:
            raise ValueError("coefficient row counts must be integers")
        if (
            type(self.stats_labels) is not bool
            or type(self.only_significant) is not bool
        ):
            raise ValueError("coefficient label policies must be boolean")
        if self.input_rows != self.retained_rows or self.retained_rows < 3:
            raise ValueError(
                "M5B retains every input study and requires at least three"
            )
        if len(self.terms) != self.retained_rows:
            raise ValueError("coefficient terms must match retained rows")
        if self.source_order != tuple(term.term for term in self.terms):
            raise ValueError("source order must match study term order")
        if self.display_order != self.source_order:
            raise ValueError("M5B display order must preserve source order")
        if len(set(self.source_order)) != len(self.source_order):
            raise ValueError("coefficient term identities must be unique")
        if tuple(term.source_position for term in self.terms) != tuple(
            range(self.retained_rows)
        ) or tuple(term.display_position for term in self.terms) != tuple(
            range(self.retained_rows)
        ):
            raise ValueError("coefficient positions must be complete and ordered")
        if not isfinite(self.conf_level) or not 0.0 < self.conf_level < 1.0:
            raise ValueError("conf_level must lie within (0, 1)")
        if abs(self.alpha - (1.0 - self.conf_level)) > 1e-15:
            raise ValueError("alpha must equal one minus conf_level")
        if any(
            abs(term.inference.interval.level - self.conf_level) > 1e-15
            for term in self.terms
        ):
            raise ValueError("study interval levels must match conf_level")
        if any(
            term.inference.significant != (term.inference.p_value < self.alpha)
            for term in self.terms
        ):
            raise ValueError("study significance must use the result alpha")
        for term in self.terms:
            expected_statistic = (
                term.estimate - self.meta_analysis.null_value
            ) / term.inference.standard_error
            interval = term.inference.interval
            if not isclose(
                term.inference.statistic,
                expected_statistic,
                rel_tol=1e-12,
                abs_tol=1e-12,
            ) or not isclose(
                interval.low + interval.high,
                2.0 * term.estimate,
                rel_tol=1e-12,
                abs_tol=1e-12,
            ):
                raise ValueError("study inference does not reconcile")
        if abs(self.meta_analysis.pooled.interval.level - self.conf_level) > 1e-15:
            raise ValueError("pooled interval level must match conf_level")
        prediction = self.meta_analysis.prediction.interval
        if prediction is not None and abs(prediction.level - self.conf_level) > 1e-15:
            raise ValueError("prediction interval level must match conf_level")
        if prediction is not None and not isclose(
            prediction.low + prediction.high,
            2.0 * self.meta_analysis.pooled.estimate,
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            raise ValueError("prediction interval must center on the pooled estimate")
        normalized = sum(term.normalized_weight for term in self.terms)
        contributions = sum(term.weighted_contribution for term in self.terms)
        if abs(normalized - 1.0) > 1e-12:
            raise ValueError("normalized study weights must sum to one")
        if abs(contributions - self.meta_analysis.pooled.estimate) > max(
            1e-12, 1e-12 * abs(contributions)
        ):
            raise ValueError("study contributions must reproduce the pooled estimate")
        tau_squared = self.meta_analysis.heterogeneity.tau_squared
        expected_weights = tuple(
            1.0 / (term.sampling_variance + tau_squared) for term in self.terms
        )
        if any(
            abs(term.random_effects_weight - expected) > max(1e-12, 1e-12 * expected)
            for term, expected in zip(self.terms, expected_weights, strict=True)
        ):
            raise ValueError("study weights must match the retained tau_squared")
        total_weight = sum(expected_weights)
        if any(
            not isclose(
                term.normalized_weight,
                expected / total_weight,
                rel_tol=1e-12,
                abs_tol=1e-12,
            )
            for term, expected in zip(self.terms, expected_weights, strict=True)
        ):
            raise ValueError("normalized study weights must match raw weights")
        pooled = self.meta_analysis.pooled
        if pooled.df != self.retained_rows - 1 or not isclose(
            pooled.statistic,
            (pooled.estimate - self.meta_analysis.null_value) / pooled.standard_error,
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            raise ValueError("pooled test does not reconcile")
        if not isclose(
            pooled.conventional_variance,
            1.0 / total_weight,
            rel_tol=1e-12,
            abs_tol=1e-12,
        ) or not isclose(
            pooled.adjusted_variance,
            pooled.q_star / total_weight,
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            raise ValueError("pooled variances do not reconcile")
        if self.meta_analysis.convergence.boundary != (tau_squared == 0.0):
            raise ValueError("REML boundary status must match tau_squared")
        prediction_present = self.meta_analysis.prediction.interval is not None
        if prediction_present != (self.retained_rows >= 5):
            raise ValueError(
                "prediction availability must use the five-study threshold"
            )
        if self.retained_rows > min(
            self.limits.maximum_studies, self.limits.maximum_rendered_points
        ):
            raise ValueError("study count exceeds retained resource limits")
        label_count = (
            sum(term.inference.significant for term in self.terms)
            if self.only_significant
            else len(self.terms)
        )
        if self.stats_labels and label_count > self.limits.maximum_labels:
            raise ValueError("requested study labels exceed maximum_labels")
        if any(not warning for warning in self.warnings):
            raise ValueError("coefficient warnings must be nonempty")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
