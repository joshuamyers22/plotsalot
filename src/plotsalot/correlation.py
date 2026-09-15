"""Matplotlib rendering for approved Pearson correlation analyses."""

from __future__ import annotations

from typing import Protocol, cast

import numpy as np
import polars as pl
from matplotlib.figure import Figure

from plotsalot.bayesian import DEFAULT_MAX_BAYESIAN_WORK
from plotsalot.bayesian_result import (
    BayesianCorrelationMatrixCell,
    BayesianCorrelationMatrixResult,
    BayesianCorrelationResult,
)
from plotsalot.correlation_analysis import (
    CorrelationAnalysis,
    CorrelationMatrixAnalysis,
    analyze_ggcorrmat,
    analyze_ggscatterstats,
)
from plotsalot.data import DEFAULT_MAX_ROWS, FloatArray
from plotsalot.plot import PlotAnnotations, StatsPlot
from plotsalot.result import CorrelationMatrixResult, CorrelationResult
from plotsalot.robust import (
    DEFAULT_BOOTSTRAP_RESAMPLES,
    DEFAULT_MAX_RESAMPLE_WORK,
    TRIM_FRACTION,
)
from plotsalot.robust_result import (
    RobustCorrelationMatrixResult,
    RobustCorrelationResult,
)


class _ScatterAxes(Protocol):
    transAxes: object

    def scatter(self, x: FloatArray, y: FloatArray, *, alpha: float) -> object: ...

    def set_xlabel(self, label: str) -> object: ...

    def set_ylabel(self, label: str) -> object: ...

    def set_title(self, label: str) -> object: ...

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


class _MatrixAxes(Protocol):
    def imshow(
        self, values: object, *, vmin: float, vmax: float, cmap: str
    ) -> object: ...

    def set_xticks(
        self,
        ticks: FloatArray,
        labels: tuple[str, ...],
        *,
        rotation: int,
        ha: str,
    ) -> object: ...

    def set_yticks(self, ticks: FloatArray, labels: tuple[str, ...]) -> object: ...

    def set_title(self, label: str) -> object: ...

    def text(
        self,
        x: int,
        y: int,
        text: str,
        *,
        ha: str,
        va: str,
        color: str,
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

    def colorbar(self, mappable: object, *, ax: object, label: str) -> object: ...


def _p_value_text(p_value: float) -> str:
    return "p < 0.001" if p_value < 0.001 else f"p = {p_value:.3f}"


def render_ggscatterstats(
    analysis: CorrelationAnalysis,
    *,
    title: str | None = None,
) -> StatsPlot[CorrelationResult]:
    """Render retained pairs and their typed correlation result."""

    result = cast(
        CorrelationResult | RobustCorrelationResult | BayesianCorrelationResult,
        analysis.result,
    )
    figure = Figure(layout="constrained")
    axes = figure.subplots()
    renderer = cast(_ScatterAxes, axes)
    renderer.scatter(analysis.sample.x_values, analysis.sample.y_values, alpha=0.6)
    renderer.set_xlabel(result.x)
    renderer.set_ylabel(result.y)
    rendered_title = title or f"{result.y} versus {result.x}"
    renderer.set_title(rendered_title)
    if isinstance(result, BayesianCorrelationResult):
        subtitle = (
            f"posterior median rho = {result.posterior.median:.2f}; "
            f"P(rho > 0) = {result.posterior.probability_above_null:.3f}; "
            f"{result.evidence.display}"
        )
        caption = (
            f"n = {result.sample.analyzed_rows} pairs; "
            f"{result.sample.dropped_null_rows} null row(s) excluded; pointwise "
            f"{result.interval.level:.0%} equal-tail credible interval "
            f"[{result.interval.low:.2f}, {result.interval.high:.2f}]; "
            "uniform prior on rho"
        )
    elif isinstance(result, RobustCorrelationResult):
        statistic_text = (
            "perfect correlation"
            if result.test.statistic is None
            else f"t({result.test.df}) = {result.test.statistic:.2f}"
        )
        subtitle = (
            f"{statistic_text}, {_p_value_text(result.test.p_value)}, "
            f"20% Winsorized r = {result.estimate:.2f}; h = {result.x_kernel.h}"
        )
        caption = (
            f"n = {result.sample.analyzed_rows} pairs; "
            f"{result.sample.dropped_null_rows} null row(s) excluded; pointwise "
            f"{result.interval.level:.0%} percentile CI "
            f"[{result.interval.low:.2f}, {result.interval.high:.2f}]; "
            f"B = {result.resampling.valid_replicates}/"
            f"{result.resampling.requested_replicates}"
        )
    else:
        statistic_text = (
            "perfect correlation"
            if result.test.statistic is None
            else f"t({result.test.df}) = {result.test.statistic:.2f}"
        )
        subtitle = (
            f"{statistic_text}, {_p_value_text(result.test.p_value)}, "
            f"Pearson r = {result.estimate:.2f}"
        )
        caption = (
            f"n = {result.sample.analyzed_rows} pairs; "
            f"{result.sample.dropped_null_rows} null row(s) excluded; "
            f"{result.interval.level:.0%} Fisher CI "
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
        result=cast(CorrelationResult, result),
        annotations=PlotAnnotations(
            title=rendered_title,
            subtitle=subtitle,
            caption=caption,
        ),
    )


def ggscatterstats(
    data: pl.DataFrame,
    x: str,
    y: str,
    *,
    conf_level: float = 0.95,
    maximum_rows: int = DEFAULT_MAX_ROWS,
    type: str = "parametric",
    trim_fraction: float = TRIM_FRACTION,
    bootstrap_resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
    random_seed: int | None = None,
    maximum_resample_work: int = DEFAULT_MAX_RESAMPLE_WORK,
    correlation_prior_shape: float = 1.0,
    credible_level: float = 0.95,
    maximum_bayesian_work: int = DEFAULT_MAX_BAYESIAN_WORK,
    title: str | None = None,
) -> StatsPlot[CorrelationResult]:
    """Analyze and render an approved classical, robust, or Bayesian scatter."""

    analysis = analyze_ggscatterstats(
        data,
        x,
        y,
        conf_level=conf_level,
        maximum_rows=maximum_rows,
        type=type,
        trim_fraction=trim_fraction,
        bootstrap_resamples=bootstrap_resamples,
        random_seed=random_seed,
        maximum_resample_work=maximum_resample_work,
        correlation_prior_shape=correlation_prior_shape,
        credible_level=credible_level,
        maximum_bayesian_work=maximum_bayesian_work,
    )
    return render_ggscatterstats(analysis, title=title)


def render_ggcorrmat(
    analysis: CorrelationMatrixAnalysis,
    *,
    title: str | None = None,
) -> StatsPlot[CorrelationMatrixResult]:
    """Render a semantic heatmap from a typed correlation-matrix result."""

    result = cast(
        CorrelationMatrixResult
        | RobustCorrelationMatrixResult
        | BayesianCorrelationMatrixResult,
        analysis.result,
    )
    index = {column: position for position, column in enumerate(result.columns)}
    estimates = np.empty((len(result.columns), len(result.columns)))
    for cell in result.cells:
        estimates[index[cell.y], index[cell.x]] = cell.estimate

    figure = Figure(layout="constrained")
    axes = figure.subplots()
    renderer = cast(_MatrixAxes, axes)
    image = renderer.imshow(estimates, vmin=-1.0, vmax=1.0, cmap="coolwarm")
    bayesian = isinstance(result, BayesianCorrelationMatrixResult)
    robust = isinstance(result, RobustCorrelationMatrixResult)
    correlation_label = (
        "posterior median rho"
        if bayesian
        else ("20% Winsorized r" if robust else "Pearson r")
    )
    cast(_FigureRenderer, figure).colorbar(image, ax=axes, label=correlation_label)
    ticks = np.arange(len(result.columns), dtype=np.float64)
    renderer.set_xticks(ticks, result.columns, rotation=45, ha="right")
    renderer.set_yticks(ticks, result.columns)
    for cell in result.cells:
        marker = "" if cell.significant is not False else " ×"
        text = f"{cell.estimate:.2f}{marker}"
        if (
            isinstance(cell, BayesianCorrelationMatrixCell)
            and cell.evidence is not None
        ):
            text = f"{cell.estimate:.2f}\n{cell.evidence.display}"
        renderer.text(
            index[cell.x],
            index[cell.y],
            text,
            ha="center",
            va="center",
            color="black",
        )

    rendered_title = title or (
        "Bayesian Pearson correlation matrix"
        if bayesian
        else (
            "20% Winsorized correlation matrix"
            if robust
            else "Pearson correlation matrix"
        )
    )
    renderer.set_title(rendered_title)
    unique_pairs = len(result.columns) * (len(result.columns) - 1) // 2
    if bayesian:
        subtitle = f"{unique_pairs} pointwise Bayesian pair(s); no p adjustment"
        caption = (
            "Cells show posterior median rho and numeric BF10; "
            "pairwise-complete samples and pointwise equal-tail intervals"
        )
    else:
        subtitle = f"{unique_pairs} pair(s); p adjustment: {result.p_adjust}"
        p_label = "Holm-adjusted p" if result.p_adjust == "holm" else "p"
        caption = f"× = {p_label} > {result.sig_level:g}; pairwise-complete samples"
    if robust:
        caption += "; pointwise percentile intervals; deterministic PCG64DXSM"
    return StatsPlot(
        figure=figure,
        axes={"main": axes},
        result=cast(CorrelationMatrixResult, result),
        annotations=PlotAnnotations(
            title=rendered_title,
            subtitle=subtitle,
            caption=caption,
        ),
    )


def ggcorrmat(
    data: pl.DataFrame,
    columns: list[str] | tuple[str, ...],
    *,
    conf_level: float = 0.95,
    sig_level: float = 0.05,
    p_adjust: str = "holm",
    maximum_rows: int = DEFAULT_MAX_ROWS,
    type: str = "parametric",
    trim_fraction: float = TRIM_FRACTION,
    bootstrap_resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
    random_seed: int | None = None,
    maximum_resample_work: int = DEFAULT_MAX_RESAMPLE_WORK,
    correlation_prior_shape: float = 1.0,
    credible_level: float = 0.95,
    maximum_bayesian_work: int = DEFAULT_MAX_BAYESIAN_WORK,
    title: str | None = None,
) -> StatsPlot[CorrelationMatrixResult]:
    """Analyze and render an approved classical, robust, or Bayesian matrix."""

    analysis = analyze_ggcorrmat(
        data,
        columns,
        conf_level=conf_level,
        sig_level=sig_level,
        p_adjust=p_adjust,
        maximum_rows=maximum_rows,
        type=type,
        trim_fraction=trim_fraction,
        bootstrap_resamples=bootstrap_resamples,
        random_seed=random_seed,
        maximum_resample_work=maximum_resample_work,
        correlation_prior_shape=correlation_prior_shape,
        credible_level=credible_level,
        maximum_bayesian_work=maximum_bayesian_work,
    )
    return render_ggcorrmat(analysis, title=title)
