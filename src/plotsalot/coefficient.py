"""Semantic Matplotlib renderer for M5 coefficient and meta-analysis results."""

from __future__ import annotations

from textwrap import fill
from typing import Literal, Protocol, cast

from matplotlib.colors import is_color_like
from matplotlib.figure import Figure

from plotsalot.coefficient_analysis import CoefficientAnalysis, analyze_ggcoefstats
from plotsalot.coefficient_meta_analysis import (
    DEFAULT_MAXIMUM_WORK,
    BayesianMetaAnalysis,
    RobustMetaAnalysis,
)
from plotsalot.coefficient_meta_result import BayesianMetaResult, RobustMetaResult
from plotsalot.coefficient_result import CoefficientResult, CoefficientTableResult
from plotsalot.coefficient_summary_analysis import (
    PosteriorCoefficientTableResult,
    ReportedCoefficientAnalysis,
    RobustCoefficientTableResult,
)
from plotsalot.coefficient_table_analysis import TableCoefficientAnalysis
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
    def suptitle(self, label: str, *, y: float) -> object: ...

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

    def subplots_adjust(
        self,
        *,
        left: float,
        right: float,
        bottom: float,
        top: float,
    ) -> None: ...


def _p_text(value: float) -> str:
    return "p < 0.001" if value < 0.001 else f"p = {value:.3f}"


def _validate_analysis_type(analysis: object) -> None:
    if not isinstance(
        analysis,
        (
            CoefficientAnalysis,
            TableCoefficientAnalysis,
            ReportedCoefficientAnalysis,
            RobustMetaAnalysis,
            BayesianMetaAnalysis,
        ),
    ):
        raise TypeError("analysis must be an approved coefficient analysis")


def _finalize_m6c_figure(
    figure: Figure,
    renderer: _CoefficientAxes,
    *,
    title: str,
    subtitle: str,
    caption: str,
    results_subtitle: bool,
    stats_labels: bool,
    height: float,
) -> None:
    figure_renderer = cast(_CoefficientFigure, figure)
    figure_renderer.suptitle(title, y=0.98)
    if results_subtitle:
        renderer.text(
            0.5,
            1.03,
            fill(subtitle, width=96),
            transform=renderer.transAxes,
            ha="center",
            va="bottom",
            fontsize="small",
        )
    figure_renderer.text(
        0.01,
        0.015,
        fill(caption, width=118),
        ha="left",
        va="bottom",
        fontsize="x-small",
    )
    figure_renderer.set_size_inches(9.6, height, forward=True)
    figure_renderer.subplots_adjust(
        left=0.16,
        right=0.64 if stats_labels else 0.95,
        bottom=0.19,
        top=0.78,
    )


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


def _identity_label(result: CoefficientTableResult, index: int) -> str:
    identity = result.terms[index].identity
    values = tuple(
        value
        for value in (
            identity.response,
            identity.component,
            identity.group,
            identity.term,
        )
        if value is not None
    )
    return " | ".join(values)


def _coefficient_subtitle(result: CoefficientTableResult) -> str:
    source = (
        "reported table" if result.source_kind == "table" else "fitted Statsmodels OLS"
    )
    if result.inference_profile == "estimate_only":
        return f"{source}; estimates only; no interval or test inference"
    if result.inference_profile == "interval":
        return (
            f"{source}; reported {result.conf_level:.0%} confidence intervals; no tests"
        )
    kind = "Student-t" if result.inference_profile == "full_t" else "normal"
    return f"{source}; {kind} coefficient inference; two-sided unadjusted p-values"


def _coefficient_caption(result: CoefficientTableResult) -> str:
    text = (
        f"n terms = {result.retained_rows}; estimate: {result.estimate_label}; "
        f"scale: {result.effect_scale}; direction: {result.effect_direction}; "
        f"units: {result.effect_units}; excluded intercepts: "
        f"{len(result.excluded_intercepts)}"
    )
    model = result.model_summary
    if model is not None:
        aic = f"{model.aic:.3g}" if model.aic is not None else "unavailable"
        bic = f"{model.bic:.3g}" if model.bic is not None else "unavailable"
        text += (
            f"; OLS {model.covariance_type}, n = {model.nobs}, AIC = {aic}, BIC = {bic}"
        )
    return text


def _reported_identity_label(
    result: RobustCoefficientTableResult | PosteriorCoefficientTableResult,
    index: int,
) -> str:
    identity = result.terms[index].identity
    values = tuple(
        value
        for value in (
            identity.response,
            identity.component,
            identity.group,
            identity.term,
        )
        if value is not None
    )
    return " | ".join(values)


def _reported_coefficient_annotations(
    result: RobustCoefficientTableResult | PosteriorCoefficientTableResult,
) -> tuple[str, str]:
    common = (
        f"n terms = {result.retained_rows}; estimate: {result.estimate_label}; "
        f"scale: {result.effect_scale}; direction: {result.effect_direction}; "
        f"units: {result.effect_units}; excluded intercepts: "
        f"{len(result.excluded_intercepts)}"
    )
    if isinstance(result, RobustCoefficientTableResult):
        subtitle = (
            f"Caller-reported unverified robust summaries; "
            f"{result.conf_level:.0%} confidence intervals"
        )
        caption = (
            f"{common}; method: {result.provenance.robust_method}; tuning: "
            f"{result.provenance.robust_tuning}; interval method: "
            f"{result.provenance.interval_method}"
        )
        return subtitle, caption
    subtitle = (
        f"Caller-reported unverified posterior summaries; "
        f"{result.credible_level:.0%} equal-tail credible intervals"
    )
    caption = (
        f"{common}; model: {result.provenance.posterior_model}; likelihood: "
        f"{result.provenance.likelihood}; prior: "
        f"{result.provenance.prior_description}; computation: "
        f"{result.provenance.computation_method}"
    )
    return subtitle, caption


def _render_reported_coefficients(
    analysis: ReportedCoefficientAnalysis,
    *,
    title: str | None,
    results_subtitle: bool,
    show_intervals: bool,
    x_label: str | None,
    point_color: str,
    theme: StatsTheme | None,
) -> StatsPlot[RobustCoefficientTableResult | PosteriorCoefficientTableResult]:
    result = analysis.result
    figure = Figure()
    axes = figure.subplots()
    renderer = cast(_CoefficientAxes, axes)
    count = len(result.terms)
    positions = tuple(float(count - index) for index in range(count))
    renderer.axvline(result.null_value, color="#666666", linestyle="--", linewidth=1.0)
    if isinstance(result, RobustCoefficientTableResult):
        for term, position in zip(result.terms, positions, strict=True):
            point = term.estimate
            interval = term.interval
            label = (
                f"estimate = {point:.3g}; {result.conf_level:.0%} CI "
                f"[{interval.low:.3g}, {interval.high:.3g}]"
            )
            xerr = (
                [[point - interval.low], [interval.high - point]]
                if show_intervals
                else None
            )
            renderer.errorbar(
                point,
                position,
                xerr=xerr,
                fmt="o",
                color=point_color,
                capsize=3.0,
                markersize=5.0,
                label=None,
                zorder=3,
            )
            if result.stats_labels:
                renderer.text(
                    1.01,
                    position,
                    label,
                    transform=axes.get_yaxis_transform(),
                    ha="left",
                    va="center",
                    fontsize="small",
                )
    else:
        for term, position in zip(result.terms, positions, strict=True):
            point = term.summary.median
            interval = term.summary.interval
            label = (
                f"median = {point:.3g}; {result.credible_level:.0%} CrI "
                f"[{interval.low:.3g}, {interval.high:.3g}]\n"
                f"P(>{result.null_value:.3g}) = "
                f"{term.summary.probability_above_null:.3f}, "
                f"P(<{result.null_value:.3g}) = "
                f"{term.summary.probability_below_null:.3f}\n"
                f"P(={result.null_value:.3g}) = "
                f"{term.summary.probability_at_null:.3f}"
            )
            xerr = (
                [[point - interval.low], [interval.high - point]]
                if show_intervals
                else None
            )
            renderer.errorbar(
                point,
                position,
                xerr=xerr,
                fmt="o",
                color=point_color,
                capsize=3.0,
                markersize=5.0,
                label=None,
                zorder=3,
            )
            if result.stats_labels:
                renderer.text(
                    1.01,
                    position,
                    label,
                    transform=axes.get_yaxis_transform(),
                    ha="left",
                    va="center",
                    fontsize="small",
                )
    renderer.set_yticks(
        positions, [_reported_identity_label(result, index) for index in range(count)]
    )
    renderer.set_ylim(0.5, float(count) + 0.5)
    renderer.set_xlabel(x_label or f"{result.estimate_label} ({result.effect_units})")
    rendered_title = title or (
        "Robust coefficient summaries"
        if isinstance(result, RobustCoefficientTableResult)
        else "Posterior coefficient summaries"
    )
    subtitle, caption = _reported_coefficient_annotations(result)
    (theme or theme_ggstatsplot()).apply(axes)
    _finalize_m6c_figure(
        figure,
        renderer,
        title=rendered_title,
        subtitle=subtitle,
        caption=caption,
        results_subtitle=results_subtitle,
        stats_labels=result.stats_labels,
        height=min(24.0, max(4.8, 2.5 + 0.34 * count)),
    )
    return StatsPlot(
        figure,
        {"main": axes},
        result,
        PlotAnnotations(rendered_title, subtitle, caption),
    )


def _robust_meta_annotations(result: RobustMetaResult) -> tuple[str, str]:
    pooled = result.meta_analysis.pooled
    subtitle = (
        f"Student-t4 ML: pooled = {pooled.estimate:.3g}, "
        f"{result.conf_level:.0%} profile CI [{pooled.interval.low:.3g}, "
        f"{pooled.interval.high:.3g}], LR chi²(1) = {pooled.statistic:.3g}, "
        f"{_p_text(pooled.p_value)}; "
        f"tau² = {pooled.tau_squared:.3g}"
    )
    warnings = ", ".join(result.warnings) if result.warnings else "none"
    caption = (
        f"k = {result.retained_rows}; estimand: {result.meta_analysis.estimand}; "
        f"scale: {result.meta_analysis.effect_scale}; direction: "
        f"{result.meta_analysis.effect_direction}; units: "
        f"{result.meta_analysis.effect_units}; heterogeneity Q/I² unavailable "
        f"({pooled.heterogeneity_absence_reason}); prediction unavailable "
        f"({pooled.prediction_absence_reason}); selected start: "
        f"{result.convergence.selected_start}; work: {result.work.actual_work}/"
        f"{result.work.reserved_work}; warnings: {warnings}"
    )
    return subtitle, caption


def _render_robust_meta(
    analysis: RobustMetaAnalysis,
    *,
    title: str | None,
    results_subtitle: bool,
    show_intervals: bool,
    x_label: str | None,
    point_color: str,
    pooled_color: str,
    theme: StatsTheme | None,
) -> StatsPlot[RobustMetaResult]:
    result = analysis.result
    figure = Figure()
    axes = figure.subplots()
    renderer = cast(_CoefficientAxes, axes)
    count = len(result.studies)
    positions = tuple(float(count - index) for index in range(count))
    renderer.axvline(
        result.meta_analysis.null_value,
        color="#666666",
        linestyle="--",
        linewidth=1.0,
    )
    for study, position in zip(result.studies, positions, strict=True):
        interval = study.sampling_interval
        renderer.errorbar(
            study.estimate,
            position,
            xerr=(
                [
                    [study.estimate - interval.low],
                    [interval.high - study.estimate],
                ]
                if show_intervals
                else None
            ),
            fmt="o",
            color=point_color,
            capsize=3.0,
            markersize=5.0,
            label=None,
            zorder=3,
        )
        if result.stats_labels:
            renderer.text(
                1.01,
                position,
                f"estimate = {study.estimate:.3g}; latent precision = "
                f"{study.latent_precision:.3g}",
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
        label="pooled profile-likelihood confidence interval",
        zorder=4,
    )
    renderer.set_yticks((*positions, 0.0), [*result.display_order, "Pooled"])
    renderer.set_ylim(-1.0, float(count + 1))
    renderer.set_xlabel(
        x_label
        or f"{result.meta_analysis.effect_scale} ({result.meta_analysis.effect_units})"
    )
    rendered_title = title or f"Robust meta-analysis of {result.meta_analysis.estimand}"
    renderer.legend(loc="best")
    subtitle, caption = _robust_meta_annotations(result)
    (theme or theme_ggstatsplot()).apply(axes)
    _finalize_m6c_figure(
        figure,
        renderer,
        title=rendered_title,
        subtitle=subtitle,
        caption=caption,
        results_subtitle=results_subtitle,
        stats_labels=result.stats_labels,
        height=min(24.0, max(4.8, 2.8 + 0.34 * count)),
    )
    return StatsPlot(
        figure,
        {"main": axes},
        result,
        PlotAnnotations(rendered_title, subtitle, caption),
    )


def _bayesian_meta_annotations(result: BayesianMetaResult) -> tuple[str, str]:
    primary = result.primary
    mean = primary.population_mean
    tau = primary.tau
    prediction = primary.true_effect_prediction
    subtitle = (
        f"Bayesian NNHM: pooled median = {mean.median:.3g}, "
        f"{result.credible_level:.0%} CrI [{mean.interval.low:.3g}, "
        f"{mean.interval.high:.3g}]; {primary.evidence.display}; "
        f"P(mu>{result.null_value:.3g}) = {mean.probability_above_null:.3f}; "
        f"tau median = {tau.median:.3g}, {result.credible_level:.0%} CrI "
        f"[{tau.interval.low:.3g}, {tau.interval.high:.3g}]"
    )
    sensitivities = ", ".join(
        f"{fit.label}: {fit.evidence.display}" for fit in result.sensitivities
    )
    warnings = ", ".join(result.warnings) if result.warnings else "none"
    caption = (
        f"k = {result.retained_rows}; estimand: {result.estimand}; scale: "
        f"{result.effect_scale}; direction: {result.effect_direction}; units: "
        f"{result.effect_units}; prior mu SD = {primary.prior.mean_scale:.3g}; "
        f"prior tau scale = {primary.prior.tau_scale:.3g}; posterior prediction "
        f"[{prediction.interval.low:.3g}, {prediction.interval.high:.3g}]; "
        f"sensitivities: {sensitivities}; work: {result.work.actual_work}/"
        f"{result.work.reserved_work}; warnings: {warnings}"
    )
    return subtitle, caption


def _render_bayesian_meta(
    analysis: BayesianMetaAnalysis,
    *,
    title: str | None,
    results_subtitle: bool,
    show_intervals: bool,
    show_prediction: bool,
    x_label: str | None,
    point_color: str,
    pooled_color: str,
    theme: StatsTheme | None,
) -> StatsPlot[BayesianMetaResult]:
    result = analysis.result
    figure = Figure()
    axes = figure.subplots()
    renderer = cast(_CoefficientAxes, axes)
    count = len(result.studies)
    positions = tuple(float(count - index) for index in range(count))
    renderer.axvline(result.null_value, color="#666666", linestyle="--", linewidth=1.0)
    for study, position in zip(result.studies, positions, strict=True):
        interval = study.sampling_interval
        renderer.errorbar(
            study.estimate,
            position,
            xerr=(
                [
                    [study.estimate - interval.low],
                    [interval.high - study.estimate],
                ]
                if show_intervals
                else None
            ),
            fmt="o",
            color=point_color,
            capsize=3.0,
            markersize=5.0,
            label=None,
            zorder=3,
        )
        if result.stats_labels:
            renderer.text(
                1.01,
                position,
                f"reported estimate = {study.estimate:.3g}; SE = "
                f"{study.standard_error:.3g}",
                transform=axes.get_yaxis_transform(),
                ha="left",
                va="center",
                fontsize="small",
            )
    pooled = result.primary.population_mean
    renderer.errorbar(
        pooled.median,
        0.0,
        xerr=[
            [pooled.median - pooled.interval.low],
            [pooled.interval.high - pooled.median],
        ],
        fmt="D",
        color=pooled_color,
        capsize=4.0,
        markersize=7.0,
        label="pooled equal-tail credible interval",
        zorder=4,
    )
    prediction = result.primary.true_effect_prediction.interval
    if show_prediction:
        renderer.hlines(
            0.0,
            prediction.low,
            prediction.high,
            color=pooled_color,
            linewidth=5.0,
            label="new-study posterior predictive credible interval",
            zorder=2,
        )
    renderer.set_yticks((*positions, 0.0), [*result.display_order, "Posterior pooled"])
    renderer.set_ylim(-1.0, float(count + 1))
    renderer.set_xlabel(x_label or f"{result.effect_scale} ({result.effect_units})")
    rendered_title = title or f"Bayesian meta-analysis of {result.estimand}"
    renderer.legend(loc="best")
    subtitle, caption = _bayesian_meta_annotations(result)
    (theme or theme_ggstatsplot()).apply(axes)
    _finalize_m6c_figure(
        figure,
        renderer,
        title=rendered_title,
        subtitle=subtitle,
        caption=caption,
        results_subtitle=results_subtitle,
        stats_labels=result.stats_labels,
        height=min(24.0, max(4.8, 2.8 + 0.34 * count)),
    )
    return StatsPlot(
        figure,
        {"main": axes},
        result,
        PlotAnnotations(rendered_title, subtitle, caption),
    )


def _render_coefficients(
    analysis: TableCoefficientAnalysis,
    *,
    title: str | None,
    results_subtitle: bool,
    show_intervals: bool,
    x_label: str | None,
    point_color: str,
    theme: StatsTheme | None,
) -> StatsPlot[CoefficientTableResult]:
    result = analysis.result
    figure = Figure(layout="constrained")
    axes = figure.subplots()
    renderer = cast(_CoefficientAxes, axes)
    count = len(result.terms)
    positions = tuple(float(count - index) for index in range(count))
    renderer.axvline(result.null_value, color="#666666", linestyle="--", linewidth=1.0)
    for term, position in zip(result.terms, positions, strict=True):
        interval = term.inference.interval if term.inference is not None else None
        xerr = (
            [[term.estimate - interval.low], [interval.high - term.estimate]]
            if show_intervals and interval is not None
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
        inference = term.inference
        visible = (
            result.stats_labels
            and inference is not None
            and inference.p_value is not None
            and (not result.only_significant or inference.significant is True)
        )
        if visible:
            if inference is None:
                raise AssertionError("visible coefficient label lost inference")
            if inference.statistic is None or inference.p_value is None:
                raise AssertionError("visible coefficient label lost test inference")
            df_text = f", df = {inference.df:.3g}" if inference.df is not None else ""
            label = (
                f"{inference.statistic_name} = {inference.statistic:.3g}"
                f"{df_text}, {_p_text(inference.p_value)}"
            )
            renderer.text(
                1.01,
                position,
                label,
                transform=axes.get_yaxis_transform(),
                ha="left",
                va="center",
                fontsize="small",
            )
    renderer.set_yticks(
        positions, [_identity_label(result, index) for index in range(count)]
    )
    renderer.set_ylim(0.5, float(count) + 0.5)
    renderer.set_xlabel(x_label or f"{result.estimate_label} ({result.effect_units})")
    rendered_title = title or "Coefficient estimates"
    renderer.set_title(rendered_title)
    subtitle = _coefficient_subtitle(result)
    caption = _coefficient_caption(result)
    if results_subtitle:
        renderer.text(
            0.5, 1.01, subtitle, transform=axes.transAxes, ha="center", va="bottom"
        )
    figure_renderer = cast(_CoefficientFigure, figure)
    figure_renderer.text(0.01, 0.01, caption, ha="left", va="bottom", fontsize="small")
    figure_renderer.set_size_inches(
        8.0, min(24.0, max(4.8, 2.5 + 0.34 * count)), forward=True
    )
    (theme or theme_ggstatsplot()).apply(axes)
    return StatsPlot(
        figure,
        {"main": axes},
        result,
        PlotAnnotations(rendered_title, subtitle, caption),
    )


def render_ggcoefstats(
    analysis: CoefficientAnalysis
    | TableCoefficientAnalysis
    | ReportedCoefficientAnalysis
    | RobustMetaAnalysis
    | BayesianMetaAnalysis,
    *,
    title: str | None = None,
    results_subtitle: bool = True,
    show_intervals: bool = True,
    show_prediction: bool = True,
    x_label: str | None = None,
    point_color: str = "#4c78a8",
    pooled_color: str = "#e45756",
    theme: StatsTheme | None = None,
) -> (
    StatsPlot[CoefficientResult]
    | StatsPlot[CoefficientTableResult]
    | StatsPlot[RobustCoefficientTableResult | PosteriorCoefficientTableResult]
    | StatsPlot[RobustMetaResult]
    | StatsPlot[BayesianMetaResult]
):
    """Render one typed coefficient analysis without recomputing statistics."""

    _validate_analysis_type(analysis)

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

    if isinstance(analysis, ReportedCoefficientAnalysis):
        return _render_reported_coefficients(
            analysis,
            title=title,
            results_subtitle=results_subtitle,
            show_intervals=show_intervals,
            x_label=x_label,
            point_color=point_color,
            theme=theme,
        )

    if isinstance(analysis, RobustMetaAnalysis):
        return _render_robust_meta(
            analysis,
            title=title,
            results_subtitle=results_subtitle,
            show_intervals=show_intervals,
            x_label=x_label,
            point_color=point_color,
            pooled_color=pooled_color,
            theme=theme,
        )

    if isinstance(analysis, BayesianMetaAnalysis):
        return _render_bayesian_meta(
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

    if isinstance(analysis, TableCoefficientAnalysis):
        return _render_coefficients(
            analysis,
            title=title,
            results_subtitle=results_subtitle,
            show_intervals=show_intervals,
            x_label=x_label,
            point_color=point_color,
            theme=theme,
        )

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
    data: object,
    *,
    meta_analytic_effect: bool = False,
    type: Literal["parametric", "robust", "bayes"] = "parametric",
    estimate_label: str = "",
    estimand: str = "",
    effect_scale: str = "",
    effect_direction: str = "",
    effect_units: str = "",
    dependence: str = "independent",
    null_value: float = 0.0,
    conf_level: float = 0.95,
    credible_level: float = 0.95,
    alpha: float = 0.05,
    stats_labels: bool = True,
    only_significant: bool = False,
    exclude_intercept: bool = False,
    sort: str = "none",
    maximum_coefficients: int = 500,
    maximum_studies: int = 500,
    maximum_rendered_points: int = 500,
    maximum_labels: int = 200,
    robust_method: str = "",
    robust_tuning: str = "",
    interval_method: str = "",
    posterior_model: str = "",
    likelihood: str = "",
    prior_description: str = "",
    computation_method: str = "",
    prior_mean_scale: float | None = None,
    prior_tau_scale: float | None = None,
    maximum_work: int = DEFAULT_MAXIMUM_WORK,
    title: str | None = None,
    results_subtitle: bool = True,
    show_intervals: bool = True,
    show_prediction: bool = True,
    x_label: str | None = None,
    point_color: str = "#4c78a8",
    pooled_color: str = "#e45756",
    theme: StatsTheme | None = None,
) -> (
    StatsPlot[CoefficientResult]
    | StatsPlot[CoefficientTableResult]
    | StatsPlot[RobustCoefficientTableResult | PosteriorCoefficientTableResult]
    | StatsPlot[RobustMetaResult]
    | StatsPlot[BayesianMetaResult]
):
    """Analyze and render an approved M5 coefficient or meta-analysis input."""

    analysis = analyze_ggcoefstats(
        data,
        meta_analytic_effect=meta_analytic_effect,
        type=type,
        estimate_label=estimate_label,
        estimand=estimand,
        effect_scale=effect_scale,
        effect_direction=effect_direction,
        effect_units=effect_units,
        dependence=dependence,
        null_value=null_value,
        conf_level=conf_level,
        credible_level=credible_level,
        alpha=alpha,
        stats_labels=stats_labels,
        only_significant=only_significant,
        exclude_intercept=exclude_intercept,
        sort=sort,
        maximum_coefficients=maximum_coefficients,
        maximum_studies=maximum_studies,
        maximum_rendered_points=maximum_rendered_points,
        maximum_labels=maximum_labels,
        robust_method=robust_method,
        robust_tuning=robust_tuning,
        interval_method=interval_method,
        posterior_model=posterior_model,
        likelihood=likelihood,
        prior_description=prior_description,
        computation_method=computation_method,
        prior_mean_scale=prior_mean_scale,
        prior_tau_scale=prior_tau_scale,
        maximum_work=maximum_work,
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
