"""Renderer-independent one-sample histogram analysis."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Literal, Protocol, cast

import numpy as np
import polars as pl

from plotsalot.data import FloatArray, NumericSample, select_numeric_sample
from plotsalot.result import (
    AnalysisResult,
    EffectSizeResult,
    EstimateResult,
    IntervalResult,
    TestResult,
)

Alternative = Literal["two-sided", "less", "greater"]


class _TtestResult(Protocol):
    statistic: float
    pvalue: float


class _TDistribution(Protocol):
    def ppf(self, probability: float, df: float) -> float: ...


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
    "M0 prototype: effect-size uncertainty and nonparametric, robust, Bayesian, "
    "and grouped modes are not implemented."
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
) -> HistogramAnalysis:
    """Analyze the parametric one-sample histogram method without rendering."""

    if not 0.0 < conf_level < 1.0:
        raise ValueError("conf_level must be strictly between 0 and 1")
    if alternative not in {"two-sided", "less", "greater"}:
        raise ValueError("alternative must be 'two-sided', 'less', or 'greater'")
    if not np.isfinite(test_value):
        raise ValueError("test_value must be finite")

    sample = select_numeric_sample(data, x, minimum_size=2, require_variation=True)
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
        analysis="gghistostats_one_sample_parametric",
        column=x,
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
