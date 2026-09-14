"""Semantic Matplotlib renderers for approved categorical analyses."""

from __future__ import annotations

from collections.abc import Mapping
from textwrap import wrap
from typing import Protocol, cast

import numpy as np
import polars as pl
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from plotsalot.categorical_analysis import (
    DEFAULT_MAX_LABELS,
    CategoricalAnalysis,
    analyze_categorical,
)
from plotsalot.categorical_data import (
    DEFAULT_MAX_CELLS,
    DEFAULT_MAX_LEVELS,
    DEFAULT_MAX_TOTAL_COUNT,
)
from plotsalot.categorical_result import CategoricalResult
from plotsalot.data import DEFAULT_MAX_ROWS
from plotsalot.plot import PlotAnnotations, StatsPlot
from plotsalot.result import ScalarIdentity
from plotsalot.theme import StatsTheme, theme_ggstatsplot

COLORS = (
    "#4c78a8",
    "#f58518",
    "#e45756",
    "#72b7b2",
    "#54a24b",
    "#eeca3b",
    "#b279a2",
    "#ff9da6",
    "#9d755d",
    "#bab0ac",
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#7f7f7f",
    "#bcbd22",
    "#17becf",
)


class _CategoricalAxes(Protocol):
    transAxes: object

    def bar(
        self,
        x: object,
        height: object,
        *,
        bottom: object,
        color: str,
        label: str,
        edgecolor: str,
    ) -> object: ...

    def text(
        self,
        x: float,
        y: float,
        text: str,
        *,
        ha: str,
        va: str,
        transform: object | None = None,
    ) -> object: ...

    def set_xticks(self, ticks: object, labels: list[str]) -> object: ...

    def set_ylim(self, low: float, high: float) -> object: ...

    def set_ylabel(self, label: str) -> object: ...

    def set_xlabel(self, label: str) -> object: ...

    def legend(
        self,
        *,
        title: str,
        handles: list[object] | None = None,
    ) -> object: ...

    def set_title(self, label: str) -> object: ...

    def pie(
        self,
        values: object,
        *,
        labels: list[str],
        colors: list[str],
        wedgeprops: dict[str, str],
    ) -> object: ...

    def plot(
        self,
        x: list[float],
        y: list[float],
        *,
        marker: str,
        linestyle: str,
        color: str,
        label: str,
    ) -> list[object]: ...


class _FigureRenderer(Protocol):
    def text(
        self,
        x: float,
        y: float,
        text: str,
        *,
        ha: str,
        va: str,
        fontsize: str | None = None,
    ) -> object: ...

    def suptitle(self, title: str) -> object: ...

    def set_size_inches(
        self, width: float, height: float, *, forward: bool
    ) -> object: ...


def _color_map(
    levels: tuple[ScalarIdentity, ...],
) -> dict[tuple[type[object], ScalarIdentity], str]:
    if len(levels) > len(COLORS):
        raise ValueError("categorical palette does not contain enough colors")
    return {(type(level), level): COLORS[index] for index, level in enumerate(levels)}


def _matrix(result: CategoricalResult) -> np.ndarray:
    rows, columns = len(result.x_levels), max(1, len(result.y_levels))
    return np.array([cell.observed for cell in result.cells], dtype=np.int64).reshape(
        rows, columns
    )


def _label(value: int, proportion: float, mode: str) -> str:
    if mode == "count":
        return str(value)
    if mode == "percentage":
        return f"{100.0 * proportion:.0f}%"
    if mode == "both":
        return f"{value} ({100.0 * proportion:.0f}%)"
    return ""


def _subtitle(result: CategoricalResult) -> str:
    test = result.omnibus
    effect = result.effect
    p_text = "p < 0.001" if test.p_value < 0.001 else f"p = {test.p_value:.3f}"
    return (
        f"{test.name}: statistic = {test.statistic:.2f}, df = {test.df:.0f}, "
        f"{p_text}; {effect.name} = {effect.value:.2f}"
    )


def _caption(result: CategoricalResult) -> str:
    base = (
        f"N = {result.sample.weighted_total}; "
        f"{result.sample.input_rows - result.sample.analyzed_rows} "
        "null row(s) excluded; "
        f"p adjustment: {result.p_adjust}"
    )
    if result.pairwise_display == "none":
        displayed = ()
    elif result.pairwise_display == "all":
        displayed = result.pairwise
    elif result.pairwise_display == "significant":
        displayed = tuple(item for item in result.pairwise if item.significant)
    else:
        displayed = tuple(item for item in result.pairwise if not item.significant)
    caption = base
    if displayed:
        pairwise = ", ".join(
            f"{item.left} vs {item.right}: {result.p_adjust} "
            f"p={item.adjusted_p_value:.3f}"
            for item in displayed
        )
        caption = f"{base}; pairwise: {pairwise}"
    return "\n".join(wrap(caption, width=110, break_long_words=False))


def render_ggbarstats(
    analysis: CategoricalAnalysis,
    *,
    label: str = "percentage",
    title: str | None = None,
    results_subtitle: bool = True,
    theme: StatsTheme | None = None,
    color_domain: tuple[ScalarIdentity, ...] | None = None,
) -> StatsPlot[CategoricalResult]:
    if label not in {"percentage", "count", "both", "none"}:
        raise ValueError("label must be percentage, count, both, or none")
    result = analysis.result
    observed = _matrix(result)
    totals = observed.sum(axis=0)
    proportions = observed / totals
    colors = _color_map(color_domain or result.x_levels)
    figure = Figure(layout="constrained")
    axes = figure.subplots()
    renderer = cast(_CategoricalAxes, axes)
    positions = np.arange(observed.shape[1], dtype=np.float64)
    bottoms = np.zeros(observed.shape[1])
    for row, level in enumerate(result.x_levels):
        values = proportions[row]
        renderer.bar(
            positions,
            values,
            bottom=bottoms,
            color=colors[(type(level), level)],
            label=str(level),
            edgecolor="white",
        )
        if label != "none":
            for column, value in enumerate(values):
                if observed[row, column] > 0:
                    renderer.text(
                        float(column),
                        float(bottoms[column] + value / 2.0),
                        _label(int(observed[row, column]), float(value), label),
                        ha="center",
                        va="center",
                    )
        bottoms += values
    labels = (
        ["all"]
        if result.design == "one_way"
        else [str(value) for value in result.y_levels]
    )
    renderer.set_xticks(positions, labels)
    renderer.set_ylim(0.0, 1.16 if result.strata else 1.08)
    renderer.set_ylabel("proportion")
    renderer.set_xlabel(result.y or "sample")
    renderer.legend(title=result.x)
    for index, total in enumerate(totals):
        renderer.text(float(index), 1.01, f"N={int(total)}", ha="center", va="bottom")
    if result.strata:
        for index, item in enumerate(result.strata):
            renderer.text(
                float(index),
                1.07,
                f"{result.p_adjust} p={item.adjusted_p_value:.3f}",
                ha="center",
                va="bottom",
            )
    rendered_title = title or (
        f"{result.x} proportions" if result.y is None else f"{result.x} by {result.y}"
    )
    renderer.set_title(rendered_title)
    subtitle, caption = _subtitle(result), _caption(result)
    figure_renderer = cast(_FigureRenderer, figure)
    figure_renderer.set_size_inches(
        max(6.4, 1.2 * observed.shape[1]),
        6.0 + 0.22 * caption.count("\n"),
        forward=True,
    )
    if results_subtitle:
        renderer.text(
            0.5, 1.01, subtitle, transform=axes.transAxes, ha="center", va="bottom"
        )
    figure_renderer.text(0.01, 0.01, caption, ha="left", va="bottom", fontsize="small")
    (theme or theme_ggstatsplot()).apply(axes)
    return StatsPlot(
        figure,
        {"main": axes},
        result,
        PlotAnnotations(rendered_title, subtitle, caption),
    )


def render_ggpiestats(
    analysis: CategoricalAnalysis,
    *,
    label: str = "percentage",
    title: str | None = None,
    results_subtitle: bool = True,
    theme: StatsTheme | None = None,
    color_domain: tuple[ScalarIdentity, ...] | None = None,
) -> StatsPlot[CategoricalResult]:
    if label not in {"percentage", "count", "both", "none"}:
        raise ValueError("label must be percentage, count, both, or none")
    result = analysis.result
    observed = _matrix(result)
    colors = _color_map(color_domain or result.x_levels)
    figure = Figure(layout="constrained")
    axes_grid = figure.subplots(1, observed.shape[1], squeeze=False)
    raw_axes = cast(list[Axes], axes_grid.ravel().tolist())
    axes_map: dict[str, Axes] = {}
    for column, raw_axis in enumerate(raw_axes):
        axes = raw_axis
        renderer = cast(_CategoricalAxes, axes)
        values = observed[:, column]
        labels = [
            _label(int(value), float(value / values.sum()), label) if value > 0 else ""
            for value in values
        ]
        renderer.pie(
            values,
            labels=labels,
            colors=[colors[(type(level), level)] for level in result.x_levels],
            wedgeprops={"edgecolor": "white"},
        )
        facet = "all" if result.y is None else str(result.y_levels[column])
        renderer.set_title(f"{facet}\nN={int(values.sum())}")
        if result.strata:
            item = result.strata[column]
            renderer.text(
                0.0,
                -1.18,
                f"{result.p_adjust} p={item.adjusted_p_value:.3f}",
                ha="center",
                va="top",
            )
        (theme or theme_ggstatsplot()).apply(axes)
        axes_map[f"facet_{column + 1}"] = axes
    handles = [
        cast(_CategoricalAxes, axes_map["facet_1"]).plot(
            [],
            [],
            marker="s",
            linestyle="",
            color=colors[(type(level), level)],
            label=str(level),
        )[0]
        for level in result.x_levels
    ]
    cast(_CategoricalAxes, axes_map["facet_1"]).legend(handles=handles, title=result.x)
    rendered_title = title or (
        f"{result.x} proportions" if result.y is None else f"{result.x} by {result.y}"
    )
    figure_renderer = cast(_FigureRenderer, figure)
    subtitle, caption = _subtitle(result), _caption(result)
    figure_renderer.set_size_inches(
        max(6.4, min(24.0, 3.0 * observed.shape[1])),
        6.0 + 0.22 * caption.count("\n"),
        forward=True,
    )
    figure_renderer.suptitle(rendered_title)
    if results_subtitle:
        figure_renderer.text(0.5, 0.965, subtitle, ha="center", va="top")
    figure_renderer.text(0.01, 0.01, caption, ha="left", va="bottom", fontsize="small")
    return StatsPlot(
        figure, axes_map, result, PlotAnnotations(rendered_title, subtitle, caption)
    )


def ggbarstats(
    data: pl.DataFrame,
    x: str,
    y: str | None = None,
    *,
    counts: str | None = None,
    type: str = "parametric",
    paired: bool = False,
    ratio: Mapping[ScalarIdentity, float] | None = None,
    alternative: str = "two-sided",
    conf_level: float = 0.95,
    p_adjust: str = "holm",
    alpha: float = 0.05,
    pairwise_display: str = "significant",
    proportion_test: bool = True,
    label: str = "percentage",
    maximum_rows: int = DEFAULT_MAX_ROWS,
    maximum_levels: int = DEFAULT_MAX_LEVELS,
    maximum_cells: int = DEFAULT_MAX_CELLS,
    maximum_total_count: int = DEFAULT_MAX_TOTAL_COUNT,
    maximum_labels: int = DEFAULT_MAX_LABELS,
    title: str | None = None,
    results_subtitle: bool = True,
    theme: StatsTheme | None = None,
) -> StatsPlot[CategoricalResult]:
    analysis = analyze_categorical(
        data,
        x,
        y,
        counts=counts,
        type=type,
        paired=paired,
        ratio=ratio,
        alternative=alternative,
        conf_level=conf_level,
        p_adjust=p_adjust,
        alpha=alpha,
        pairwise_display=pairwise_display,
        proportion_test=proportion_test,
        maximum_rows=maximum_rows,
        maximum_levels=maximum_levels,
        maximum_cells=maximum_cells,
        maximum_total_count=maximum_total_count,
        maximum_labels=maximum_labels,
    )
    return render_ggbarstats(
        analysis,
        label=label,
        title=title,
        results_subtitle=results_subtitle,
        theme=theme,
    )


def ggpiestats(
    data: pl.DataFrame,
    x: str,
    y: str | None = None,
    *,
    counts: str | None = None,
    type: str = "parametric",
    paired: bool = False,
    ratio: Mapping[ScalarIdentity, float] | None = None,
    alternative: str = "two-sided",
    conf_level: float = 0.95,
    p_adjust: str = "holm",
    alpha: float = 0.05,
    pairwise_display: str = "significant",
    proportion_test: bool = True,
    label: str = "percentage",
    maximum_rows: int = DEFAULT_MAX_ROWS,
    maximum_levels: int = DEFAULT_MAX_LEVELS,
    maximum_cells: int = DEFAULT_MAX_CELLS,
    maximum_total_count: int = DEFAULT_MAX_TOTAL_COUNT,
    maximum_labels: int = DEFAULT_MAX_LABELS,
    title: str | None = None,
    results_subtitle: bool = True,
    theme: StatsTheme | None = None,
) -> StatsPlot[CategoricalResult]:
    analysis = analyze_categorical(
        data,
        x,
        y,
        counts=counts,
        type=type,
        paired=paired,
        ratio=ratio,
        alternative=alternative,
        conf_level=conf_level,
        p_adjust=p_adjust,
        alpha=alpha,
        pairwise_display=pairwise_display,
        proportion_test=proportion_test,
        maximum_rows=maximum_rows,
        maximum_levels=maximum_levels,
        maximum_cells=maximum_cells,
        maximum_total_count=maximum_total_count,
        maximum_labels=maximum_labels,
    )
    return render_ggpiestats(
        analysis,
        label=label,
        title=title,
        results_subtitle=results_subtitle,
        theme=theme,
    )
