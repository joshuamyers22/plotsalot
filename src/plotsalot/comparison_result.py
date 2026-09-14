"""Typed results for independent and repeated comparison analyses."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any, Literal

from plotsalot.result import (
    EffectSizeResult,
    IntervalResult,
    ResourceLimits,
    SampleAudit,
    ScalarIdentity,
)

ComparisonDesign = Literal["between", "within"]
PairwiseDisplay = Literal["significant", "non-significant", "all", "none"]


def _validate_identity(value: ScalarIdentity, name: str) -> None:
    if isinstance(value, str) and not value:
        raise ValueError(f"{name} must be non-empty")
    if isinstance(value, float) and not isfinite(value):
        raise ValueError(f"numeric {name} must be finite")


@dataclass(frozen=True, slots=True)
class RepeatedSampleAudit:
    """Row and subject counts for a complete-block repeated analysis."""

    input_rows: int
    analyzed_rows: int
    analyzed_subjects: int
    dropped_null_identity_rows: int
    dropped_null_value_rows: int
    excluded_incomplete_rows: int
    excluded_incomplete_subjects: int

    def __post_init__(self) -> None:
        values = (
            self.input_rows,
            self.analyzed_rows,
            self.analyzed_subjects,
            self.dropped_null_identity_rows,
            self.dropped_null_value_rows,
            self.excluded_incomplete_rows,
            self.excluded_incomplete_subjects,
        )
        if any(type(value) is not int or value < 0 for value in values):
            raise ValueError("repeated sample counts must be non-negative integers")
        if self.input_rows != (
            self.analyzed_rows
            + self.dropped_null_identity_rows
            + self.dropped_null_value_rows
            + self.excluded_incomplete_rows
        ):
            raise ValueError("repeated sample row counts must reconcile")
        if self.analyzed_subjects < 1:
            raise ValueError("repeated sample requires an analyzed subject")


@dataclass(frozen=True, slots=True)
class ComparisonLevelResult:
    """Descriptive result for one resolved group or condition level."""

    level: ScalarIdentity
    n_obs: int
    mean: float
    standard_deviation: float
    interval: IntervalResult

    def __post_init__(self) -> None:
        _validate_identity(self.level, "comparison level")
        if type(self.n_obs) is not int or self.n_obs < 2:
            raise ValueError("comparison level requires at least two observations")
        if not isfinite(self.mean):
            raise ValueError("comparison level mean must be finite")
        if not isfinite(self.standard_deviation) or self.standard_deviation < 0.0:
            raise ValueError(
                "comparison level deviation must be finite and non-negative"
            )
        if self.interval.target != "population_mean":
            raise ValueError("comparison level interval must target population_mean")
        if not self.interval.low <= self.mean <= self.interval.high:
            raise ValueError("comparison level mean must lie within its interval")


@dataclass(frozen=True, slots=True)
class ComparisonTestResult:
    """Welch, paired-t, or repeated-measures omnibus test."""

    name: str
    statistic: float
    df1: float | None
    df2: float
    p_value: float

    def __post_init__(self) -> None:
        supported = {"welch_t", "welch_anova", "paired_t", "repeated_measures_anova"}
        if self.name not in supported:
            raise ValueError("comparison test name is unsupported")
        if not isfinite(self.statistic):
            raise ValueError("comparison statistic must be finite")
        if self.name in {"welch_anova", "repeated_measures_anova"}:
            if self.statistic < 0.0 or self.df1 is None:
                raise ValueError("ANOVA tests require non-negative F and df1")
        elif self.df1 is not None:
            raise ValueError("t tests must not have numerator degrees of freedom")
        if self.df1 is not None and (not isfinite(self.df1) or self.df1 <= 0.0):
            raise ValueError("comparison df1 must be finite and positive")
        if not isfinite(self.df2) or self.df2 <= 0.0:
            raise ValueError("comparison df2 must be finite and positive")
        if not isfinite(self.p_value) or not 0.0 <= self.p_value <= 1.0:
            raise ValueError("comparison p_value must lie within [0, 1]")


@dataclass(frozen=True, slots=True)
class PairwiseComparisonResult:
    """One fully retained pairwise contrast."""

    left: ScalarIdentity
    right: ScalarIdentity
    estimate: float
    standard_error: float
    test: ComparisonTestResult
    interval: IntervalResult
    effect_size: EffectSizeResult
    adjusted_p_value: float
    significant: bool

    def __post_init__(self) -> None:
        _validate_identity(self.left, "left comparison level")
        _validate_identity(self.right, "right comparison level")
        if (type(self.left), self.left) == (type(self.right), self.right):
            raise ValueError("pairwise levels must differ")
        if not isfinite(self.estimate):
            raise ValueError("pairwise estimate must be finite")
        if not isfinite(self.standard_error) or self.standard_error <= 0.0:
            raise ValueError("pairwise standard_error must be finite and positive")
        if self.test.name not in {"welch_t", "paired_t"}:
            raise ValueError("pairwise test must be a supported t test")
        if self.interval.target != "population_mean_difference":
            raise ValueError("pairwise interval target is unsupported")
        if not self.interval.low <= self.estimate <= self.interval.high:
            raise ValueError("pairwise estimate must lie within its interval")
        if not isfinite(self.adjusted_p_value) or not (
            0.0 <= self.adjusted_p_value <= 1.0
        ):
            raise ValueError("adjusted p_value must lie within [0, 1]")


@dataclass(frozen=True, slots=True)
class RepeatedCorrectionResult:
    """Greenhouse–Geisser correction retained beside the primary result."""

    name: str
    epsilon: float
    uncorrected_df1: float
    uncorrected_df2: float
    uncorrected_p_value: float
    corrected_df1: float
    corrected_df2: float
    corrected_p_value: float

    def __post_init__(self) -> None:
        if self.name != "greenhouse_geisser":
            raise ValueError("repeated correction name is unsupported")
        numeric = (
            self.epsilon,
            self.uncorrected_df1,
            self.uncorrected_df2,
            self.uncorrected_p_value,
            self.corrected_df1,
            self.corrected_df2,
            self.corrected_p_value,
        )
        if not all(isfinite(value) for value in numeric):
            raise ValueError("repeated correction values must be finite")
        if not 0.0 < self.epsilon <= 1.0:
            raise ValueError("Greenhouse-Geisser epsilon must lie within (0, 1]")
        if (
            min(
                self.uncorrected_df1,
                self.uncorrected_df2,
                self.corrected_df1,
                self.corrected_df2,
            )
            <= 0.0
        ):
            raise ValueError("repeated correction degrees of freedom must be positive")
        if not 0.0 <= self.uncorrected_p_value <= 1.0 or not (
            0.0 <= self.corrected_p_value <= 1.0
        ):
            raise ValueError("repeated correction probabilities must lie within [0, 1]")


@dataclass(frozen=True, slots=True)
class ComparisonResult:
    """Schema-v1 result for an independent or repeated comparison."""

    schema_version: int
    analysis: str
    design: ComparisonDesign
    x: str
    y: str
    subject_id: str | None
    sample: SampleAudit | RepeatedSampleAudit
    levels: tuple[ComparisonLevelResult, ...]
    omnibus: ComparisonTestResult
    estimate: float | None
    interval: IntervalResult | None
    effect_size: EffectSizeResult
    pairwise: tuple[PairwiseComparisonResult, ...]
    p_adjust: str
    pairwise_alpha: float
    pairwise_display: PairwiseDisplay
    correction: RepeatedCorrectionResult | None
    limits: ResourceLimits
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("comparison schema_version must be 1")
        identities = {
            "ggbetweenstats_welch": "between",
            "ggwithinstats_parametric": "within",
        }
        if identities.get(self.analysis) != self.design:
            raise ValueError("comparison analysis and design are inconsistent")
        if not self.x or not self.y or self.x == self.y:
            raise ValueError("comparison columns must be distinct and non-empty")
        if self.design == "between":
            if self.subject_id is not None or not isinstance(self.sample, SampleAudit):
                raise ValueError("between comparison must not contain subject data")
        elif (
            not self.subject_id
            or self.subject_id in {self.x, self.y}
            or not isinstance(self.sample, RepeatedSampleAudit)
        ):
            raise ValueError("within comparison requires a distinct subject column")
        if not 2 <= len(self.levels) <= 20:
            raise ValueError("comparison requires 2-20 levels")
        level_keys = tuple((type(level.level), level.level) for level in self.levels)
        if len(set(level_keys)) != len(level_keys):
            raise ValueError("comparison levels must be unique")
        if sum(level.n_obs for level in self.levels) != self.sample.analyzed_rows:
            raise ValueError("comparison level counts must match analyzed rows")
        if isinstance(self.sample, RepeatedSampleAudit):
            expected_rows = self.sample.analyzed_subjects * len(self.levels)
            if self.sample.analyzed_rows != expected_rows:
                raise ValueError("repeated rows must form a complete subject block")
            if any(
                level.n_obs != self.sample.analyzed_subjects for level in self.levels
            ):
                raise ValueError("repeated level counts must match analyzed subjects")
        two_level = len(self.levels) == 2
        if two_level != (self.estimate is not None and self.interval is not None):
            raise ValueError("only two-level comparisons have a primary difference")
        if self.estimate is not None and (
            not isfinite(self.estimate)
            or self.interval is None
            or self.interval.target != "population_mean_difference"
            or not self.interval.low <= self.estimate <= self.interval.high
        ):
            raise ValueError("primary comparison estimate and interval are invalid")
        expected_test = {
            ("between", True): "welch_t",
            ("between", False): "welch_anova",
            ("within", True): "paired_t",
            ("within", False): "repeated_measures_anova",
        }[(self.design, two_level)]
        if self.omnibus.name != expected_test:
            raise ValueError("comparison omnibus test is inconsistent")
        expected_pairs = (
            0 if two_level else len(self.levels) * (len(self.levels) - 1) // 2
        )
        if len(self.pairwise) != expected_pairs:
            raise ValueError("comparison pairwise family is incomplete")
        expected_identities = {
            (type(left.level), left.level, type(right.level), right.level)
            for index, left in enumerate(self.levels)
            for right in self.levels[index + 1 :]
        }
        actual_identities = {
            (type(item.left), item.left, type(item.right), item.right)
            for item in self.pairwise
        }
        if actual_identities != (expected_identities if not two_level else set()):
            raise ValueError("comparison pairwise identities are incomplete")
        if self.p_adjust not in {"holm", "none"}:
            raise ValueError("comparison p_adjust is unsupported")
        if not isfinite(self.pairwise_alpha) or not 0.0 < self.pairwise_alpha < 1.0:
            raise ValueError("pairwise_alpha must lie within (0, 1)")
        if self.pairwise_display not in {
            "significant",
            "non-significant",
            "all",
            "none",
        }:
            raise ValueError("pairwise_display is unsupported")
        if any(
            item.significant != (item.adjusted_p_value <= self.pairwise_alpha)
            for item in self.pairwise
        ):
            raise ValueError("pairwise significance must use adjusted p-values")
        if (self.design == "within" and not two_level) != (self.correction is not None):
            raise ValueError("only repeated ANOVA requires a correction record")
        if self.correction is not None:
            if self.omnibus.p_value != self.correction.corrected_p_value:
                raise ValueError("repeated ANOVA must use corrected primary p-value")
            if self.omnibus.df1 != self.correction.corrected_df1:
                raise ValueError("repeated ANOVA primary df1 must be corrected")
            if self.omnibus.df2 != self.correction.corrected_df2:
                raise ValueError("repeated ANOVA primary df2 must be corrected")
        required_limits = (
            self.limits.maximum_levels,
            self.limits.maximum_pairwise_hypotheses,
            self.limits.maximum_rendered_observations,
        )
        if any(limit is None for limit in required_limits):
            raise ValueError("comparison result must retain its resource limits")
        if self.design == "within" and self.limits.maximum_subject_paths is None:
            raise ValueError("within result must retain maximum_subject_paths")
        if any(not warning for warning in self.warnings):
            raise ValueError("comparison warnings must not contain empty strings")

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-serializable representation."""

        return asdict(self)
