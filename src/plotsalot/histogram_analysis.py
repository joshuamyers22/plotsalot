"""Renderer-independent one-sample histogram analysis."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Literal, Protocol, cast

import numpy as np
import polars as pl

from plotsalot.bayesian import (
    DEFAULT_MAX_BAYESIAN_WORK,
    one_sample_posterior,
)
from plotsalot.bayesian import (
    method_result as bayesian_method_result,
)
from plotsalot.bayesian_result import BayesianOneSampleResult
from plotsalot.data import (
    DEFAULT_MAX_ROWS,
    FloatArray,
    NumericSample,
    select_numeric_sample,
)
from plotsalot.result import (
    AnalysisResult,
    EffectSizeResult,
    EstimateResult,
    IntervalResult,
    ResourceLimits,
    TestResult,
)
from plotsalot.robust import TRIM_FRACTION, method_result, trimmed_kernel
from plotsalot.robust_result import (
    RobustEffectResult,
    RobustEstimateResult,
    RobustOneSampleResult,
    RobustTestResult,
)

Alternative = Literal["two-sided", "less", "greater"]
OneSampleAnalysisIdentity = Literal[
    "gghistostats_one_sample_parametric",
    "ggdotplotstats_one_sample_parametric",
    "gghistostats_one_sample_robust",
    "ggdotplotstats_one_sample_robust",
    "gghistostats_one_sample_bayesian",
    "ggdotplotstats_one_sample_bayesian",
]


class _TtestResult(Protocol):
    statistic: float
    pvalue: float


class _TDistribution(Protocol):
    def ppf(self, probability: float, df: float) -> float: ...

    def cdf(self, value: float, df: float) -> float: ...

    def sf(self, value: float, df: float) -> float: ...


class _ScipyStats(Protocol):
    t: _TDistribution

    def ttest_1samp(
        self,
        values: FloatArray,
        *,
        popmean: float,
        alternative: Alternative,
    ) -> _TtestResult: ...


scipy_stats = cast(_ScipyStats, import_module("scipy.stats"))

_PROTOTYPE_WARNING = (
    "Adapted method: effect-size uncertainty and nonparametric and Bayesian "
    "modes are not implemented."
)


@dataclass(frozen=True, slots=True)
class HistogramAnalysis:
    """One-sample result and the exact numeric sample used to compute it."""

    sample: NumericSample
    result: AnalysisResult

    def __post_init__(self) -> None:
        if self.sample.column != self.result.column:
            raise ValueError("numeric sample and result columns must match")
        if self.sample.audit != self.result.sample:
            raise ValueError("numeric sample and result audits must match")


def analyze_gghistostats(
    data: pl.DataFrame,
    x: str,
    *,
    test_value: float = 0.0,
    alternative: Alternative = "two-sided",
    conf_level: float = 0.95,
    type: str = "parametric",
    trim_fraction: float = TRIM_FRACTION,
    prior_scale: float | None = None,
    credible_level: float = 0.95,
    maximum_bayesian_work: int = DEFAULT_MAX_BAYESIAN_WORK,
    maximum_rows: int = DEFAULT_MAX_ROWS,
) -> HistogramAnalysis:
    """Analyze an approved classical, robust, or Bayesian histogram method."""

    if type not in {"parametric", "robust", "bayes"}:
        raise ValueError("type must be 'parametric', 'robust', or 'bayes'")
    if type == "parametric" and (
        trim_fraction != TRIM_FRACTION
        or prior_scale is not None
        or credible_level != 0.95
        or maximum_bayesian_work != DEFAULT_MAX_BAYESIAN_WORK
    ):
        raise ValueError("robust/Bayesian options are unused for parametric analysis")
    if type == "robust" and (
        prior_scale is not None
        or credible_level != 0.95
        or maximum_bayesian_work != DEFAULT_MAX_BAYESIAN_WORK
    ):
        raise ValueError("Bayesian options are unused for robust analysis")
    if type == "bayes":
        if trim_fraction != TRIM_FRACTION:
            raise ValueError("trim_fraction is unused for Bayesian analysis")
        if prior_scale is None:
            raise ValueError("prior_scale is required for Bayesian analysis")
        if alternative != "two-sided":
            raise ValueError("Bayesian one-sample alternative must be 'two-sided'")
    sample = select_numeric_sample(
        data,
        x,
        minimum_size=5 if type == "robust" else (3 if type == "bayes" else 2),
        require_variation=type != "bayes",
        maximum_rows=maximum_rows,
    )
    return analyze_one_sample_sample(
        sample,
        analysis=(
            "gghistostats_one_sample_robust"
            if type == "robust"
            else (
                "gghistostats_one_sample_bayesian"
                if type == "bayes"
                else "gghistostats_one_sample_parametric"
            )
        ),
        test_value=test_value,
        alternative=alternative,
        conf_level=conf_level,
        trim_fraction=trim_fraction,
        prior_scale=prior_scale,
        credible_level=credible_level,
        maximum_bayesian_work=maximum_bayesian_work,
        maximum_rows=maximum_rows,
    )


def analyze_one_sample_sample(
    sample: NumericSample,
    *,
    analysis: OneSampleAnalysisIdentity,
    test_value: float = 0.0,
    alternative: Alternative = "two-sided",
    conf_level: float = 0.95,
    trim_fraction: float = TRIM_FRACTION,
    prior_scale: float | None = None,
    credible_level: float = 0.95,
    maximum_bayesian_work: int = DEFAULT_MAX_BAYESIAN_WORK,
    maximum_rows: int = DEFAULT_MAX_ROWS,
) -> HistogramAnalysis:
    """Apply the approved one-sample method to an already reconciled sample."""

    if not 0.0 < conf_level < 1.0:
        raise ValueError("conf_level must be strictly between 0 and 1")
    if alternative not in {"two-sided", "less", "greater"}:
        raise ValueError("alternative must be 'two-sided', 'less', or 'greater'")
    if not np.isfinite(test_value):
        raise ValueError("test_value must be finite")

    if analysis.endswith("_bayesian"):
        if prior_scale is None:
            raise ValueError("prior_scale is required for Bayesian analysis")
        if alternative != "two-sided":
            raise ValueError("Bayesian one-sample alternative must be 'two-sided'")
        if trim_fraction != TRIM_FRACTION:
            raise ValueError("trim_fraction is unused for Bayesian analysis")
        prior, location, effect, evidence, computation = one_sample_posterior(
            sample.values,
            test_value=float(test_value),
            prior_scale=prior_scale,
            credible_level=credible_level,
            maximum_work=maximum_bayesian_work,
        )
        return HistogramAnalysis(
            sample=sample,
            result=cast(
                AnalysisResult,
                BayesianOneSampleResult(
                    schema_version=3,
                    analysis=analysis,
                    mode="bayes",
                    column=sample.column,
                    sample=sample.audit,
                    method=bayesian_method_result("conjugate_normal_location"),
                    prior=prior,
                    location=location,
                    effect=effect,
                    evidence=evidence,
                    computation=computation,
                    limits=ResourceLimits(maximum_rows=maximum_rows),
                    warnings=(
                        "numeric Bayes factor uses plotsalot's adapted proper prior",
                    ),
                ),
            ),
        )

    if analysis.endswith("_robust"):
        kernel, _ = trimmed_kernel(sample.values, trim_fraction=trim_fraction)
        standard_error = float(np.sqrt(kernel.q))
        statistic = (kernel.trimmed_mean - test_value) / standard_error
        df = float(kernel.h - 1)
        if alternative == "two-sided":
            p_value = min(1.0, 2.0 * float(scipy_stats.t.sf(abs(statistic), df)))
        elif alternative == "less":
            p_value = float(scipy_stats.t.cdf(statistic, df))
        else:
            p_value = float(scipy_stats.t.sf(statistic, df))
        critical = float(scipy_stats.t.ppf(0.5 + (conf_level / 2.0), df))
        margin = critical * standard_error
        result = RobustOneSampleResult(
            schema_version=2,
            analysis=analysis,
            mode="robust",
            column=sample.column,
            sample=sample.audit,
            method=method_result("twenty_percent_trimmed_location"),
            estimate=RobustEstimateResult(
                name="trimmed_mean",
                value=kernel.trimmed_mean,
                standard_deviation=float(np.sqrt(kernel.winsorized_variance)),
                kernel=kernel,
            ),
            test=RobustTestResult(
                name="trimmed_mean_t",
                target="population_20pct_trimmed_location",
                null_value=float(test_value),
                alternative=alternative,
                statistic=statistic,
                df1=None,
                df2=df,
                p_value=p_value,
                reference_distribution="student_t",
            ),
            interval=IntervalResult(
                target="population_20pct_trimmed_location",
                method="trimmed_mean_student_t_two_sided",
                level=conf_level,
                low=kernel.trimmed_mean - margin,
                high=kernel.trimmed_mean + margin,
            ),
            effect_size=RobustEffectResult(
                name="raw_trimmed_location_difference",
                value=kernel.trimmed_mean - test_value,
                target="population_20pct_trimmed_location_difference",
                standardized_effect_unavailable="not_approved_for_m6a",
            ),
            limits=ResourceLimits(maximum_rows=maximum_rows),
            warnings=("standardized effect unavailable: not approved for M6A",),
        )
        return HistogramAnalysis(sample=sample, result=cast(AnalysisResult, result))

    if trim_fraction != TRIM_FRACTION:
        raise ValueError("trim_fraction is unused for parametric analysis")
    if prior_scale is not None or maximum_bayesian_work != DEFAULT_MAX_BAYESIAN_WORK:
        raise ValueError("Bayesian options are unused for parametric analysis")

    values = sample.values
    mean = float(np.mean(values))
    standard_deviation = float(np.std(values, ddof=1))
    test = scipy_stats.ttest_1samp(
        values, popmean=float(test_value), alternative=alternative
    )
    statistic = float(test.statistic)
    p_value = float(test.pvalue)
    df = float(values.size - 1)

    standard_error = standard_deviation / float(np.sqrt(values.size))
    critical = float(scipy_stats.t.ppf(0.5 + (conf_level / 2.0), df))
    margin = critical * standard_error
    effect_size = (mean - test_value) / standard_deviation

    result = AnalysisResult(
        schema_version=1,
        analysis=analysis,
        column=sample.column,
        sample=sample.audit,
        estimate=EstimateResult(
            name="mean",
            value=mean,
            standard_deviation=standard_deviation,
        ),
        test=TestResult(
            name="one_sample_t",
            null_value=float(test_value),
            alternative=alternative,
            statistic=statistic,
            df=df,
            p_value=p_value,
        ),
        interval=IntervalResult(
            target="population_mean",
            method="student_t_two_sided",
            level=conf_level,
            low=mean - margin,
            high=mean + margin,
        ),
        effect_size=EffectSizeResult(
            name="cohen_d",
            value=effect_size,
            standardizer="sample_standard_deviation_ddof_1",
        ),
        warnings=(_PROTOTYPE_WARNING,),
    )

    return HistogramAnalysis(sample=sample, result=result)
