"""Matplotlib rendering and composition for the histogram analysis."""

from __future__ import annotations

from typing import Protocol, cast

import numpy as np
import polars as pl
from matplotlib.figure import Figure

from plotsalot.bayesian import DEFAULT_MAX_BAYESIAN_WORK
from plotsalot.bayesian_result import BayesianOneSampleResult
from plotsalot.data import DEFAULT_MAX_ROWS, FloatArray
from plotsalot.histogram_analysis import (
    Alternative,
    HistogramAnalysis,
    analyze_gghistostats,
)
from plotsalot.plot import PlotAnnotations, StatsPlot
from plotsalot.result import AnalysisResult
from plotsalot.robust import TRIM_FRACTION
from plotsalot.robust_result import RobustOneSampleResult


class _AxesRenderer(Protocol):
    transAxes: object

    def hist(
        self,
        values: FloatArray,
        *,
        bins: str | int,
        color: str,
        edgecolor: str,
        alpha: float,
    ) -> object: ...

    def axvline(
        self, x: float, *, color: str, linestyle: str, label: str
    ) -> object: ...

    def set_xlabel(self, label: str) -> object: ...

    def set_ylabel(self, label: str) -> object: ...

    def set_title(self, label: str) -> object: ...

    def legend(self) -> object: ...

    def text(
        self,
        x: float,
        y: float,
        text: str,
        *,
        ha: str,
        va: str,
        transform: object,
    ) -> object: ...


class _FigureRenderer(Protocol):
    def text(
        self,
        x: float,
        y: float,
        text: str,
        *,
        ha: str,
        va: str,
        fontsize: str,
    ) -> object: ...


def _p_value_text(p_value: float) -> str:
    return "p < 0.001" if p_value < 0.001 else f"p = {p_value:.3f}"


def render_gghistostats(
    analysis: HistogramAnalysis,
    *,
    binwidth: float | None = None,
    title: str | None = None,
) -> StatsPlot[AnalysisResult]:
    """Render a previously computed histogram analysis with Matplotlib."""

    if binwidth is not None and (not np.isfinite(binwidth) or binwidth <= 0.0):
        raise ValueError("binwidth must be finite and greater than zero")

    values = analysis.sample.values
    result = cast(
        AnalysisResult | RobustOneSampleResult | BayesianOneSampleResult,
        analysis.result,
    )
    sample = result.sample
    x = analysis.sample.column
    bayesian = isinstance(result, BayesianOneSampleResult)
    if bayesian:
        test_value = result.location.null_value
        conf_level = result.location.interval.level
        mean = result.location.median
    else:
        if result.test.null_value is None:
            raise ValueError("one-sample result requires a null value")
        test_value = result.test.null_value
        conf_level = result.interval.level
        mean = result.estimate.value

    if binwidth is None:
        bins: str | int = "auto"
    else:
        data_range = float(np.max(values) - np.min(values))
        bins = max(1, int(np.ceil(data_range / binwidth)))

    figure = Figure(layout="constrained")
    axes = figure.subplots()
    renderer = cast(_AxesRenderer, axes)
    renderer.hist(values, bins=bins, color="0.55", edgecolor="black", alpha=0.75)
    renderer.axvline(test_value, color="black", linestyle=":", label="test value")
    robust = isinstance(result, RobustOneSampleResult)
    centrality_label = (
        "posterior median"
        if bayesian
        else ("20% trimmed mean" if robust else "sample mean")
    )
    renderer.axvline(mean, color="#1f77b4", linestyle="--", label=centrality_label)
    renderer.set_xlabel(x)
    renderer.set_ylabel("Count")
    rendered_title = title if title is not None else f"Distribution of {x}"
    renderer.set_title(rendered_title)
    renderer.legend()

    if bayesian:
        subtitle = (
            f"posterior median = {result.location.median:.2f}; "
            f"P(effect > 0) = {result.effect.probability_above_null:.3f}; "
            f"{result.evidence.display}"
        )
        caption = (
            f"n = {sample.analyzed_rows}; {sample.dropped_null_rows} null row(s) "
            f"excluded; {conf_level:.0%} equal-tail credible interval "
            f"[{result.location.interval.low:.2f}, "
            f"{result.location.interval.high:.2f}]; adapted NIG prior"
        )
    elif robust:
        statistic = result.test.statistic
        if statistic is None:
            raise ValueError("robust one-sample result requires a statistic")
        effect_size = result.effect_size.value
        if effect_size is None:
            raise ValueError("robust one-sample result requires a raw effect")
        df = result.test.df
        p_value = result.test.p_value
        subtitle = (
            f"20% trimmed-mean t({df:.0f}) = {statistic:.2f}, "
            f"{_p_value_text(p_value)}; raw difference = {effect_size:.2f}; "
            f"h = {result.estimate.kernel.h}; standardized effect unavailable"
        )
        caption = (
            f"n = {sample.analyzed_rows}; {sample.dropped_null_rows} null row(s) "
            f"excluded; pointwise {conf_level:.0%} trimmed-location CI "
            f"[{result.interval.low:.2f}, {result.interval.high:.2f}]"
        )
    else:
        statistic = result.test.statistic
        effect_size = result.effect_size.value
        df = result.test.df
        p_value = result.test.p_value
        subtitle = (
            f"t({df:.0f}) = {statistic:.2f}, {_p_value_text(p_value)}, "
            f"Cohen's d = {effect_size:.2f}"
        )
        caption = (
            f"n = {sample.analyzed_rows}; {sample.dropped_null_rows} null row(s) "
            f"excluded; {conf_level:.0%} mean CI "
            f"[{result.interval.low:.2f}, {result.interval.high:.2f}]"
        )
    renderer.text(
        0.5,
        1.01,
        subtitle,
        ha="center",
        va="bottom",
        transform=renderer.transAxes,
    )
    cast(_FigureRenderer, figure).text(
        0.01, 0.01, caption, ha="left", va="bottom", fontsize="small"
    )

    return StatsPlot(
        figure=figure,
        axes={"main": axes},
        result=cast(AnalysisResult, result),
        annotations=PlotAnnotations(
            title=rendered_title,
            subtitle=subtitle,
            caption=caption,
        ),
    )


def gghistostats(
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
    binwidth: float | None = None,
    title: str | None = None,
) -> StatsPlot[AnalysisResult]:
    """Analyze and render an approved classical, robust, or Bayesian histogram."""

    analysis = analyze_gghistostats(
        data,
        x,
        test_value=test_value,
        alternative=alternative,
        conf_level=conf_level,
        type=type,
        trim_fraction=trim_fraction,
        prior_scale=prior_scale,
        credible_level=credible_level,
        maximum_bayesian_work=maximum_bayesian_work,
        maximum_rows=maximum_rows,
    )
    return render_gghistostats(analysis, binwidth=binwidth, title=title)
