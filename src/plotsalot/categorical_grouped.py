"""Atomic grouped execution for M4 categorical analyses."""

from __future__ import annotations

from collections.abc import Mapping

import polars as pl

from plotsalot.bayesian import (
    DEFAULT_MAX_BAYESIAN_WORK,
    bayesian_child_seed,
    validate_random_seed,
    validate_work_limit,
)
from plotsalot.categorical import render_ggbarstats, render_ggpiestats
from plotsalot.categorical_analysis import (
    DEFAULT_MAX_LABELS,
    CategoricalAnalysis,
    analyze_categorical,
)
from plotsalot.categorical_data import (
    DEFAULT_MAX_CELLS,
    DEFAULT_MAX_LEVELS,
    DEFAULT_MAX_TOTAL_COUNT,
    select_categorical_table,
)
from plotsalot.categorical_result import CategoricalResult
from plotsalot.data import DEFAULT_MAX_ROWS
from plotsalot.grouped import (
    DEFAULT_MAX_GROUPS,
    GroupAnalysisItem,
    GroupedAnalysis,
    group_annotations,
    group_error,
    grouped_result,
    split_groups,
)
from plotsalot.plot import GroupedStatsPlot
from plotsalot.result import GroupResultItem, ResourceLimits, ScalarIdentity
from plotsalot.theme import StatsTheme


def analyze_grouped_categorical(
    data: object,
    x: str,
    group: str,
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
    maximum_rows: int = DEFAULT_MAX_ROWS,
    maximum_groups: int = DEFAULT_MAX_GROUPS,
    maximum_levels: int = DEFAULT_MAX_LEVELS,
    maximum_cells: int = DEFAULT_MAX_CELLS,
    maximum_total_count: int = DEFAULT_MAX_TOTAL_COUNT,
    maximum_labels: int = DEFAULT_MAX_LABELS,
    prior_cell_concentration: float = 1.0,
    credible_level: float = 0.95,
    random_seed: int | None = None,
    maximum_bayesian_work: int = DEFAULT_MAX_BAYESIAN_WORK,
) -> GroupedAnalysis[CategoricalAnalysis]:
    selected = tuple(column for column in (x, y, counts, group) if column is not None)
    if len(set(selected)) != len(selected):
        raise ValueError("categorical and group columns must be distinct")
    partitions, sample = split_groups(
        data, group, maximum_rows=maximum_rows, maximum_groups=maximum_groups
    )
    analyses: list[GroupAnalysisItem[CategoricalAnalysis]] = []
    results: list[GroupResultItem] = []
    root_seed = (
        validate_random_seed(random_seed) if type == "bayes" and y is not None else 0
    )
    bayesian_work = 0
    if type == "bayes":
        for partition in partitions:
            try:
                retained = select_categorical_table(
                    partition.data,
                    x,
                    y,
                    counts=counts,
                    maximum_rows=maximum_rows,
                    maximum_levels=maximum_levels,
                    maximum_cells=maximum_cells,
                    maximum_total_count=maximum_total_count,
                )
            except (TypeError, ValueError) as error:
                raise group_error(partition.group, error) from error
            rows, columns = retained.observed.shape
            bayesian_work += rows * 3 if y is None else 8 * 4096 * rows * columns
        validate_work_limit(maximum_bayesian_work, bayesian_work)
    for partition in partitions:
        try:
            analysis = analyze_categorical(
                partition.data,
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
                prior_cell_concentration=prior_cell_concentration,
                credible_level=credible_level,
                random_seed=(
                    bayesian_child_seed(
                        root_seed,
                        "grouped_categorical_bayesian",
                        (("group", partition.group),),
                    )
                    if type == "bayes" and y is not None
                    else random_seed
                ),
                maximum_bayesian_work=maximum_bayesian_work,
            )
        except (TypeError, ValueError) as error:
            raise group_error(partition.group, error) from error
        analyses.append(GroupAnalysisItem(partition.group, analysis))
        results.append(GroupResultItem(partition.group, analysis.result))
    categorical_domain: set[tuple[type[object], ScalarIdentity]] = {
        (level.__class__, level)
        for item in analyses
        for level in item.analysis.result.x_levels
    }
    if len(categorical_domain) > maximum_levels:
        raise ValueError(
            f"grouped x category domain exceeds maximum_levels={maximum_levels}"
        )
    limits = ResourceLimits(
        maximum_rows=maximum_rows,
        maximum_groups=maximum_groups,
        maximum_variables=maximum_levels,
        maximum_labels=maximum_labels,
        maximum_levels=maximum_levels,
        maximum_pairwise_hypotheses=maximum_levels * (maximum_levels - 1) // 2,
        maximum_cells=maximum_cells,
        maximum_total_count=maximum_total_count,
    )
    return GroupedAnalysis(
        tuple(analyses),
        grouped_result(
            analysis=(
                "grouped_categorical_bayesian"
                if type == "bayes"
                else "grouped_categorical_classical"
            ),
            group_column=group,
            sample=sample,
            correction_scope="within_each_categorical_result_none_across_outer_groups",
            items=tuple(results),
            limits=limits,
            bayesian_root_seed=(
                root_seed if type == "bayes" and y is not None else None
            ),
            calculated_bayesian_work=bayesian_work if type == "bayes" else None,
            maximum_bayesian_work=(maximum_bayesian_work if type == "bayes" else None),
        ),
    )


analyze_grouped_ggbarstats = analyze_grouped_categorical
analyze_grouped_ggpiestats = analyze_grouped_categorical


def _color_domain(
    analysis: GroupedAnalysis[CategoricalAnalysis],
) -> tuple[ScalarIdentity, ...]:
    values: list[ScalarIdentity] = []
    seen: set[tuple[type[object], ScalarIdentity]] = set()
    for item in analysis.groups:
        for level in item.analysis.result.x_levels:
            key = (type(level), level)
            if key not in seen:
                seen.add(key)
                values.append(level)
    return tuple(values)


def render_grouped_ggbarstats(
    analysis: GroupedAnalysis[CategoricalAnalysis],
    *,
    label: str = "percentage",
    title: str | None = None,
    results_subtitle: bool = True,
    theme: StatsTheme | None = None,
) -> GroupedStatsPlot[CategoricalResult]:
    domain = _color_domain(analysis)
    plots = tuple(
        render_ggbarstats(
            item.analysis,
            label=label,
            title=f"{analysis.result.group_column} = {item.group}",
            results_subtitle=results_subtitle,
            theme=theme,
            color_domain=domain,
        )
        for item in analysis.groups
    )
    rendered_title = (
        title or f"Grouped categorical bars by {analysis.result.group_column}"
    )
    return GroupedStatsPlot(
        plots, analysis.result, group_annotations(analysis.result, rendered_title)
    )


def render_grouped_ggpiestats(
    analysis: GroupedAnalysis[CategoricalAnalysis],
    *,
    label: str = "percentage",
    title: str | None = None,
    results_subtitle: bool = True,
    theme: StatsTheme | None = None,
) -> GroupedStatsPlot[CategoricalResult]:
    domain = _color_domain(analysis)
    plots = tuple(
        render_ggpiestats(
            item.analysis,
            label=label,
            title=f"{analysis.result.group_column} = {item.group}",
            results_subtitle=results_subtitle,
            theme=theme,
            color_domain=domain,
        )
        for item in analysis.groups
    )
    rendered_title = (
        title or f"Grouped categorical pies by {analysis.result.group_column}"
    )
    return GroupedStatsPlot(
        plots, analysis.result, group_annotations(analysis.result, rendered_title)
    )


def grouped_ggbarstats(
    data: pl.DataFrame,
    x: str,
    group: str,
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
    maximum_groups: int = DEFAULT_MAX_GROUPS,
    maximum_levels: int = DEFAULT_MAX_LEVELS,
    maximum_cells: int = DEFAULT_MAX_CELLS,
    maximum_total_count: int = DEFAULT_MAX_TOTAL_COUNT,
    maximum_labels: int = DEFAULT_MAX_LABELS,
    prior_cell_concentration: float = 1.0,
    credible_level: float = 0.95,
    random_seed: int | None = None,
    maximum_bayesian_work: int = DEFAULT_MAX_BAYESIAN_WORK,
    title: str | None = None,
    results_subtitle: bool = True,
    theme: StatsTheme | None = None,
) -> GroupedStatsPlot[CategoricalResult]:
    analysis = analyze_grouped_categorical(
        data,
        x,
        group,
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
        maximum_groups=maximum_groups,
        maximum_levels=maximum_levels,
        maximum_cells=maximum_cells,
        maximum_total_count=maximum_total_count,
        maximum_labels=maximum_labels,
        prior_cell_concentration=prior_cell_concentration,
        credible_level=credible_level,
        random_seed=random_seed,
        maximum_bayesian_work=maximum_bayesian_work,
    )
    return render_grouped_ggbarstats(
        analysis,
        label=label,
        title=title,
        results_subtitle=results_subtitle,
        theme=theme,
    )


def grouped_ggpiestats(
    data: pl.DataFrame,
    x: str,
    group: str,
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
    maximum_groups: int = DEFAULT_MAX_GROUPS,
    maximum_levels: int = DEFAULT_MAX_LEVELS,
    maximum_cells: int = DEFAULT_MAX_CELLS,
    maximum_total_count: int = DEFAULT_MAX_TOTAL_COUNT,
    maximum_labels: int = DEFAULT_MAX_LABELS,
    prior_cell_concentration: float = 1.0,
    credible_level: float = 0.95,
    random_seed: int | None = None,
    maximum_bayesian_work: int = DEFAULT_MAX_BAYESIAN_WORK,
    title: str | None = None,
    results_subtitle: bool = True,
    theme: StatsTheme | None = None,
) -> GroupedStatsPlot[CategoricalResult]:
    analysis = analyze_grouped_categorical(
        data,
        x,
        group,
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
        maximum_groups=maximum_groups,
        maximum_levels=maximum_levels,
        maximum_cells=maximum_cells,
        maximum_total_count=maximum_total_count,
        maximum_labels=maximum_labels,
        prior_cell_concentration=prior_cell_concentration,
        credible_level=credible_level,
        random_seed=random_seed,
        maximum_bayesian_work=maximum_bayesian_work,
    )
    return render_grouped_ggpiestats(
        analysis,
        label=label,
        title=title,
        results_subtitle=results_subtitle,
        theme=theme,
    )
