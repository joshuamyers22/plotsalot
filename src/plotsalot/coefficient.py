"""Semantic Matplotlib renderer for M5 coefficient and meta-analysis results."""

from __future__ import annotations

from typing import Protocol, cast

import polars as pl
from matplotlib.colors import is_color_like
from matplotlib.figure import Figure

from plotsalot.coefficient_analysis import CoefficientAnalysis, analyze_ggcoefstats
from plotsalot.coefficient_result import CoefficientResult
from plotsalot.plot import PlotAnnotations, StatsPlot
from plotsalot.theme import StatsTheme, theme_ggstatsplot


class _CoefficientAxes(Protocol):
    transAxes: object

    def errorbar(
        self,
        x: float,
        y: float,
        *,
        xerr: object,
        fmt: str,
        color: str,
        capsize: float,
        markersize: float,
        label: str | None = None,
        zorder: int | None = None,
    ) -> object: ...

    def axvline(
        self, x: float, *, color: str, linestyle: str, linewidth: float
    ) -> object: ...

    def hlines(
        self,
        y: float,
        xmin: float,
        xmax: float,
        *,
        color: str,
        linewidth: float,
        label: str,
        zorder: int,
    ) -> object: ...

    def text(
        self,
        x: float,
        y: float,
        text: str,
        *,
        transform: object | None = None,
        ha: str,
        va: str,
        fontsize: str | None = None,
    ) -> object: ...

    def set_yticks(self, ticks: object, labels: list[str]) -> object: ...

    def set_ylim(self, low: float, high: float) -> object: ...

    def set_xlabel(self, label: str) -> object: ...

    def set_title(self, label: str) -> object: ...

    def legend(self, *, loc: str) -> object: ...


class _CoefficientFigure(Protocol):
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

    def set_size_inches(
        self, width: float, height: float, *, forward: bool
    ) -> object: ...


def _p_text(value: float) -> str:
    return "p < 0.001" if value < 0.001 else f"p = {value:.3f}"


def _subtitle(result: CoefficientResult) -> str:
    pooled = result.meta_analysis.pooled
    heterogeneity = result.meta_analysis.heterogeneity
    return (
        f"REML + modified Hartung-Knapp: pooled = {pooled.estimate:.3g}, "
        f"{result.conf_level:.0%} CI [{pooled.interval.low:.3g}, "
        f"{pooled.interval.high:.3g}], {_p_text(pooled.p_value)}; "
        f"tau² = {heterogeneity.tau_squared:.3g}, "
        f"I² = {100.0 * heterogeneity.i_squared:.1f}%"
    )


def _caption(result: CoefficientResult) -> str:
    meta = result.meta_analysis
    prediction = meta.prediction
    prediction_text = (
        f"prediction [{prediction.interval.low:.3g}, {prediction.interval.high:.3g}]"
        if prediction.interval is not None
        else f"prediction unavailable ({prediction.absence_reason})"
    )
    return (
        f"k = {result.retained_rows}; estimand: {meta.estimand}; scale: "
        f"{meta.effect_scale}; direction: {meta.effect_direction}; units: "
        f"{meta.effect_units}; {prediction_text}"
    )


def render_ggcoefstats(
    analysis: CoefficientAnalysis,
    *,
    title: str | None = None,
    results_subtitle: bool = True,
    show_intervals: bool = True,
    show_prediction: bool = True,
    x_label: str | None = None,
    point_color: str = "#4c78a8",
    pooled_color: str = "#e45756",
    theme: StatsTheme | None = None,
) -> StatsPlot[CoefficientResult]:
    """Render one typed M5B analysis without recomputing statistics."""

    for value, label in (
        (results_subtitle, "results_subtitle"),
        (show_intervals, "show_intervals"),
        (show_prediction, "show_prediction"),
    ):
        if type(value) is not bool:
            raise TypeError(f"{label} must be boolean")
    for value, label in ((point_color, "point_color"), (pooled_color, "pooled_color")):
        if not value or not is_color_like(value):
            raise ValueError(f"{label} must be a valid Matplotlib color")
    if title is not None and not title:
        raise ValueError("title must be nonempty when supplied")
    if x_label is not None and not x_label:
        raise ValueError("x_label must be nonempty when supplied")

    result = analysis.result
    figure = Figure(layout="constrained")
    axes = figure.subplots()
    renderer = cast(_CoefficientAxes, axes)
    count = len(result.terms)
    study_positions = tuple(float(count - index) for index in range(count))
    renderer.axvline(
        result.meta_analysis.null_value,
        color="#666666",
        linestyle="--",
        linewidth=1.0,
    )
    for term, position in zip(result.terms, study_positions, strict=True):
        interval = term.inference.interval
        xerr = (
            [[term.estimate - interval.low], [interval.high - term.estimate]]
            if show_intervals
            else None
        )
        renderer.errorbar(
            term.estimate,
            position,
            xerr=xerr,
            fmt="o",
            color=point_color,
            capsize=3.0,
            markersize=5.0,
            label=None,
            zorder=3,
        )
        visible = result.stats_labels and (
            not result.only_significant or term.inference.significant
        )
        if visible:
            renderer.text(
                1.01,
                position,
                f"{term.estimate:.3g} ({_p_text(term.inference.p_value)})",
                transform=axes.get_yaxis_transform(),
                ha="left",
                va="center",
                fontsize="small",
            )

    pooled = result.meta_analysis.pooled
    renderer.errorbar(
        pooled.estimate,
        0.0,
        xerr=[
            [pooled.estimate - pooled.interval.low],
            [pooled.interval.high - pooled.estimate],
        ],
        fmt="D",
        color=pooled_color,
        capsize=4.0,
        markersize=7.0,
        label="pooled confidence interval",
        zorder=4,
    )
    prediction = result.meta_analysis.prediction.interval
    if show_prediction and prediction is not None:
        renderer.hlines(
            0.0,
            prediction.low,
            prediction.high,
            color=pooled_color,
            linewidth=5.0,
            label="prediction interval",
            zorder=2,
        )
    renderer.set_yticks((*study_positions, 0.0), [*result.display_order, "Pooled"])
    renderer.set_ylim(-1.0, float(count + 1))
    renderer.set_xlabel(
        x_label
        or f"{result.meta_analysis.effect_scale} ({result.meta_analysis.effect_units})"
    )
    rendered_title = title or f"Meta-analysis of {result.meta_analysis.estimand}"
    renderer.set_title(rendered_title)
    renderer.legend(loc="best")
    subtitle = _subtitle(result)
    caption = _caption(result)
    if results_subtitle:
        renderer.text(
            0.5,
            1.01,
            subtitle,
            transform=axes.transAxes,
            ha="center",
            va="bottom",
        )
    figure_renderer = cast(_CoefficientFigure, figure)
    figure_renderer.text(0.01, 0.01, caption, ha="left", va="bottom", fontsize="small")
    figure_renderer.set_size_inches(
        8.0, min(24.0, max(4.8, 2.8 + 0.34 * count)), forward=True
    )
    (theme or theme_ggstatsplot()).apply(axes)
    return StatsPlot(
        figure,
        {"main": axes},
        result,
        PlotAnnotations(rendered_title, subtitle, caption),
    )


def ggcoefstats(
    data: pl.DataFrame,
    *,
    meta_analytic_effect: bool = False,
    estimand: str = "",
    effect_scale: str = "",
    effect_direction: str = "",
    effect_units: str = "",
    dependence: str = "independent",
    null_value: float = 0.0,
    conf_level: float = 0.95,
    stats_labels: bool = True,
    only_significant: bool = False,
    maximum_studies: int = 500,
    maximum_rendered_points: int = 500,
    maximum_labels: int = 200,
    title: str | None = None,
    results_subtitle: bool = True,
    show_intervals: bool = True,
    show_prediction: bool = True,
    x_label: str | None = None,
    point_color: str = "#4c78a8",
    pooled_color: str = "#e45756",
    theme: StatsTheme | None = None,
) -> StatsPlot[CoefficientResult]:
    """Analyze and render the explicit M5B meta-analysis mode."""

    analysis = analyze_ggcoefstats(
        data,
        meta_analytic_effect=meta_analytic_effect,
        estimand=estimand,
        effect_scale=effect_scale,
        effect_direction=effect_direction,
        effect_units=effect_units,
        dependence=dependence,
        null_value=null_value,
        conf_level=conf_level,
        stats_labels=stats_labels,
        only_significant=only_significant,
        maximum_studies=maximum_studies,
        maximum_rendered_points=maximum_rendered_points,
        maximum_labels=maximum_labels,
    )
    return render_ggcoefstats(
        analysis,
        title=title,
        results_subtitle=results_subtitle,
        show_intervals=show_intervals,
        show_prediction=show_prediction,
        x_label=x_label,
        point_color=point_color,
        pooled_color=pooled_color,
        theme=theme,
    )
