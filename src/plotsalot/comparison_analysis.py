"""Approved classical between- and within-group comparison analyses."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from math import exp, isclose, log, sqrt
from typing import Protocol, cast

import numpy as np
import polars as pl
from numpy.typing import NDArray

from plotsalot.comparison_data import (
    ComparisonSample,
    RepeatedSample,
    select_comparison_sample,
    select_repeated_sample,
)
from plotsalot.comparison_result import (
    ComparisonLevelResult,
    ComparisonResult,
    ComparisonTestResult,
    PairwiseComparisonResult,
    PairwiseDisplay,
    RepeatedCorrectionResult,
)
from plotsalot.data import DEFAULT_MAX_ROWS, FloatArray
from plotsalot.result import EffectSizeResult, IntervalResult, ResourceLimits
from plotsalot.robust import TRIM_FRACTION, method_result, trimmed_kernel
from plotsalot.robust_result import (
    Alternative as RobustAlternative,
)
from plotsalot.robust_result import (
    RobustComparisonLevelResult,
    RobustComparisonResult,
    RobustEffectResult,
    RobustPairwiseComparisonResult,
    RobustRepeatedCorrectionResult,
    RobustTestResult,
)

DEFAULT_MAX_LEVELS = 20
DEFAULT_MAX_RENDERED_OBSERVATIONS = 1_000_000
DEFAULT_MAX_SUBJECT_PATHS = 10_000


class _ContinuousDistribution(Protocol):
    def ppf(self, probability: float, *parameters: float) -> float: ...

    def sf(self, value: float, *parameters: float) -> float: ...


class _FResult(Protocol):
    statistic: float
    pvalue: float


class _ScipyStats(Protocol):
    t: _ContinuousDistribution
    f: _ContinuousDistribution

    def f_oneway(self, *samples: FloatArray, equal_var: bool) -> _FResult: ...


class _ScipySpecial(Protocol):
    def gammaln(self, value: float) -> float: ...


class _StatsmodelsMultitest(Protocol):
    def multipletests(
        self, pvals: list[float], *, method: str
    ) -> tuple[np.ndarray, np.ndarray, float, float]: ...


scipy_stats = cast(_ScipyStats, import_module("scipy.stats"))
scipy_special = cast(_ScipySpecial, import_module("scipy.special"))
statsmodels_multitest = cast(
    _StatsmodelsMultitest, import_module("statsmodels.stats.multitest")
)


@dataclass(frozen=True, slots=True)
class ComparisonAnalysis:
    """A typed comparison result and the exact owned sample used to compute it."""

    sample: ComparisonSample | RepeatedSample
    result: ComparisonResult

    def __post_init__(self) -> None:
        if (self.sample.x, self.sample.y) != (self.result.x, self.result.y):
            raise ValueError("comparison sample and result columns must match")
        sample_levels = (
            self.sample.levels
            if isinstance(self.sample, ComparisonSample)
            else self.sample.conditions
        )
        result_levels = tuple(level.level for level in self.result.levels)
        if sample_levels != result_levels:
            raise ValueError("comparison sample and result levels must match")
        if self.sample.audit != self.result.sample:
            raise ValueError("comparison sample and result audits must match")


@dataclass(frozen=True, slots=True)
class _Contrast:
    estimate: float
    standard_error: float
    test: ComparisonTestResult
    interval: IntervalResult
    effect_size: EffectSizeResult


def _validate_options(
    *,
    method_type: str,
    alternative: str,
    conf_level: float,
    p_adjust: str,
    pairwise_alpha: float,
    pairwise_display: str,
    maximum_levels: int,
    maximum_rendered_observations: int,
) -> PairwiseDisplay:
    if method_type not in {"parametric", "robust"}:
        raise ValueError("type must be 'parametric' or 'robust'")
    if alternative not in {"two-sided", "less", "greater"}:
        raise ValueError("alternative must be 'two-sided', 'less', or 'greater'")
    if method_type == "parametric" and alternative != "two-sided":
        raise ValueError("parametric comparison alternative must be 'two-sided'")
    if not np.isfinite(conf_level) or not 0.0 < conf_level < 1.0:
        raise ValueError("conf_level must be strictly between 0 and 1")
    if p_adjust not in {"holm", "none"}:
        raise ValueError("p_adjust must be 'holm' or 'none'")
    if not np.isfinite(pairwise_alpha) or not 0.0 < pairwise_alpha < 1.0:
        raise ValueError("pairwise_alpha must be strictly between 0 and 1")
    supported_display = {"significant", "non-significant", "all", "none"}
    if pairwise_display not in supported_display:
        raise ValueError(
            "pairwise_display must be 'significant', 'non-significant', "
            "'all', or 'none'"
        )
    if type(maximum_levels) is not int or not 2 <= maximum_levels <= 20:
        raise ValueError("maximum_levels must be an integer between 2 and 20")
    if (
        type(maximum_rendered_observations) is not int
        or maximum_rendered_observations < 1
    ):
        raise ValueError("maximum_rendered_observations must be a positive integer")
    return cast(PairwiseDisplay, pairwise_display)


def _mean_interval(values: FloatArray, conf_level: float) -> IntervalResult:
    mean = float(np.mean(values))
    deviation = float(np.std(values, ddof=1))
    critical = float(
        scipy_stats.t.ppf(0.5 + (conf_level / 2.0), float(values.size - 1))
    )
    margin = critical * deviation / sqrt(values.size)
    return IntervalResult(
        target="population_mean",
        method="student_t_two_sided",
        level=conf_level,
        low=mean - margin,
        high=mean + margin,
    )


def _level_results(
    levels: tuple[object, ...],
    values: tuple[FloatArray, ...],
    conf_level: float,
) -> tuple[ComparisonLevelResult, ...]:
    return tuple(
        ComparisonLevelResult(
            level=cast(str | int | float | bool, level),
            n_obs=int(level_values.size),
            mean=float(np.mean(level_values)),
            standard_deviation=float(np.std(level_values, ddof=1)),
            interval=_mean_interval(level_values, conf_level),
        )
        for level, level_values in zip(levels, values, strict=True)
    )


def _hedges_correction(df: float) -> float:
    return exp(
        float(scipy_special.gammaln(df / 2.0))
        - (0.5 * log(df / 2.0))
        - float(scipy_special.gammaln((df - 1.0) / 2.0))
    )


def _welch_contrast(
    left: FloatArray,
    right: FloatArray,
    conf_level: float,
) -> _Contrast:
    left_mean = float(np.mean(left))
    right_mean = float(np.mean(right))
    left_variance = float(np.var(left, ddof=1))
    right_variance = float(np.var(right, ddof=1))
    left_component = left_variance / left.size
    right_component = right_variance / right.size
    standard_error = sqrt(left_component + right_component)
    estimate = left_mean - right_mean
    statistic = estimate / standard_error
    df = ((left_component + right_component) ** 2) / (
        (left_component**2 / (left.size - 1)) + (right_component**2 / (right.size - 1))
    )
    p_value = min(1.0, 2.0 * float(scipy_stats.t.sf(abs(statistic), df)))
    critical = float(scipy_stats.t.ppf(0.5 + (conf_level / 2.0), df))
    margin = critical * standard_error
    standardizer = sqrt((left_variance + right_variance) / 2.0)
    correction_df = float(left.size + right.size - 2)
    effect = (estimate / standardizer) * _hedges_correction(correction_df)
    return _Contrast(
        estimate=estimate,
        standard_error=standard_error,
        test=ComparisonTestResult(
            name="welch_t",
            statistic=statistic,
            df1=None,
            df2=df,
            p_value=p_value,
        ),
        interval=IntervalResult(
            target="population_mean_difference",
            method="welch_satterthwaite_two_sided",
            level=conf_level,
            low=estimate - margin,
            high=estimate + margin,
        ),
        effect_size=EffectSizeResult(
            name="hedges_g",
            value=effect,
            standardizer="unpooled_root_mean_square_sd",
        ),
    )


def _paired_contrast(
    left: FloatArray,
    right: FloatArray,
    conf_level: float,
) -> _Contrast:
    differences = left - right
    estimate = float(np.mean(differences))
    deviation = float(np.std(differences, ddof=1))
    if deviation <= 0.0:
        raise ValueError("paired differences require positive sample variation")
    df = float(differences.size - 1)
    standard_error = deviation / sqrt(differences.size)
    statistic = estimate / standard_error
    p_value = min(1.0, 2.0 * float(scipy_stats.t.sf(abs(statistic), df)))
    critical = float(scipy_stats.t.ppf(0.5 + (conf_level / 2.0), df))
    margin = critical * standard_error
    effect = (estimate / deviation) * _hedges_correction(df)
    return _Contrast(
        estimate=estimate,
        standard_error=standard_error,
        test=ComparisonTestResult(
            name="paired_t",
            statistic=statistic,
            df1=None,
            df2=df,
            p_value=p_value,
        ),
        interval=IntervalResult(
            target="population_mean_difference",
            method="paired_student_t_two_sided",
            level=conf_level,
            low=estimate - margin,
            high=estimate + margin,
        ),
        effect_size=EffectSizeResult(
            name="hedges_g_z",
            value=effect,
            standardizer="paired_difference_sd",
        ),
    )


def _holm_adjust(p_values: list[float]) -> list[float]:
    order = sorted(range(len(p_values)), key=p_values.__getitem__)
    adjusted = [0.0] * len(p_values)
    running = 0.0
    total = len(p_values)
    for rank, index in enumerate(order):
        running = max(running, (total - rank) * p_values[index])
        adjusted[index] = min(1.0, running)
    return adjusted


def _adjust_p_values(p_values: list[float], p_adjust: str) -> list[float]:
    if p_adjust == "none":
        return list(p_values)
    adjusted = [
        float(value)
        for value in statsmodels_multitest.multipletests(p_values, method="holm")[1]
    ]
    independent = _holm_adjust(p_values)
    if not all(
        isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-15)
        for actual, expected in zip(adjusted, independent, strict=True)
    ):
        raise RuntimeError("Holm adjustment failed its independent cross-check")
    return adjusted


def _pairwise_results(
    levels: tuple[object, ...],
    values: tuple[FloatArray, ...],
    *,
    design: str,
    conf_level: float,
    p_adjust: str,
    pairwise_alpha: float,
) -> tuple[PairwiseComparisonResult, ...]:
    raw: list[tuple[object, object, _Contrast]] = []
    for index, left_level in enumerate(levels):
        for right_index in range(index + 1, len(levels)):
            contrast = (
                _welch_contrast(values[index], values[right_index], conf_level)
                if design == "between"
                else _paired_contrast(values[index], values[right_index], conf_level)
            )
            raw.append((left_level, levels[right_index], contrast))
    adjusted = _adjust_p_values(
        [contrast.test.p_value for _, _, contrast in raw], p_adjust
    )
    return tuple(
        PairwiseComparisonResult(
            left=cast(str | int | float | bool, left),
            right=cast(str | int | float | bool, right),
            estimate=contrast.estimate,
            standard_error=contrast.standard_error,
            test=contrast.test,
            interval=contrast.interval,
            effect_size=contrast.effect_size,
            adjusted_p_value=adjusted_p,
            significant=adjusted_p <= pairwise_alpha,
        )
        for (left, right, contrast), adjusted_p in zip(raw, adjusted, strict=True)
    )


def _welch_anova(values: tuple[FloatArray, ...]) -> ComparisonTestResult:
    sizes = np.asarray([values_.size for values_ in values], dtype=np.float64)
    means = np.asarray([np.mean(values_) for values_ in values], dtype=np.float64)
    variances = np.asarray(
        [np.var(values_, ddof=1) for values_ in values], dtype=np.float64
    )
    weights = sizes / variances
    weight_sum = float(np.sum(weights))
    weighted_mean = float(np.sum(weights * means) / weight_sum)
    adjustment = float(np.sum(((1.0 - (weights / weight_sum)) ** 2) / (sizes - 1.0)))
    groups = len(values)
    statistic = float(
        (np.sum(weights * ((means - weighted_mean) ** 2)) / (groups - 1.0))
        / (1.0 + (2.0 * (groups - 2.0) * adjustment / ((groups**2) - 1.0)))
    )
    df1 = float(groups - 1)
    df2 = float(((groups**2) - 1.0) / (3.0 * adjustment))
    p_value = float(scipy_stats.f.sf(statistic, df1, df2))
    reference = scipy_stats.f_oneway(*values, equal_var=False)
    if not isclose(statistic, float(reference.statistic), rel_tol=1e-12, abs_tol=1e-12):
        raise RuntimeError("Welch ANOVA failed its SciPy cross-check")
    if not isclose(p_value, float(reference.pvalue), rel_tol=1e-12, abs_tol=1e-15):
        raise RuntimeError("Welch ANOVA probability failed its SciPy cross-check")
    return ComparisonTestResult(
        name="welch_anova",
        statistic=statistic,
        df1=df1,
        df2=df2,
        p_value=p_value,
    )


def _omega_from_f(statistic: float, df1: float, df2: float) -> float:
    return max(0.0, (df1 * (statistic - 1.0)) / ((df1 * statistic) + df2 + 1.0))


def _robust_probability(statistic: float, df: float, alternative: str) -> float:
    if alternative == "two-sided":
        return min(1.0, 2.0 * float(scipy_stats.t.sf(abs(statistic), df)))
    if alternative == "greater":
        return float(scipy_stats.t.sf(statistic, df))
    return float(1.0 - scipy_stats.t.sf(statistic, df))


def _robust_interval(
    estimate: float,
    standard_error: float,
    df: float,
    conf_level: float,
    *,
    target: str,
    method: str,
) -> IntervalResult:
    critical = float(scipy_stats.t.ppf(0.5 + (conf_level / 2.0), df))
    margin = critical * standard_error
    return IntervalResult(
        target=target,
        method=method,
        level=conf_level,
        low=estimate - margin,
        high=estimate + margin,
    )


def _robust_levels(
    levels: tuple[object, ...],
    values: tuple[FloatArray, ...],
    conf_level: float,
) -> tuple[RobustComparisonLevelResult, ...]:
    results: list[RobustComparisonLevelResult] = []
    for level, level_values in zip(levels, values, strict=True):
        kernel, _ = trimmed_kernel(level_values)
        interval = _robust_interval(
            kernel.trimmed_mean,
            sqrt(kernel.q),
            float(kernel.h - 1),
            conf_level,
            target="population_20pct_trimmed_location",
            method="trimmed_mean_student_t_two_sided",
        )
        results.append(
            RobustComparisonLevelResult(
                level=cast(str | int | float | bool, level),
                n_obs=kernel.n,
                mean=kernel.trimmed_mean,
                standard_deviation=sqrt(kernel.winsorized_variance),
                interval=interval,
                kernel=kernel,
            )
        )
    return tuple(results)


def _yuen_contrast(
    left: FloatArray,
    right: FloatArray,
    conf_level: float,
    alternative: str,
) -> RobustPairwiseComparisonResult:
    left_kernel, _ = trimmed_kernel(left)
    right_kernel, _ = trimmed_kernel(right)
    estimate = left_kernel.trimmed_mean - right_kernel.trimmed_mean
    standard_error = sqrt(left_kernel.q + right_kernel.q)
    df = ((left_kernel.q + right_kernel.q) ** 2) / (
        (left_kernel.q**2 / (left_kernel.h - 1))
        + (right_kernel.q**2 / (right_kernel.h - 1))
    )
    statistic = estimate / standard_error
    return RobustPairwiseComparisonResult(
        left="__left__",
        right="__right__",
        estimate=estimate,
        standard_error=standard_error,
        test=RobustTestResult(
            name="yuen_t",
            target="population_20pct_trimmed_location_difference",
            null_value=0.0,
            alternative=cast(RobustAlternative, alternative),
            statistic=statistic,
            df1=None,
            df2=df,
            p_value=_robust_probability(statistic, df, alternative),
            reference_distribution="student_t",
        ),
        interval=_robust_interval(
            estimate,
            standard_error,
            df,
            conf_level,
            target="population_20pct_trimmed_location_difference",
            method="yuen_satterthwaite_two_sided_pointwise",
        ),
        effect_size=RobustEffectResult(
            name="raw_trimmed_location_difference",
            value=estimate,
            target="population_20pct_trimmed_location_difference",
            standardized_effect_unavailable="robust_standardized_effect_not_approved",
        ),
        adjusted_p_value=0.0,
        significant=False,
        left_kernel=left_kernel,
        right_kernel=right_kernel,
        difference_kernel=None,
    )


def _trimmed_difference_contrast(
    left: FloatArray,
    right: FloatArray,
    conf_level: float,
    alternative: str,
) -> RobustPairwiseComparisonResult:
    kernel, _ = trimmed_kernel(left - right)
    standard_error = sqrt(kernel.q)
    df = float(kernel.h - 1)
    statistic = kernel.trimmed_mean / standard_error
    return RobustPairwiseComparisonResult(
        left="__left__",
        right="__right__",
        estimate=kernel.trimmed_mean,
        standard_error=standard_error,
        test=RobustTestResult(
            name="trimmed_subject_difference_t",
            target="population_20pct_trimmed_subject_difference",
            null_value=0.0,
            alternative=cast(RobustAlternative, alternative),
            statistic=statistic,
            df1=None,
            df2=df,
            p_value=_robust_probability(statistic, df, alternative),
            reference_distribution="student_t",
        ),
        interval=_robust_interval(
            kernel.trimmed_mean,
            standard_error,
            df,
            conf_level,
            target="population_20pct_trimmed_location_difference",
            method="trimmed_subject_difference_t_two_sided_pointwise",
        ),
        effect_size=RobustEffectResult(
            name="raw_trimmed_location_difference",
            value=kernel.trimmed_mean,
            target="population_20pct_trimmed_subject_difference",
            standardized_effect_unavailable="robust_standardized_effect_not_approved",
        ),
        adjusted_p_value=0.0,
        significant=False,
        left_kernel=None,
        right_kernel=None,
        difference_kernel=kernel,
    )


def _named_robust_contrast(
    contrast: RobustPairwiseComparisonResult,
    left: object,
    right: object,
    *,
    adjusted_p_value: float,
    alpha: float,
) -> RobustPairwiseComparisonResult:
    return RobustPairwiseComparisonResult(
        left=cast(str | int | float | bool, left),
        right=cast(str | int | float | bool, right),
        estimate=contrast.estimate,
        standard_error=contrast.standard_error,
        test=contrast.test,
        interval=contrast.interval,
        effect_size=contrast.effect_size,
        adjusted_p_value=adjusted_p_value,
        significant=adjusted_p_value <= alpha,
        left_kernel=contrast.left_kernel,
        right_kernel=contrast.right_kernel,
        difference_kernel=contrast.difference_kernel,
    )


def _robust_pairwise(
    levels: tuple[object, ...],
    values: tuple[FloatArray, ...],
    *,
    design: str,
    conf_level: float,
    p_adjust: str,
    alpha: float,
) -> tuple[RobustPairwiseComparisonResult, ...]:
    raw: list[tuple[object, object, RobustPairwiseComparisonResult]] = []
    for index, left in enumerate(levels):
        for right_index in range(index + 1, len(levels)):
            contrast = (
                _yuen_contrast(
                    values[index], values[right_index], conf_level, "two-sided"
                )
                if design == "between"
                else _trimmed_difference_contrast(
                    values[index], values[right_index], conf_level, "two-sided"
                )
            )
            raw.append((left, levels[right_index], contrast))
    adjusted = _adjust_p_values(
        [contrast.test.p_value for _, _, contrast in raw], p_adjust
    )
    return tuple(
        _named_robust_contrast(
            contrast,
            left,
            right,
            adjusted_p_value=adjusted_p,
            alpha=alpha,
        )
        for (left, right, contrast), adjusted_p in zip(raw, adjusted, strict=True)
    )


def _welch_yuen(values: tuple[FloatArray, ...]) -> RobustTestResult:
    kernels = tuple(trimmed_kernel(item)[0] for item in values)
    weights = np.asarray([1.0 / kernel.q for kernel in kernels], dtype=np.float64)
    locations = np.asarray(
        [kernel.trimmed_mean for kernel in kernels], dtype=np.float64
    )
    total_weight = float(np.sum(weights))
    weighted_location = float(np.sum(weights * locations) / total_weight)
    groups = len(kernels)
    a_value = float(
        np.sum(weights * ((locations - weighted_location) ** 2)) / (groups - 1)
    )
    c_value = float(
        np.sum(
            ((1.0 - (weights / total_weight)) ** 2)
            / np.asarray([kernel.h - 1 for kernel in kernels], dtype=np.float64)
        )
        / ((groups**2) - 1)
    )
    denominator = 1.0 + (2.0 * (groups - 2) * c_value)
    if c_value <= 0.0 or denominator <= 0.0:
        raise ValueError("Welch-Yuen omnibus denominator is invalid")
    statistic = a_value / denominator
    df1 = float(groups - 1)
    df2 = 1.0 / (3.0 * c_value)
    return RobustTestResult(
        name="welch_yuen_anova",
        target="equal_population_20pct_trimmed_locations",
        null_value=None,
        alternative="two-sided",
        statistic=statistic,
        df1=df1,
        df2=df2,
        p_value=float(scipy_stats.f.sf(statistic, df1, df2)),
        reference_distribution="f",
    )


def _robust_repeated(
    values: NDArray[np.float64],
) -> tuple[RobustTestResult, RobustRepeatedCorrectionResult]:
    subjects, conditions = values.shape
    kernels_and_values = tuple(
        trimmed_kernel(values[:, index]) for index in range(conditions)
    )
    kernels = tuple(item[0] for item in kernels_and_values)
    winsorized: NDArray[np.float64] = np.empty_like(values)
    for index, (_, column) in enumerate(kernels_and_values):
        winsorized[:, index] = column
    h = kernels[0].h
    locations = np.asarray([kernel.trimmed_mean for kernel in kernels])
    qc = float(h * np.sum((locations - np.mean(locations)) ** 2))
    centered = (
        winsorized
        - np.mean(winsorized, axis=1, keepdims=True)
        - np.mean(winsorized, axis=0, keepdims=True)
        + np.mean(winsorized)
    )
    qe = float(np.sum(centered**2))
    if qe <= 0.0:
        raise ValueError("robust repeated design requires positive residual variation")
    statistic = qc / (qe / (h - 1))
    covariance_centered = winsorized - np.mean(winsorized, axis=0, keepdims=True)
    covariance: NDArray[np.float64] = (covariance_centered.T @ covariance_centered) / (
        subjects - 1
    )
    v_bar = float(np.mean(covariance))
    v_diag = sum(float(covariance[index, index]) for index in range(conditions)) / (
        conditions
    )
    row_means = np.mean(covariance, axis=1)
    a_value = float((conditions**2) * ((v_diag - v_bar) ** 2) / (conditions - 1))
    b_value = float(
        np.sum(covariance**2)
        - (2 * conditions * np.sum(row_means**2))
        + ((conditions**2) * (v_bar**2))
    )
    if a_value <= 0.0 or b_value <= 0.0:
        raise ValueError("robust repeated covariance epsilon is degenerate")
    epsilon_hat = a_value / b_value
    epsilon_denominator = (conditions - 1) * (
        subjects - 1 - ((conditions - 1) * epsilon_hat)
    )
    if epsilon_denominator <= 0.0:
        raise ValueError("robust repeated epsilon denominator is invalid")
    epsilon_raw = (
        (subjects * (conditions - 1) * epsilon_hat) - 2.0
    ) / epsilon_denominator
    if not np.isfinite(epsilon_raw) or epsilon_raw <= 0.0:
        raise ValueError("robust repeated epsilon is invalid")
    epsilon = min(1.0, max(1.0 / (conditions - 1), epsilon_raw))
    uncorrected_df1 = float(conditions - 1)
    uncorrected_df2 = float((conditions - 1) * (h - 1))
    df1 = uncorrected_df1 * epsilon
    df2 = uncorrected_df2 * epsilon
    p_value = float(scipy_stats.f.sf(statistic, df1, df2))
    correction = RobustRepeatedCorrectionResult(
        name="wrs2_winsorized_epsilon",
        epsilon=epsilon,
        uncorrected_df1=uncorrected_df1,
        uncorrected_df2=uncorrected_df2,
        corrected_df1=df1,
        corrected_df2=df2,
        corrected_p_value=p_value,
        covariance_a=a_value,
        covariance_b=b_value,
        epsilon_hat=epsilon_hat,
        epsilon_raw=epsilon_raw,
        qc=qc,
        qe=qe,
    )
    return (
        RobustTestResult(
            name="winsorized_repeated_anova",
            target="equal_population_20pct_trimmed_condition_locations",
            null_value=None,
            alternative="two-sided",
            statistic=statistic,
            df1=df1,
            df2=df2,
            p_value=p_value,
            reference_distribution="f",
        ),
        correction,
    )


def analyze_ggbetweenstats(
    data: pl.DataFrame,
    x: str,
    y: str,
    *,
    type: str = "parametric",
    alternative: str = "two-sided",
    conf_level: float = 0.95,
    p_adjust: str = "holm",
    pairwise_alpha: float = 0.05,
    pairwise_display: str = "significant",
    maximum_rows: int = DEFAULT_MAX_ROWS,
    maximum_levels: int = DEFAULT_MAX_LEVELS,
    maximum_rendered_observations: int = DEFAULT_MAX_RENDERED_OBSERVATIONS,
    trim_fraction: float = TRIM_FRACTION,
) -> ComparisonAnalysis:
    """Analyze an approved Welch or robust independent-groups comparison."""

    display = _validate_options(
        method_type=type,
        alternative=alternative,
        conf_level=conf_level,
        p_adjust=p_adjust,
        pairwise_alpha=pairwise_alpha,
        pairwise_display=pairwise_display,
        maximum_levels=maximum_levels,
        maximum_rendered_observations=maximum_rendered_observations,
    )
    sample = select_comparison_sample(
        data,
        x,
        y,
        maximum_rows=maximum_rows,
        maximum_levels=maximum_levels,
    )
    if type == "robust":
        if trim_fraction != TRIM_FRACTION:
            raise ValueError("trim_fraction must equal 0.20 for M6A robust methods")
        if len(sample.levels) > 2 and alternative != "two-sided":
            raise ValueError("robust omnibus alternatives must be 'two-sided'")
        robust_levels = _robust_levels(
            cast(tuple[object, ...], sample.levels), sample.values, conf_level
        )
        if len(sample.levels) == 2:
            unnamed = _yuen_contrast(
                sample.values[0], sample.values[1], conf_level, alternative
            )
            primary = _named_robust_contrast(
                unnamed,
                sample.levels[0],
                sample.levels[1],
                adjusted_p_value=unnamed.test.p_value,
                alpha=pairwise_alpha,
            )
            omnibus = primary.test
            estimate = primary.estimate
            interval = primary.interval
            effect_size = primary.effect_size
            robust_pairwise: tuple[RobustPairwiseComparisonResult, ...] = ()
        else:
            omnibus = _welch_yuen(sample.values)
            estimate = None
            interval = None
            effect_size = RobustEffectResult(
                name="raw_trimmed_location_difference",
                value=None,
                target="omnibus_has_no_single_raw_difference",
                standardized_effect_unavailable=(
                    "robust_standardized_effect_not_approved"
                ),
            )
            robust_pairwise = _robust_pairwise(
                cast(tuple[object, ...], sample.levels),
                sample.values,
                design="between",
                conf_level=conf_level,
                p_adjust=p_adjust,
                alpha=pairwise_alpha,
            )
        return ComparisonAnalysis(
            sample=sample,
            result=cast(
                ComparisonResult,
                RobustComparisonResult(
                    schema_version=2,
                    analysis="ggbetweenstats_robust",
                    mode="robust",
                    design="between",
                    x=x,
                    y=y,
                    subject_id=None,
                    sample=sample.audit,
                    method=method_result("yuen_welch_yuen_twenty_percent_trimmed"),
                    levels=robust_levels,
                    omnibus=omnibus,
                    estimate=estimate,
                    interval=interval,
                    effect_size=effect_size,
                    pairwise=robust_pairwise,
                    p_adjust=p_adjust,
                    pairwise_alpha=float(pairwise_alpha),
                    pairwise_display=display,
                    correction=None,
                    limits=ResourceLimits(
                        maximum_rows=maximum_rows,
                        maximum_levels=maximum_levels,
                        maximum_pairwise_hypotheses=(
                            maximum_levels * (maximum_levels - 1) // 2
                        ),
                        maximum_rendered_observations=maximum_rendered_observations,
                    ),
                    warnings=(
                        "standardized robust effect unavailable: not approved for M6A",
                        "pairwise intervals are pointwise and unadjusted",
                    ),
                ),
            ),
        )
    if trim_fraction != TRIM_FRACTION:
        raise ValueError("trim_fraction is unused for parametric analysis")
    levels = _level_results(
        cast(tuple[object, ...], sample.levels), sample.values, conf_level
    )
    if len(sample.levels) == 2:
        primary = _welch_contrast(sample.values[0], sample.values[1], conf_level)
        omnibus = primary.test
        estimate = primary.estimate
        interval = primary.interval
        effect_size = primary.effect_size
        pairwise: tuple[PairwiseComparisonResult, ...] = ()
    else:
        omnibus = _welch_anova(sample.values)
        estimate = None
        interval = None
        effect_size = EffectSizeResult(
            name="partial_omega_squared_welch_f",
            value=_omega_from_f(
                omnibus.statistic, cast(float, omnibus.df1), omnibus.df2
            ),
            standardizer="welch_f_conversion",
        )
        pairwise = _pairwise_results(
            cast(tuple[object, ...], sample.levels),
            sample.values,
            design="between",
            conf_level=conf_level,
            p_adjust=p_adjust,
            pairwise_alpha=pairwise_alpha,
        )
    result = ComparisonResult(
        schema_version=1,
        analysis="ggbetweenstats_welch",
        design="between",
        x=x,
        y=y,
        subject_id=None,
        sample=sample.audit,
        levels=levels,
        omnibus=omnibus,
        estimate=estimate,
        interval=interval,
        effect_size=effect_size,
        pairwise=pairwise,
        p_adjust=p_adjust,
        pairwise_alpha=float(pairwise_alpha),
        pairwise_display=display,
        correction=None,
        limits=ResourceLimits(
            maximum_rows=maximum_rows,
            maximum_levels=maximum_levels,
            maximum_pairwise_hypotheses=maximum_levels * (maximum_levels - 1) // 2,
            maximum_rendered_observations=maximum_rendered_observations,
        ),
        warnings=("effect-size confidence intervals are not implemented",),
    )
    return ComparisonAnalysis(sample=sample, result=result)


def _repeated_anova(
    values: NDArray[np.float64],
) -> tuple[ComparisonTestResult, RepeatedCorrectionResult, EffectSizeResult]:
    subjects, conditions = values.shape
    grand_mean = float(np.mean(values))
    condition_means = np.mean(values, axis=0)
    subject_means = np.mean(values, axis=1)
    ss_condition = float(subjects * np.sum((condition_means - grand_mean) ** 2))
    ss_subject = float(conditions * np.sum((subject_means - grand_mean) ** 2))
    ss_total = float(np.sum((values - grand_mean) ** 2))
    ss_error = ss_total - ss_condition - ss_subject
    df1 = float(conditions - 1)
    df2 = float((subjects - 1) * (conditions - 1))
    if ss_error <= 0.0:
        raise ValueError("repeated design requires positive residual variation")
    statistic = (ss_condition / df1) / (ss_error / df2)

    covariance = np.cov(values, rowvar=False, ddof=1)
    centering = np.eye(conditions) - (np.ones((conditions, conditions)) / conditions)
    projected = centering @ covariance @ centering
    projected_trace = sum(float(projected[index, index]) for index in range(conditions))
    projected_square = projected @ projected
    square_trace = sum(
        float(projected_square[index, index]) for index in range(conditions)
    )
    numerator = projected_trace**2
    denominator = float((conditions - 1) * square_trace)
    if denominator <= 0.0:
        raise ValueError("repeated covariance is degenerate for sphericity correction")
    epsilon = min(1.0, max(1.0 / (conditions - 1), numerator / denominator))
    uncorrected_p = float(scipy_stats.f.sf(statistic, df1, df2))
    corrected_df1 = epsilon * df1
    corrected_df2 = epsilon * df2
    corrected_p = float(scipy_stats.f.sf(statistic, corrected_df1, corrected_df2))
    correction = RepeatedCorrectionResult(
        name="greenhouse_geisser",
        epsilon=epsilon,
        uncorrected_df1=df1,
        uncorrected_df2=df2,
        uncorrected_p_value=uncorrected_p,
        corrected_df1=corrected_df1,
        corrected_df2=corrected_df2,
        corrected_p_value=corrected_p,
    )
    test = ComparisonTestResult(
        name="repeated_measures_anova",
        statistic=statistic,
        df1=corrected_df1,
        df2=corrected_df2,
        p_value=corrected_p,
    )
    effect = EffectSizeResult(
        name="partial_omega_squared_repeated_f",
        value=_omega_from_f(statistic, df1, df2),
        standardizer="uncorrected_repeated_f_conversion",
    )
    return test, correction, effect


def analyze_ggwithinstats(
    data: pl.DataFrame,
    x: str,
    y: str,
    *,
    subject_id: str,
    type: str = "parametric",
    alternative: str = "two-sided",
    conf_level: float = 0.95,
    p_adjust: str = "holm",
    pairwise_alpha: float = 0.05,
    pairwise_display: str = "significant",
    maximum_rows: int = DEFAULT_MAX_ROWS,
    maximum_levels: int = DEFAULT_MAX_LEVELS,
    maximum_rendered_observations: int = DEFAULT_MAX_RENDERED_OBSERVATIONS,
    maximum_subject_paths: int = DEFAULT_MAX_SUBJECT_PATHS,
    trim_fraction: float = TRIM_FRACTION,
) -> ComparisonAnalysis:
    """Analyze an approved classical or robust complete-block comparison."""

    display = _validate_options(
        method_type=type,
        alternative=alternative,
        conf_level=conf_level,
        p_adjust=p_adjust,
        pairwise_alpha=pairwise_alpha,
        pairwise_display=pairwise_display,
        maximum_levels=maximum_levels,
        maximum_rendered_observations=maximum_rendered_observations,
    )
    if isinstance(maximum_subject_paths, bool) or maximum_subject_paths < 1:
        raise ValueError("maximum_subject_paths must be a positive integer")
    sample = select_repeated_sample(
        data,
        x,
        y,
        subject_id,
        maximum_rows=maximum_rows,
        maximum_levels=maximum_levels,
        minimum_subjects=5 if type == "robust" else 3,
    )
    columns = tuple(sample.values[:, index] for index in range(len(sample.conditions)))
    if type == "robust":
        if trim_fraction != TRIM_FRACTION:
            raise ValueError("trim_fraction must equal 0.20 for M6A robust methods")
        if len(sample.conditions) > 2 and alternative != "two-sided":
            raise ValueError("robust omnibus alternatives must be 'two-sided'")
        robust_levels = _robust_levels(
            cast(tuple[object, ...], sample.conditions), columns, conf_level
        )
        if len(sample.conditions) == 2:
            unnamed = _trimmed_difference_contrast(
                columns[0], columns[1], conf_level, alternative
            )
            primary = _named_robust_contrast(
                unnamed,
                sample.conditions[0],
                sample.conditions[1],
                adjusted_p_value=unnamed.test.p_value,
                alpha=pairwise_alpha,
            )
            omnibus = primary.test
            estimate = primary.estimate
            interval = primary.interval
            effect_size = primary.effect_size
            robust_pairwise: tuple[RobustPairwiseComparisonResult, ...] = ()
            correction = None
        else:
            omnibus, correction = _robust_repeated(sample.values)
            estimate = None
            interval = None
            effect_size = RobustEffectResult(
                name="raw_trimmed_location_difference",
                value=None,
                target="omnibus_has_no_single_raw_difference",
                standardized_effect_unavailable=(
                    "robust_standardized_effect_not_approved"
                ),
            )
            robust_pairwise = _robust_pairwise(
                cast(tuple[object, ...], sample.conditions),
                columns,
                design="within",
                conf_level=conf_level,
                p_adjust=p_adjust,
                alpha=pairwise_alpha,
            )
        return ComparisonAnalysis(
            sample=sample,
            result=cast(
                ComparisonResult,
                RobustComparisonResult(
                    schema_version=2,
                    analysis="ggwithinstats_robust",
                    mode="robust",
                    design="within",
                    x=x,
                    y=y,
                    subject_id=subject_id,
                    sample=sample.audit,
                    method=method_result(
                        "trimmed_subject_difference_winsorized_repeated"
                    ),
                    levels=robust_levels,
                    omnibus=omnibus,
                    estimate=estimate,
                    interval=interval,
                    effect_size=effect_size,
                    pairwise=robust_pairwise,
                    p_adjust=p_adjust,
                    pairwise_alpha=float(pairwise_alpha),
                    pairwise_display=display,
                    correction=correction,
                    limits=ResourceLimits(
                        maximum_rows=maximum_rows,
                        maximum_levels=maximum_levels,
                        maximum_pairwise_hypotheses=(
                            maximum_levels * (maximum_levels - 1) // 2
                        ),
                        maximum_rendered_observations=maximum_rendered_observations,
                        maximum_subject_paths=maximum_subject_paths,
                    ),
                    warnings=(
                        "standardized robust effect unavailable: not approved for M6A",
                        "pairwise intervals are pointwise and unadjusted",
                    ),
                ),
            ),
        )
    if trim_fraction != TRIM_FRACTION:
        raise ValueError("trim_fraction is unused for parametric analysis")
    levels = _level_results(
        cast(tuple[object, ...], sample.conditions), columns, conf_level
    )
    if len(sample.conditions) == 2:
        primary = _paired_contrast(columns[0], columns[1], conf_level)
        omnibus = primary.test
        estimate = primary.estimate
        interval = primary.interval
        effect_size = primary.effect_size
        pairwise: tuple[PairwiseComparisonResult, ...] = ()
        correction = None
    else:
        omnibus, correction, effect_size = _repeated_anova(sample.values)
        estimate = None
        interval = None
        pairwise = _pairwise_results(
            cast(tuple[object, ...], sample.conditions),
            columns,
            design="within",
            conf_level=conf_level,
            p_adjust=p_adjust,
            pairwise_alpha=pairwise_alpha,
        )
    result = ComparisonResult(
        schema_version=1,
        analysis="ggwithinstats_parametric",
        design="within",
        x=x,
        y=y,
        subject_id=subject_id,
        sample=sample.audit,
        levels=levels,
        omnibus=omnibus,
        estimate=estimate,
        interval=interval,
        effect_size=effect_size,
        pairwise=pairwise,
        p_adjust=p_adjust,
        pairwise_alpha=float(pairwise_alpha),
        pairwise_display=display,
        correction=correction,
        limits=ResourceLimits(
            maximum_rows=maximum_rows,
            maximum_levels=maximum_levels,
            maximum_pairwise_hypotheses=maximum_levels * (maximum_levels - 1) // 2,
            maximum_rendered_observations=maximum_rendered_observations,
            maximum_subject_paths=maximum_subject_paths,
        ),
        warnings=("effect-size confidence intervals are not implemented",),
    )
    return ComparisonAnalysis(sample=sample, result=result)
