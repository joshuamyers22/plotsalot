"""Matplotlib rendering for labeled dot-plot analyses."""

from __future__ import annotations

from typing import Protocol, cast

import numpy as np
import polars as pl
from matplotlib.figure import Figure

from plotsalot.data import DEFAULT_MAX_ROWS, FloatArray
from plotsalot.dotplot_analysis import (
    DEFAULT_MAX_LABELS,
    DotPlotAnalysis,
    analyze_ggdotplotstats,
)
from plotsalot.histogram_analysis import Alternative
from plotsalot.plot import PlotAnnotations, StatsPlot
from plotsalot.result import DotPlotResult
from plotsalot.robust import TRIM_FRACTION
from plotsalot.robust_result import RobustDotPlotResult


class _DotAxes(Protocol):
    transAxes: object

    def errorbar(
        self,
        x: float,
        y: float,
        *,
        xerr: object,
        fmt: str,
        color: str,
        capsize: int,
    ) -> object: ...

    def plot(self, x: float, y: float, fmt: str, *, color: str) -> object: ...

    def axvline(
        self, x: float, *, color: str, linestyle: str, label: str
    ) -> object: ...

    def set_yticks(self, ticks: FloatArray, labels: list[str]) -> object: ...

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


def _draw_dotplot(
    axes: _DotAxes,
    analysis: DotPlotAnalysis,
    *,
    title: str,
    show_intervals: bool,
) -> PlotAnnotations:
    result = cast(DotPlotResult | RobustDotPlotResult, analysis.result)
    positions = np.arange(len(result.estimates), dtype=np.float64)
    for position, estimate in zip(positions, result.estimates, strict=True):
        if show_intervals and estimate.interval is not None:
            lower = estimate.value - estimate.interval.low
            upper = estimate.interval.high - estimate.value
            axes.errorbar(
                estimate.value,
                position,
                xerr=np.array([[lower], [upper]]),
                fmt="o",
                color="black",
                capsize=3,
            )
        else:
            axes.plot(estimate.value, position, "o", color="black")

    robust = isinstance(result, RobustDotPlotResult)
    axes.axvline(
        result.one_sample.estimate.value,
        color="#1f77b4",
        linestyle="--",
        label="overall 20% trimmed mean" if robust else "overall mean",
    )
    axes.set_yticks(positions, [str(estimate.label) for estimate in result.estimates])
    axes.set_xlabel(result.x)
    axes.set_ylabel(result.label_column)
    axes.set_title(title)
    axes.legend()

    test = result.one_sample.test
    if robust:
        subtitle = (
            f"20% trimmed-mean t({test.df:.0f}) = {test.statistic:.2f}, "
            f"{_p_value_text(test.p_value)}; raw difference = "
            f"{result.one_sample.effect_size.value:.2f}; "
            "standardized effect unavailable"
        )
        caption = (
            f"n = {result.sample.analyzed_rows}; "
            f"{result.sample.dropped_null_rows} null row(s) excluded; "
            f"{result.one_sample.interval.level:.0%} per-label trimmed-location CIs"
        )
    else:
        subtitle = (
            f"t({test.df:.0f}) = {test.statistic:.2f}, "
            f"{_p_value_text(test.p_value)}, "
            f"Cohen's d = {result.one_sample.effect_size.value:.2f}"
        )
        caption = (
            f"n = {result.sample.analyzed_rows}; "
            f"{result.sample.dropped_null_rows} null row(s) excluded; "
            f"{result.one_sample.interval.level:.0%} per-label mean CIs where estimable"
        )
    axes.text(
        0.5,
        1.01,
        subtitle,
        ha="center",
        va="bottom",
        transform=axes.transAxes,
    )
    return PlotAnnotations(title=title, subtitle=subtitle, caption=caption)


def render_ggdotplotstats(
    analysis: DotPlotAnalysis,
    *,
    title: str | None = None,
    show_intervals: bool = True,
) -> StatsPlot[DotPlotResult]:
    """Render a previously computed labeled dot-plot analysis."""

    figure = Figure(layout="constrained")
    axes = figure.subplots()
    renderer = cast(_DotAxes, axes)
    rendered_title = title or f"{analysis.result.x} by {analysis.result.label_column}"
    annotations = _draw_dotplot(
        renderer,
        analysis,
        title=rendered_title,
        show_intervals=show_intervals,
    )
    cast(_FigureRenderer, figure).text(
        0.01,
        0.01,
        annotations.caption,
        ha="left",
        va="bottom",
        fontsize="small",
    )
    return StatsPlot(
        figure=figure,
        axes={"main": axes},
        result=analysis.result,
        annotations=annotations,
    )


def ggdotplotstats(
    data: pl.DataFrame,
    x: str,
    y: str,
    *,
    test_value: float = 0.0,
    alternative: Alternative = "two-sided",
    conf_level: float = 0.95,
    type: str = "parametric",
    trim_fraction: float = TRIM_FRACTION,
    maximum_rows: int = DEFAULT_MAX_ROWS,
    maximum_labels: int = DEFAULT_MAX_LABELS,
    title: str | None = None,
    show_intervals: bool = True,
) -> StatsPlot[DotPlotResult]:
    """Analyze and render an approved classical or robust labeled dot plot."""

    analysis = analyze_ggdotplotstats(
        data,
        x,
        y,
        test_value=test_value,
        alternative=alternative,
        conf_level=conf_level,
        type=type,
        trim_fraction=trim_fraction,
        maximum_rows=maximum_rows,
        maximum_labels=maximum_labels,
    )
    return render_ggdotplotstats(
        analysis,
        title=title,
        show_intervals=show_intervals,
    )
