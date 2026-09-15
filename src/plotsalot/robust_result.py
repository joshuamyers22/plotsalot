"""Immutable M6A result contracts for approved robust analyses."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import ceil, isclose, isfinite, sqrt
from typing import Any, Literal

from plotsalot.comparison_result import RepeatedSampleAudit
from plotsalot.result import (
    IntervalResult,
    ResourceLimits,
    SampleAudit,
    ScalarIdentity,
)

Alternative = Literal["two-sided", "less", "greater"]
PairwiseDisplay = Literal["significant", "non-significant", "all", "none"]


def _finite(value: float, label: str) -> None:
    if not isfinite(value):
        raise ValueError(f"{label} must be finite")


def _identity(value: ScalarIdentity, label: str) -> None:
    if isinstance(value, str) and not value:
        raise ValueError(f"{label} must be non-empty")
    if isinstance(value, float) and not isfinite(value):
        raise ValueError(f"numeric {label} must be finite")


@dataclass(frozen=True, slots=True)
class RobustMethodResult:
    """Method and software identity shared by M6A result variants."""

    name: str
    version: str
    compatibility: str
    numpy_version: str
    scipy_version: str

    def __post_init__(self) -> None:
        if not all(
            (
                self.name,
                self.version,
                self.numpy_version,
                self.scipy_version,
            )
        ):
            raise ValueError("robust method identity must be complete")
        if self.compatibility != "adapted":
            raise ValueError("M6A robust methods must be classified as adapted")


@dataclass(frozen=True, slots=True)
class TrimmedKernelResult:
    """Auditable fixed-trim location and Winsorized scale calculation."""

    trim_fraction: float
    n: int
    g: int
    h: int
    lower_bound: float
    upper_bound: float
    trimmed_mean: float
    winsorized_variance: float
    q: float

    def __post_init__(self) -> None:
        if self.trim_fraction != 0.20:
            raise ValueError("M6A trim_fraction must equal 0.20")
        if self.n < 5 or self.g != int(self.trim_fraction * self.n):
            raise ValueError("robust kernel n/g are inconsistent")
        if self.h != self.n - (2 * self.g) or self.g < 1 or self.h < 3:
            raise ValueError("robust kernel effective count is invalid")
        for value, label in (
            (self.lower_bound, "lower bound"),
            (self.upper_bound, "upper bound"),
            (self.trimmed_mean, "trimmed mean"),
            (self.winsorized_variance, "Winsorized variance"),
            (self.q, "trimmed-mean variance"),
        ):
            _finite(value, label)
        if self.lower_bound > self.upper_bound:
            raise ValueError("Winsorization bounds must be ordered")
        if self.winsorized_variance <= 0.0 or self.q <= 0.0:
            raise ValueError("robust scale values must be positive")
        expected_q = ((self.n - 1) * self.winsorized_variance) / (self.h * (self.h - 1))
        if not isclose(self.q, expected_q, rel_tol=1e-12, abs_tol=0.0):
            raise ValueError("robust trimmed-mean variance is inconsistent")


@dataclass(frozen=True, slots=True)
class RobustTestResult:
    """Student-t or F reference test with explicit robust target."""

    name: str
    target: str
    null_value: float | None
    alternative: Alternative
    statistic: float | None
    df1: float | None
    df2: float
    p_value: float
    reference_distribution: str

    def __post_init__(self) -> None:
        if not self.name or not self.target:
            raise ValueError("robust test identity must be complete")
        if self.alternative not in {"two-sided", "less", "greater"}:
            raise ValueError("robust test alternative is unsupported")
        if self.statistic is not None:
            _finite(self.statistic, "robust statistic")
        if self.df1 is not None and (not isfinite(self.df1) or self.df1 <= 0.0):
            raise ValueError("robust numerator df must be positive")
        if not isfinite(self.df2) or self.df2 <= 0.0:
            raise ValueError("robust denominator df must be positive")
        if not isfinite(self.p_value) or not 0.0 <= self.p_value <= 1.0:
            raise ValueError("robust p_value must lie within [0, 1]")
        if self.reference_distribution not in {"student_t", "f"}:
            raise ValueError("robust reference distribution is unsupported")
        if self.reference_distribution == "f" and self.df1 is None:
            raise ValueError("F reference requires numerator degrees of freedom")
        if self.reference_distribution == "student_t" and self.df1 is not None:
            raise ValueError("Student-t reference must not have numerator df")

    @property
    def df(self) -> float:
        """Compatibility alias for renderers of Student-t results."""

        return self.df2


@dataclass(frozen=True, slots=True)
class RobustEffectResult:
    """Approved raw robust effect and typed standardized-effect absence."""

    name: str
    value: float | None
    target: str
    standardized_effect_unavailable: str

    def __post_init__(self) -> None:
        if not self.name or not self.target:
            raise ValueError("robust effect identity must be complete")
        if self.value is not None:
            _finite(self.value, "robust effect")
        if self.standardized_effect_unavailable not in {
            "not_approved_for_m6a",
            "robust_standardized_effect_not_approved",
        }:
            raise ValueError("robust standardized-effect absence is unsupported")


@dataclass(frozen=True, slots=True)
class ResamplingResult:
    """Complete deterministic bootstrap and resource provenance."""

    algorithm: str
    bit_generator: str
    root_seed: int
    child_seed: int
    child_identity: str
    requested_replicates: int
    valid_replicates: int
    failed_replicates: int
    quantile_method: str
    calculated_work: int
    maximum_resample_work: int
    hard_maximum_resample_work: int
    batch_index_limit: int

    def __post_init__(self) -> None:
        if self.algorithm != "paired_percentile_bootstrap":
            raise ValueError("robust resampling algorithm is unsupported")
        if self.bit_generator != "PCG64DXSM" or self.quantile_method != "linear_type7":
            raise ValueError("robust RNG or quantile identity is unsupported")
        if not 0 <= self.root_seed <= (2**64) - 1:
            raise ValueError("root seed must be an unsigned 64-bit integer")
        if not 0 <= self.child_seed <= (2**64) - 1 or not self.child_identity:
            raise ValueError("child seed identity is invalid")
        if self.requested_replicates != (
            self.valid_replicates + self.failed_replicates
        ):
            raise ValueError("bootstrap replicate counts must reconcile")
        if (
            not 999 <= self.requested_replicates <= 9_999
            or self.requested_replicates % 2 != 1
            or self.valid_replicates < max(950, ceil(0.99 * self.requested_replicates))
        ):
            raise ValueError("bootstrap replicate counts do not meet M6A policy")
        if (
            self.calculated_work < 1
            or self.calculated_work > self.maximum_resample_work
        ):
            raise ValueError("bootstrap work exceeds its requested ceiling")
        if not (
            self.maximum_resample_work <= self.hard_maximum_resample_work == 500_000_000
        ):
            raise ValueError("bootstrap work ceilings are inconsistent")
        if self.batch_index_limit != 1_000_000:
            raise ValueError("bootstrap batch index limit is unsupported")


@dataclass(frozen=True, slots=True)
class RobustEstimateResult:
    name: str
    value: float
    standard_deviation: float
    kernel: TrimmedKernelResult

    def __post_init__(self) -> None:
        if self.name != "trimmed_mean" or self.value != self.kernel.trimmed_mean:
            raise ValueError("robust estimate must match its trimmed kernel")
        if not isfinite(self.standard_deviation) or self.standard_deviation <= 0.0:
            raise ValueError("robust Winsorized deviation must be positive")
        if not isclose(
            self.standard_deviation**2,
            self.kernel.winsorized_variance,
            rel_tol=1e-12,
            abs_tol=0.0,
        ):
            raise ValueError("robust deviation must match Winsorized variance")


@dataclass(frozen=True, slots=True)
class RobustOneSampleResult:
    schema_version: int
    analysis: str
    mode: str
    column: str
    sample: SampleAudit
    method: RobustMethodResult
    estimate: RobustEstimateResult
    test: RobustTestResult
    interval: IntervalResult
    effect_size: RobustEffectResult
    limits: ResourceLimits
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.schema_version != 2 or self.mode != "robust":
            raise ValueError("robust one-sample result requires schema v2/robust mode")
        if self.analysis not in {
            "gghistostats_one_sample_robust",
            "ggdotplotstats_one_sample_robust",
        }:
            raise ValueError("robust one-sample analysis identity is unsupported")
        if not self.column or self.sample.analyzed_rows != self.estimate.kernel.n:
            raise ValueError("robust one-sample sample identity is inconsistent")
        if self.interval.target != "population_20pct_trimmed_location":
            raise ValueError("robust one-sample interval target is unsupported")
        if not self.interval.low <= self.estimate.value <= self.interval.high:
            raise ValueError("robust estimate must lie within its analytic interval")
        if self.test.null_value is None:
            raise ValueError("robust one-sample test requires a null value")
        if self.effect_size.value is None:
            raise ValueError("robust one-sample result requires a raw effect")
        if self.effect_size.value != self.estimate.value - self.test.null_value:
            raise ValueError("robust raw effect must match estimate minus null")
        if (
            self.test.name != "trimmed_mean_t"
            or self.test.df2 != self.estimate.kernel.h - 1
            or self.test.df1 is not None
        ):
            raise ValueError("robust one-sample test is inconsistent")
        expected_statistic = self.effect_size.value / sqrt(self.estimate.kernel.q)
        if self.test.statistic is None or not isclose(
            self.test.statistic, expected_statistic, rel_tol=1e-12, abs_tol=1e-15
        ):
            raise ValueError("robust one-sample statistic is inconsistent")
        if not isclose(
            self.interval.high - self.estimate.value,
            self.estimate.value - self.interval.low,
            rel_tol=1e-12,
            abs_tol=1e-15,
        ):
            raise ValueError("robust one-sample interval must be symmetric")
        if any(not warning for warning in self.warnings):
            raise ValueError("robust warnings must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RobustDotEstimateResult:
    label: ScalarIdentity
    sample: SampleAudit
    value: float
    standard_deviation: float
    interval: IntervalResult
    kernel: TrimmedKernelResult
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        _identity(self.label, "dot label")
        if (
            self.sample.analyzed_rows != self.kernel.n
            or self.value != self.kernel.trimmed_mean
        ):
            raise ValueError("robust dot estimate must match its kernel")
        if not isfinite(self.standard_deviation) or self.standard_deviation <= 0.0:
            raise ValueError("robust dot deviation must be positive")
        if self.interval.target != "population_20pct_trimmed_location":
            raise ValueError("robust dot interval target is unsupported")
        if not self.interval.low <= self.value <= self.interval.high:
            raise ValueError("robust dot estimate must lie within its interval")


@dataclass(frozen=True, slots=True)
class RobustDotPlotResult:
    schema_version: int
    analysis: str
    mode: str
    x: str
    label_column: str
    sample: SampleAudit
    method: RobustMethodResult
    one_sample: RobustOneSampleResult
    estimates: tuple[RobustDotEstimateResult, ...]
    limits: ResourceLimits
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        if (
            self.schema_version != 2
            or self.analysis != "ggdotplotstats_one_sample_robust"
        ):
            raise ValueError("robust dot plot identity is unsupported")
        if self.mode != "robust" or not self.estimates:
            raise ValueError("robust dot plot requires estimates")
        if self.sample != self.one_sample.sample or self.x != self.one_sample.column:
            raise ValueError("robust dot plot and overall sample must match")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RobustCorrelationResult:
    schema_version: int
    analysis: str
    mode: str
    x: str
    y: str
    sample: SampleAudit
    method: RobustMethodResult
    x_kernel: TrimmedKernelResult
    y_kernel: TrimmedKernelResult
    winsorized_covariance: float
    estimate: float
    test: RobustTestResult
    interval: IntervalResult
    resampling: ResamplingResult
    limits: ResourceLimits
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.schema_version != 2 or self.analysis != "ggscatterstats_winsorized":
            raise ValueError("robust correlation identity is unsupported")
        if self.mode != "robust" or self.x == self.y or not self.x or not self.y:
            raise ValueError("robust correlation columns are invalid")
        if (
            self.sample.analyzed_rows != self.x_kernel.n
            or self.x_kernel.n != self.y_kernel.n
        ):
            raise ValueError("robust correlation kernel counts must match")
        _finite(self.winsorized_covariance, "Winsorized covariance")
        if not isfinite(self.estimate) or not -1.0 <= self.estimate <= 1.0:
            raise ValueError("robust correlation estimate must lie within [-1, 1]")
        if self.interval.target != "population_winsorized_pearson_r":
            raise ValueError("robust correlation interval target is unsupported")
        if self.resampling.calculated_work != (
            self.sample.analyzed_rows * self.resampling.requested_replicates
        ):
            raise ValueError("robust correlation work is inconsistent")
        expected = self.winsorized_covariance / sqrt(
            self.x_kernel.winsorized_variance * self.y_kernel.winsorized_variance
        )
        if not isclose(self.estimate, expected, rel_tol=1e-12, abs_tol=1e-15):
            raise ValueError("robust correlation estimate is inconsistent")
        if (
            self.test.name != "winsorized_correlation_t"
            or self.test.df2 != self.x_kernel.h - 2
            or self.test.alternative != "two-sided"
        ):
            raise ValueError("robust correlation test is inconsistent")
        if not -1.0 <= self.interval.low <= self.interval.high <= 1.0:
            raise ValueError("robust correlation interval is outside [-1, 1]")
        perfect = abs(self.estimate) == 1.0
        if perfect != (self.test.statistic is None and self.test.p_value == 0.0):
            raise ValueError("perfect robust correlation handling is inconsistent")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RobustCorrelationMatrixCell:
    x: str
    y: str
    n_obs: int
    estimate: float
    interval: IntervalResult | None
    statistic: float | None
    df: float | None
    p_value: float | None
    adjusted_p_value: float | None
    significant: bool | None
    x_kernel: TrimmedKernelResult | None
    y_kernel: TrimmedKernelResult | None
    winsorized_covariance: float | None
    resampling: ResamplingResult | None

    def __post_init__(self) -> None:
        if not self.x or not self.y or self.n_obs < 1:
            raise ValueError("robust matrix cell identity is invalid")
        if not isfinite(self.estimate) or not -1.0 <= self.estimate <= 1.0:
            raise ValueError("robust matrix estimate must lie within [-1, 1]")
        diagonal = self.x == self.y
        optional = (
            self.interval,
            self.statistic,
            self.df,
            self.p_value,
            self.adjusted_p_value,
            self.significant,
            self.x_kernel,
            self.y_kernel,
            self.winsorized_covariance,
            self.resampling,
        )
        if diagonal:
            if self.estimate != 1.0 or any(value is not None for value in optional):
                raise ValueError("robust matrix diagonal must be structural")
            return
        required = (
            self.interval,
            self.df,
            self.p_value,
            self.adjusted_p_value,
            self.significant,
            self.x_kernel,
            self.y_kernel,
            self.winsorized_covariance,
            self.resampling,
        )
        if any(value is None for value in required):
            raise ValueError("robust off-diagonal cells require complete inference")
        if self.x_kernel is not None and self.x_kernel.n != self.n_obs:
            raise ValueError("robust matrix x kernel count is inconsistent")
        if self.y_kernel is not None and self.y_kernel.n != self.n_obs:
            raise ValueError("robust matrix y kernel count is inconsistent")
        if self.resampling is not None and self.resampling.calculated_work != (
            self.n_obs * self.resampling.requested_replicates
        ):
            raise ValueError("robust matrix cell work is inconsistent")


@dataclass(frozen=True, slots=True)
class RobustCorrelationMatrixResult:
    schema_version: int
    analysis: str
    mode: str
    columns: tuple[str, ...]
    method: RobustMethodResult
    p_adjust: str
    sig_level: float
    cells: tuple[RobustCorrelationMatrixCell, ...]
    limits: ResourceLimits
    maximum_resample_work: int
    calculated_resample_work: int
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.schema_version != 2 or self.analysis != "ggcorrmat_winsorized":
            raise ValueError("robust matrix identity is unsupported")
        if self.mode != "robust" or not 2 <= len(self.columns) <= 50:
            raise ValueError("robust matrix columns are invalid")
        if len(set(self.columns)) != len(self.columns):
            raise ValueError("robust matrix columns must be unique")
        if len(self.cells) != len(self.columns) ** 2:
            raise ValueError("robust matrix must contain every ordered cell")
        if self.p_adjust not in {"holm", "none"}:
            raise ValueError("robust matrix p adjustment is unsupported")
        if not isfinite(self.sig_level) or not 0.0 < self.sig_level < 1.0:
            raise ValueError("robust matrix significance level is invalid")
        if self.calculated_resample_work > self.maximum_resample_work:
            raise ValueError("robust matrix resample work exceeds its limit")
        by_identity = {(cell.x, cell.y): cell for cell in self.cells}
        expected = {(x, y) for x in self.columns for y in self.columns}
        if set(by_identity) != expected:
            raise ValueError("robust matrix cell identities are incomplete")
        unique_work = 0
        for left_index, x in enumerate(self.columns):
            for y in self.columns[left_index + 1 :]:
                cell = by_identity[(x, y)]
                mirror = by_identity[(y, x)]
                if (
                    cell.n_obs,
                    cell.estimate,
                    cell.interval,
                    cell.statistic,
                    cell.df,
                    cell.p_value,
                    cell.adjusted_p_value,
                    cell.significant,
                    cell.winsorized_covariance,
                    cell.resampling,
                ) != (
                    mirror.n_obs,
                    mirror.estimate,
                    mirror.interval,
                    mirror.statistic,
                    mirror.df,
                    mirror.p_value,
                    mirror.adjusted_p_value,
                    mirror.significant,
                    mirror.winsorized_covariance,
                    mirror.resampling,
                ):
                    raise ValueError("robust matrix cells must be symmetric")
                if cell.x_kernel != mirror.y_kernel or cell.y_kernel != mirror.x_kernel:
                    raise ValueError("robust matrix mirrored kernels must be swapped")
                if cell.resampling is None:
                    raise ValueError("robust matrix pair requires resampling metadata")
                unique_work += cell.resampling.calculated_work
        if unique_work != self.calculated_resample_work:
            raise ValueError("robust matrix total resample work is inconsistent")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RobustComparisonLevelResult:
    level: ScalarIdentity
    n_obs: int
    mean: float
    standard_deviation: float
    interval: IntervalResult
    kernel: TrimmedKernelResult

    def __post_init__(self) -> None:
        _identity(self.level, "robust comparison level")
        if self.n_obs != self.kernel.n or self.mean != self.kernel.trimmed_mean:
            raise ValueError("robust level must match its kernel")
        if not isfinite(self.standard_deviation) or self.standard_deviation <= 0.0:
            raise ValueError("robust level deviation must be positive")
        if not isclose(
            self.standard_deviation**2,
            self.kernel.winsorized_variance,
            rel_tol=1e-12,
            abs_tol=0.0,
        ):
            raise ValueError("robust level deviation is inconsistent")
        if self.interval.target != "population_20pct_trimmed_location":
            raise ValueError("robust level interval target is unsupported")
        if not self.interval.low <= self.mean <= self.interval.high:
            raise ValueError("robust level estimate must lie within its interval")


@dataclass(frozen=True, slots=True)
class RobustPairwiseComparisonResult:
    left: ScalarIdentity
    right: ScalarIdentity
    estimate: float
    standard_error: float
    test: RobustTestResult
    interval: IntervalResult
    effect_size: RobustEffectResult
    adjusted_p_value: float
    significant: bool
    left_kernel: TrimmedKernelResult | None
    right_kernel: TrimmedKernelResult | None
    difference_kernel: TrimmedKernelResult | None

    def __post_init__(self) -> None:
        _identity(self.left, "left robust comparison level")
        _identity(self.right, "right robust comparison level")
        if (type(self.left), self.left) == (type(self.right), self.right):
            raise ValueError("robust pairwise levels must differ")
        _finite(self.estimate, "robust pairwise estimate")
        if not isfinite(self.standard_error) or self.standard_error <= 0.0:
            raise ValueError("robust pairwise standard error must be positive")
        if not self.interval.low <= self.estimate <= self.interval.high:
            raise ValueError("robust pairwise estimate must lie within its interval")
        if self.effect_size.value != self.estimate:
            raise ValueError("robust pairwise raw effect must match its estimate")
        independent = self.test.name == "yuen_t"
        if independent != (
            self.left_kernel is not None
            and self.right_kernel is not None
            and self.difference_kernel is None
        ):
            raise ValueError("robust pairwise kernel provenance is inconsistent")
        repeated = self.test.name == "trimmed_subject_difference_t"
        if repeated != (
            self.left_kernel is None
            and self.right_kernel is None
            and self.difference_kernel is not None
        ):
            raise ValueError("robust pairwise difference provenance is inconsistent")
        if independent:
            if self.left_kernel is None or self.right_kernel is None:
                raise ValueError("Yuen contrast requires two kernels")
            expected_estimate = (
                self.left_kernel.trimmed_mean - self.right_kernel.trimmed_mean
            )
            expected_se = sqrt(self.left_kernel.q + self.right_kernel.q)
            expected_df = ((self.left_kernel.q + self.right_kernel.q) ** 2) / (
                (self.left_kernel.q**2 / (self.left_kernel.h - 1))
                + (self.right_kernel.q**2 / (self.right_kernel.h - 1))
            )
        else:
            if self.difference_kernel is None:
                raise ValueError("repeated contrast requires a difference kernel")
            expected_estimate = self.difference_kernel.trimmed_mean
            expected_se = sqrt(self.difference_kernel.q)
            expected_df = float(self.difference_kernel.h - 1)
        if not isclose(self.estimate, expected_estimate, rel_tol=1e-12, abs_tol=1e-15):
            raise ValueError("robust pairwise estimate is inconsistent")
        if not isclose(self.standard_error, expected_se, rel_tol=1e-12, abs_tol=1e-15):
            raise ValueError("robust pairwise standard error is inconsistent")
        if self.test.statistic is None or not isclose(
            self.test.statistic,
            self.estimate / self.standard_error,
            rel_tol=1e-12,
            abs_tol=1e-15,
        ):
            raise ValueError("robust pairwise statistic is inconsistent")
        if not isclose(self.test.df2, expected_df, rel_tol=1e-12, abs_tol=1e-15):
            raise ValueError("robust pairwise degrees of freedom are inconsistent")
        if not isfinite(self.adjusted_p_value) or not (
            0.0 <= self.adjusted_p_value <= 1.0
        ):
            raise ValueError("robust adjusted p_value must lie within [0, 1]")


@dataclass(frozen=True, slots=True)
class RobustRepeatedCorrectionResult:
    name: str
    epsilon: float
    uncorrected_df1: float
    uncorrected_df2: float
    corrected_df1: float
    corrected_df2: float
    corrected_p_value: float
    covariance_a: float
    covariance_b: float
    epsilon_hat: float
    epsilon_raw: float
    qc: float
    qe: float

    def __post_init__(self) -> None:
        if self.name != "wrs2_winsorized_epsilon":
            raise ValueError("robust repeated correction identity is unsupported")
        numeric = (
            self.epsilon,
            self.uncorrected_df1,
            self.uncorrected_df2,
            self.corrected_df1,
            self.corrected_df2,
            self.corrected_p_value,
            self.covariance_a,
            self.covariance_b,
            self.epsilon_hat,
            self.epsilon_raw,
            self.qc,
            self.qe,
        )
        if not all(isfinite(value) for value in numeric):
            raise ValueError("robust repeated correction values must be finite")
        if not 0.0 < self.epsilon <= 1.0 or self.qe <= 0.0:
            raise ValueError("robust repeated correction is invalid")
        if not 0.0 <= self.corrected_p_value <= 1.0:
            raise ValueError("robust repeated p_value must lie within [0, 1]")
        if not isclose(
            self.corrected_df1,
            self.uncorrected_df1 * self.epsilon,
            rel_tol=1e-12,
        ) or not isclose(
            self.corrected_df2,
            self.uncorrected_df2 * self.epsilon,
            rel_tol=1e-12,
        ):
            raise ValueError("robust repeated corrected degrees of freedom mismatch")


@dataclass(frozen=True, slots=True)
class RobustComparisonResult:
    schema_version: int
    analysis: str
    mode: str
    design: Literal["between", "within"]
    x: str
    y: str
    subject_id: str | None
    sample: SampleAudit | RepeatedSampleAudit
    method: RobustMethodResult
    levels: tuple[RobustComparisonLevelResult, ...]
    omnibus: RobustTestResult
    estimate: float | None
    interval: IntervalResult | None
    effect_size: RobustEffectResult
    pairwise: tuple[RobustPairwiseComparisonResult, ...]
    p_adjust: str
    pairwise_alpha: float
    pairwise_display: PairwiseDisplay
    correction: RobustRepeatedCorrectionResult | None
    limits: ResourceLimits
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        identities = {
            "ggbetweenstats_robust": "between",
            "ggwithinstats_robust": "within",
        }
        if self.schema_version != 2 or self.mode != "robust":
            raise ValueError("robust comparison requires schema v2/robust mode")
        if identities.get(self.analysis) != self.design:
            raise ValueError("robust comparison identity is inconsistent")
        if not 2 <= len(self.levels) <= 20:
            raise ValueError("robust comparison requires 2-20 levels")
        if self.design == "between" and not isinstance(self.sample, SampleAudit):
            raise ValueError("robust between comparison requires a row audit")
        if self.design == "within" and not isinstance(self.sample, RepeatedSampleAudit):
            raise ValueError("robust within comparison requires a subject audit")
        if self.design == "between" and self.subject_id is not None:
            raise ValueError("robust between comparison cannot retain a subject column")
        if self.design == "within" and (
            not self.subject_id or self.subject_id in {self.x, self.y}
        ):
            raise ValueError("robust within comparison requires a subject column")
        two_level = len(self.levels) == 2
        if sum(level.n_obs for level in self.levels) != self.sample.analyzed_rows:
            raise ValueError("robust comparison level counts must match the sample")
        if two_level != (self.estimate is not None and self.interval is not None):
            raise ValueError(
                "only two-level robust comparisons have a primary estimate"
            )
        if two_level and self.effect_size.value != self.estimate:
            raise ValueError("robust primary raw effect is inconsistent")
        if not two_level and self.effect_size.value is not None:
            raise ValueError("robust omnibus cannot report one raw difference")
        expected_pairs = (
            0 if two_level else len(self.levels) * (len(self.levels) - 1) // 2
        )
        if len(self.pairwise) != expected_pairs:
            raise ValueError("robust pairwise family is incomplete")
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
            raise ValueError("robust pairwise identities are incomplete")
        if any(
            item.significant != (item.adjusted_p_value <= self.pairwise_alpha)
            for item in self.pairwise
        ):
            raise ValueError("robust pairwise significance is inconsistent")
        if (self.design == "within" and not two_level) != (self.correction is not None):
            raise ValueError("robust repeated omnibus correction is inconsistent")
        if self.correction is not None and (
            self.omnibus.df1 != self.correction.corrected_df1
            or self.omnibus.df2 != self.correction.corrected_df2
            or self.omnibus.p_value != self.correction.corrected_p_value
        ):
            raise ValueError("robust repeated primary test and correction differ")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
