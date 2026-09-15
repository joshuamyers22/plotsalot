"""Semantic Matplotlib rendering for approved comparison analyses."""

from __future__ import annotations

from typing import Protocol, cast

import numpy as np
import polars as pl
from matplotlib.figure import Figure

from plotsalot.bayesian import DEFAULT_MAX_BAYESIAN_WORK
from plotsalot.bayesian_result import (
    BayesianComparisonResult,
    BayesianPairwiseComparisonResult,
)
from plotsalot.comparison_analysis import (
    DEFAULT_MAX_LEVELS,
    DEFAULT_MAX_RENDERED_OBSERVATIONS,
    DEFAULT_MAX_SUBJECT_PATHS,
    ComparisonAnalysis,
    analyze_ggbetweenstats,
    analyze_ggwithinstats,
)
from plotsalot.comparison_data import ComparisonSample, RepeatedSample
from plotsalot.comparison_result import (
    ComparisonResult,
    PairwiseComparisonResult,
)
from plotsalot.data import DEFAULT_MAX_ROWS, FloatArray
from plotsalot.plot import PlotAnnotations, StatsPlot
from plotsalot.result import SampleAudit
from plotsalot.robust import TRIM_FRACTION
from plotsalot.robust_result import (
    RobustComparisonResult,
    RobustPairwiseComparisonResult,
)
from plotsalot.theme import StatsTheme, theme_ggstatsplot


class _StyledArtist(Protocol):
    def set_alpha(self, alpha: float) -> None: ...

    def set_facecolor(self, color: str) -> None: ...


class _ComparisonAxes(Protocol):
    transAxes: object

    def violinplot(
        self,
        dataset: object,
        *,
        positions: object,
        widths: float,
        showmeans: bool,
        showmedians: bool,
        showextrema: bool,
    ) -> dict[str, list[_StyledArtist]]: ...

    def boxplot(
        self,
        values: object,
        *,
        positions: object,
        widths: float,
        patch_artist: bool,
        showfliers: bool,
    ) -> dict[str, list[_StyledArtist]]: ...

    def scatter(
        self,
        x: object,
        y: object,
        *,
        alpha: float,
        s: float,
        color: str,
        zorder: int,
    ) -> object: ...

    def errorbar(
        self,
        x: float,
        y: float,
        *,
        yerr: object,
        fmt: str,
        color: str,
        capsize: int,
        zorder: int,
    ) -> object: ...

    def plot(
        self,
        x: object,
        y: object,
        *,
        color: str,
        alpha: float = 1.0,
        linewidth: float,
        linestyle: str = "-",
        zorder: int = 2,
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

    def set_xlabel(self, label: str) -> object: ...

    def set_ylabel(self, label: str) -> object: ...

    def set_title(self, label: str) -> object: ...


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


def _displayed_pairwise(
    result: ComparisonResult | RobustComparisonResult | BayesianComparisonResult,
) -> tuple[
    PairwiseComparisonResult
    | RobustPairwiseComparisonResult
    | BayesianPairwiseComparisonResult,
    ...,
]:
    if result.pairwise_display == "none":
        return ()
    if result.pairwise_display == "all":
        return result.pairwise
    if isinstance(result, BayesianComparisonResult):
        return ()
    if result.pairwise_display == "significant":
        return tuple(item for item in result.pairwise if item.significant)
    return tuple(item for item in result.pairwise if not item.significant)


def _subtitle(
    result: ComparisonResult | RobustComparisonResult | BayesianComparisonResult,
) -> str:
    if isinstance(result, BayesianComparisonResult):
        return (
            f"{result.omnibus.display}; posterior medians with "
            f"{result.credible_level:.0%} equal-tail credible intervals"
        )
    test = result.omnibus
    effect = result.effect_size
    robust = isinstance(result, RobustComparisonResult)
    if test.df1 is None:
        if robust:
            if effect.value is None:
                raise ValueError("robust t result requires a raw difference")
            return (
                f"{test.name}: t({test.df2:.2f}) = {test.statistic:.2f}, "
                f"{_p_value_text(test.p_value)}; raw difference = "
                f"{effect.value:.2f}; standardized effect unavailable"
            )
        return (
            f"{test.name}: t({test.df2:.2f}) = {test.statistic:.2f}, "
            f"{_p_value_text(test.p_value)}; {effect.name} = {effect.value:.2f}"
        )
    correction = ""
    if result.correction is not None:
        correction_name = "robust epsilon" if robust else "GG epsilon"
        correction = f"; {correction_name} = {result.correction.epsilon:.3f}"
    if robust:
        return (
            f"{test.name}: F({test.df1:.2f}, {test.df2:.2f}) = "
            f"{test.statistic:.2f}, {_p_value_text(test.p_value)}; "
            f"standardized effect unavailable{correction}"
        )
    return (
        f"{test.name}: F({test.df1:.2f}, {test.df2:.2f}) = {test.statistic:.2f}, "
        f"{_p_value_text(test.p_value)}; {effect.name} = {effect.value:.2f}"
        f"{correction}"
    )


def _caption(
    result: ComparisonResult | RobustComparisonResult | BayesianComparisonResult,
) -> str:
    sample = result.sample
    if isinstance(sample, SampleAudit):
        caption = (
            f"n = {sample.analyzed_rows}; "
            f"{sample.dropped_null_rows} null row(s) excluded; "
            + (
                "pointwise Bayesian evidence"
                if isinstance(result, BayesianComparisonResult)
                else f"pairwise p adjustment: {result.p_adjust}"
            )
        )
    else:
        caption = (
            f"n = {sample.analyzed_subjects} complete subject(s); "
            f"{sample.excluded_incomplete_subjects} incomplete subject(s) excluded; "
            + (
                "pointwise Bayesian evidence"
                if isinstance(result, BayesianComparisonResult)
                else f"pairwise p adjustment: {result.p_adjust}"
            )
        )
    if isinstance(result, RobustComparisonResult):
        caption += "; 20% trimmed locations; pairwise CIs are pointwise"
    if isinstance(result, BayesianComparisonResult):
        caption += "; eight scrambled Sobol replicates; BF10 orientation H1/H0"
    return caption


def _draw_distributions(
    axes: _ComparisonAxes,
    values: tuple[FloatArray, ...],
    positions: FloatArray,
) -> None:
    variable_values: list[FloatArray] = []
    variable_positions: list[float] = []
    for position, level_values in zip(positions, values, strict=True):
        if float(np.std(level_values, ddof=1)) > 0.0:
            variable_values.append(level_values)
            variable_positions.append(float(position))
    if variable_values:
        violins = axes.violinplot(
            variable_values,
            positions=variable_positions,
            widths=0.72,
            showmeans=False,
            showmedians=False,
            showextrema=False,
        )
        for body in violins["bodies"]:
            body.set_alpha(0.2)
            body.set_facecolor("#4c78a8")
    boxes = axes.boxplot(
        values,
        positions=positions,
        widths=0.25,
        patch_artist=True,
        showfliers=False,
    )
    for box in boxes["boxes"]:
        box.set_alpha(0.35)
        box.set_facecolor("#9ecae1")

    for position, level_values in zip(positions, values, strict=True):
        offsets = np.linspace(-0.09, 0.09, level_values.size, dtype=np.float64)
        axes.scatter(
            np.full(level_values.size, position, dtype=np.float64) + offsets,
            level_values,
            alpha=0.45,
            s=18.0,
            color="#2f4b7c",
            zorder=3,
        )


def _draw_means(
    axes: _ComparisonAxes,
    analysis: ComparisonAnalysis,
    accent_color: str,
) -> None:
    for index, level in enumerate(analysis.result.levels, start=1):
        lower = level.mean - level.interval.low
        upper = level.interval.high - level.mean
        axes.errorbar(
            float(index),
            level.mean,
            yerr=np.array([[lower], [upper]]),
            fmt="o",
            color=accent_color,
            capsize=4,
            zorder=5,
        )


def _draw_pairwise(
    axes: _ComparisonAxes,
    result: ComparisonResult | RobustComparisonResult | BayesianComparisonResult,
    values: tuple[FloatArray, ...],
) -> None:
    displayed = _displayed_pairwise(result)
    if not displayed:
        return
    index = {
        (type(level.level), level.level): position
        for position, level in enumerate(result.levels, start=1)
    }
    observed_low = min(float(np.min(values_)) for values_ in values)
    observed_high = max(float(np.max(values_)) for values_ in values)
    span = observed_high - observed_low
    step = 0.08 * span if span > 0.0 else 1.0
    base = observed_high + step
    for bracket_index, item in enumerate(displayed):
        left = index[(type(item.left), item.left)]
        right = index[(type(item.right), item.right)]
        height = base + (bracket_index * step)
        tip = step * 0.25
        axes.plot(
            [left, left, right, right],
            [height - tip, height, height, height - tip],
            color="#333333",
            linewidth=0.8,
        )
        label = (
            item.evidence.display
            if isinstance(item, BayesianPairwiseComparisonResult)
            else _p_value_text(item.adjusted_p_value)
        )
        axes.text((left + right) / 2.0, height, label, ha="center", va="bottom")


def render_comparison(
    analysis: ComparisonAnalysis,
    *,
    title: str | None = None,
    results_subtitle: bool = True,
    show_subject_paths: bool = True,
    theme: StatsTheme | None = None,
) -> StatsPlot[ComparisonResult]:
    """Render an approved comparison without recomputing its statistics."""

    result = cast(
        ComparisonResult | RobustComparisonResult | BayesianComparisonResult,
        analysis.result,
    )
    if result.sample.analyzed_rows > cast(
        int, result.limits.maximum_rendered_observations
    ):
        raise ValueError(
            "analyzed sample exceeds maximum_rendered_observations="
            f"{result.limits.maximum_rendered_observations}"
        )
    if isinstance(analysis.sample, ComparisonSample):
        values = analysis.sample.values
    else:
        if show_subject_paths and analysis.sample.audit.analyzed_subjects > cast(
            int, result.limits.maximum_subject_paths
        ):
            raise ValueError(
                "complete subject count exceeds maximum_subject_paths="
                f"{result.limits.maximum_subject_paths}"
            )
        values = tuple(
            analysis.sample.values[:, index]
            for index in range(len(analysis.sample.conditions))
        )

    figure = Figure(layout="constrained")
    axes = figure.subplots()
    renderer = cast(_ComparisonAxes, axes)
    positions = np.arange(1, len(result.levels) + 1, dtype=np.float64)
    _draw_distributions(renderer, values, positions)
    if isinstance(analysis.sample, RepeatedSample) and show_subject_paths:
        for subject_values in analysis.sample.values:
            renderer.plot(
                positions,
                subject_values,
                color="#777777",
                alpha=0.28,
                linewidth=0.7,
                linestyle="--",
                zorder=1,
            )
    selected_theme = theme or theme_ggstatsplot()
    _draw_means(renderer, analysis, selected_theme.accent_color)
    _draw_pairwise(renderer, result, values)
    renderer.set_xticks(positions, [str(level.level) for level in result.levels])
    renderer.set_xlabel(result.x)
    renderer.set_ylabel(result.y)
    rendered_title = title or (
        f"{result.y} by {result.x}"
        if result.design == "between"
        else f"Repeated {result.y} by {result.x}"
    )
    renderer.set_title(rendered_title)
    subtitle = _subtitle(result)
    caption = _caption(result)
    if results_subtitle:
        renderer.text(
            0.5,
            1.01,
            subtitle,
            ha="center",
            va="bottom",
            transform=axes.transAxes,
        )
    cast(_FigureRenderer, figure).text(
        0.01, 0.01, caption, ha="left", va="bottom", fontsize="small"
    )
    selected_theme.apply(axes)
    return StatsPlot(
        figure=figure,
        axes={"main": axes},
        result=cast(ComparisonResult, result),
        annotations=PlotAnnotations(
            title=rendered_title,
            subtitle=subtitle,
            caption=caption,
        ),
    )


def render_ggbetweenstats(
    analysis: ComparisonAnalysis,
    *,
    title: str | None = None,
    results_subtitle: bool = True,
    theme: StatsTheme | None = None,
) -> StatsPlot[ComparisonResult]:
    """Render an approved independent-groups analysis."""

    if analysis.result.design != "between":
        raise ValueError("render_ggbetweenstats requires a between-group analysis")
    return render_comparison(
        analysis,
        title=title,
        results_subtitle=results_subtitle,
        show_subject_paths=False,
        theme=theme,
    )


def ggbetweenstats(
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
    prior_location: float | None = None,
    prior_scale: float | None = None,
    credible_level: float = 0.95,
    random_seed: int | None = None,
    maximum_bayesian_work: int = DEFAULT_MAX_BAYESIAN_WORK,
    title: str | None = None,
    results_subtitle: bool = True,
    theme: StatsTheme | None = None,
) -> StatsPlot[ComparisonResult]:
    """Analyze and render the approved Welch independent-groups method."""

    analysis = analyze_ggbetweenstats(
        data,
        x,
        y,
        type=type,
        alternative=alternative,
        conf_level=conf_level,
        p_adjust=p_adjust,
        pairwise_alpha=pairwise_alpha,
        pairwise_display=pairwise_display,
        maximum_rows=maximum_rows,
        maximum_levels=maximum_levels,
        maximum_rendered_observations=maximum_rendered_observations,
        trim_fraction=trim_fraction,
        prior_location=prior_location,
        prior_scale=prior_scale,
        credible_level=credible_level,
        random_seed=random_seed,
        maximum_bayesian_work=maximum_bayesian_work,
    )
    return render_ggbetweenstats(
        analysis,
        title=title,
        results_subtitle=results_subtitle,
        theme=theme,
    )


def render_ggwithinstats(
    analysis: ComparisonAnalysis,
    *,
    title: str | None = None,
    results_subtitle: bool = True,
    show_subject_paths: bool = True,
    theme: StatsTheme | None = None,
) -> StatsPlot[ComparisonResult]:
    """Render an approved repeated-measures analysis."""

    if analysis.result.design != "within":
        raise ValueError("render_ggwithinstats requires a repeated analysis")
    return render_comparison(
        analysis,
        title=title,
        results_subtitle=results_subtitle,
        show_subject_paths=show_subject_paths,
        theme=theme,
    )


def ggwithinstats(
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
    prior_location: float | None = None,
    prior_scale: float | None = None,
    credible_level: float = 0.95,
    random_seed: int | None = None,
    maximum_bayesian_work: int = DEFAULT_MAX_BAYESIAN_WORK,
    title: str | None = None,
    results_subtitle: bool = True,
    show_subject_paths: bool = True,
    theme: StatsTheme | None = None,
) -> StatsPlot[ComparisonResult]:
    """Analyze and render the approved explicit-subject repeated method."""

    analysis = analyze_ggwithinstats(
        data,
        x,
        y,
        subject_id=subject_id,
        type=type,
        alternative=alternative,
        conf_level=conf_level,
        p_adjust=p_adjust,
        pairwise_alpha=pairwise_alpha,
        pairwise_display=pairwise_display,
        maximum_rows=maximum_rows,
        maximum_levels=maximum_levels,
        maximum_rendered_observations=maximum_rendered_observations,
        maximum_subject_paths=maximum_subject_paths,
        trim_fraction=trim_fraction,
        prior_location=prior_location,
        prior_scale=prior_scale,
        credible_level=credible_level,
        random_seed=random_seed,
        maximum_bayesian_work=maximum_bayesian_work,
    )
    return render_ggwithinstats(
        analysis,
        title=title,
        results_subtitle=results_subtitle,
        show_subject_paths=show_subject_paths,
        theme=theme,
    )
