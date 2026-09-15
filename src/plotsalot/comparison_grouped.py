"""Atomic grouped execution for approved M3 comparison analyses."""

from __future__ import annotations

from plotsalot.bayesian import (
    DEFAULT_MAX_BAYESIAN_WORK,
    bayesian_child_seed,
    validate_random_seed,
    validate_work_limit,
)
from plotsalot.comparison import render_ggbetweenstats, render_ggwithinstats
from plotsalot.comparison_analysis import (
    DEFAULT_MAX_LEVELS,
    DEFAULT_MAX_RENDERED_OBSERVATIONS,
    DEFAULT_MAX_SUBJECT_PATHS,
    ComparisonAnalysis,
    analyze_ggbetweenstats,
    analyze_ggwithinstats,
)
from plotsalot.comparison_data import select_comparison_sample, select_repeated_sample
from plotsalot.comparison_result import ComparisonResult
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
from plotsalot.result import GroupResultItem, ResourceLimits
from plotsalot.robust import TRIM_FRACTION
from plotsalot.theme import StatsTheme


def analyze_grouped_ggbetweenstats(
    data: object,
    x: str,
    y: str,
    group: str,
    *,
    type: str = "parametric",
    alternative: str = "two-sided",
    conf_level: float = 0.95,
    p_adjust: str = "holm",
    pairwise_alpha: float = 0.05,
    pairwise_display: str = "significant",
    maximum_rows: int = DEFAULT_MAX_ROWS,
    maximum_groups: int = DEFAULT_MAX_GROUPS,
    maximum_levels: int = DEFAULT_MAX_LEVELS,
    maximum_rendered_observations: int = DEFAULT_MAX_RENDERED_OBSERVATIONS,
    trim_fraction: float = TRIM_FRACTION,
    prior_location: float | None = None,
    prior_scale: float | None = None,
    credible_level: float = 0.95,
    random_seed: int | None = None,
    maximum_bayesian_work: int = DEFAULT_MAX_BAYESIAN_WORK,
) -> GroupedAnalysis[ComparisonAnalysis]:
    """Apply the approved independent comparison atomically by outer group."""

    partitions, sample = split_groups(
        data,
        group,
        maximum_rows=maximum_rows,
        maximum_groups=maximum_groups,
    )
    groups: list[GroupAnalysisItem[ComparisonAnalysis]] = []
    results: list[GroupResultItem] = []
    root_seed = validate_random_seed(random_seed) if type == "bayes" else 0
    bayesian_work = 0
    if type == "bayes":
        for partition in partitions:
            try:
                retained = select_comparison_sample(
                    partition.data,
                    x,
                    y,
                    maximum_rows=maximum_rows,
                    maximum_levels=maximum_levels,
                )
            except (TypeError, ValueError) as error:
                raise group_error(partition.group, error) from error
            levels = len(retained.levels)
            bayesian_work += 8 * 4096 * (levels + 1)
        validate_work_limit(maximum_bayesian_work, bayesian_work)
    for partition in partitions:
        try:
            item_analysis = analyze_ggbetweenstats(
                partition.data,
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
                random_seed=(
                    bayesian_child_seed(
                        root_seed,
                        "grouped_ggbetweenstats_bayesian",
                        (("group", partition.group),),
                    )
                    if type == "bayes"
                    else random_seed
                ),
                maximum_bayesian_work=maximum_bayesian_work,
            )
        except (TypeError, ValueError) as error:
            raise group_error(partition.group, error) from error
        groups.append(GroupAnalysisItem(partition.group, item_analysis))
        results.append(GroupResultItem(partition.group, item_analysis.result))
    return GroupedAnalysis(
        groups=tuple(groups),
        result=grouped_result(
            analysis=(
                "grouped_ggbetweenstats_bayesian"
                if type == "bayes"
                else (
                    "grouped_ggbetweenstats_robust"
                    if type == "robust"
                    else "grouped_ggbetweenstats_welch"
                )
            ),
            group_column=group,
            sample=sample,
            correction_scope=("within_each_comparison_result_none_across_outer_groups"),
            items=tuple(results),
            limits=ResourceLimits(
                maximum_rows=maximum_rows,
                maximum_groups=maximum_groups,
                maximum_levels=maximum_levels,
                maximum_pairwise_hypotheses=(
                    maximum_levels * (maximum_levels - 1) // 2
                ),
                maximum_rendered_observations=maximum_rendered_observations,
            ),
            bayesian_root_seed=root_seed if type == "bayes" else None,
            calculated_bayesian_work=bayesian_work if type == "bayes" else None,
            maximum_bayesian_work=(maximum_bayesian_work if type == "bayes" else None),
        ),
    )


def analyze_grouped_ggwithinstats(
    data: object,
    x: str,
    y: str,
    group: str,
    *,
    subject_id: str,
    type: str = "parametric",
    alternative: str = "two-sided",
    conf_level: float = 0.95,
    p_adjust: str = "holm",
    pairwise_alpha: float = 0.05,
    pairwise_display: str = "significant",
    maximum_rows: int = DEFAULT_MAX_ROWS,
    maximum_groups: int = DEFAULT_MAX_GROUPS,
    maximum_levels: int = DEFAULT_MAX_LEVELS,
    maximum_rendered_observations: int = DEFAULT_MAX_RENDERED_OBSERVATIONS,
    maximum_subject_paths: int = DEFAULT_MAX_SUBJECT_PATHS,
    trim_fraction: float = TRIM_FRACTION,
    prior_location: float | None = None,
    prior_scale: float | None = None,
    credible_level: float = 0.95,
    random_seed: int | None = None,
    maximum_bayesian_work: int = DEFAULT_MAX_BAYESIAN_WORK,
) -> GroupedAnalysis[ComparisonAnalysis]:
    """Apply the approved repeated comparison atomically by outer group."""

    partitions, sample = split_groups(
        data,
        group,
        maximum_rows=maximum_rows,
        maximum_groups=maximum_groups,
    )
    groups: list[GroupAnalysisItem[ComparisonAnalysis]] = []
    results: list[GroupResultItem] = []
    root_seed = validate_random_seed(random_seed) if type == "bayes" else 0
    bayesian_work = 0
    if type == "bayes":
        for partition in partitions:
            try:
                retained = select_repeated_sample(
                    partition.data,
                    x,
                    y,
                    subject_id,
                    maximum_rows=maximum_rows,
                    maximum_levels=maximum_levels,
                    minimum_subjects=3,
                )
            except (TypeError, ValueError) as error:
                raise group_error(partition.group, error) from error
            conditions = retained.values.shape[1]
            bayesian_work += 8 * 4096 * (conditions + 2)
        validate_work_limit(maximum_bayesian_work, bayesian_work)
    for partition in partitions:
        try:
            item_analysis = analyze_ggwithinstats(
                partition.data,
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
                random_seed=(
                    bayesian_child_seed(
                        root_seed,
                        "grouped_ggwithinstats_bayesian",
                        (("group", partition.group),),
                    )
                    if type == "bayes"
                    else random_seed
                ),
                maximum_bayesian_work=maximum_bayesian_work,
            )
        except (TypeError, ValueError) as error:
            raise group_error(partition.group, error) from error
        groups.append(GroupAnalysisItem(partition.group, item_analysis))
        results.append(GroupResultItem(partition.group, item_analysis.result))
    return GroupedAnalysis(
        groups=tuple(groups),
        result=grouped_result(
            analysis=(
                "grouped_ggwithinstats_bayesian"
                if type == "bayes"
                else (
                    "grouped_ggwithinstats_robust"
                    if type == "robust"
                    else "grouped_ggwithinstats_parametric"
                )
            ),
            group_column=group,
            sample=sample,
            correction_scope=("within_each_repeated_result_none_across_outer_groups"),
            items=tuple(results),
            limits=ResourceLimits(
                maximum_rows=maximum_rows,
                maximum_groups=maximum_groups,
                maximum_levels=maximum_levels,
                maximum_pairwise_hypotheses=(
                    maximum_levels * (maximum_levels - 1) // 2
                ),
                maximum_rendered_observations=maximum_rendered_observations,
                maximum_subject_paths=maximum_subject_paths,
            ),
            bayesian_root_seed=root_seed if type == "bayes" else None,
            calculated_bayesian_work=bayesian_work if type == "bayes" else None,
            maximum_bayesian_work=(maximum_bayesian_work if type == "bayes" else None),
        ),
    )


def render_grouped_ggbetweenstats(
    analysis: GroupedAnalysis[ComparisonAnalysis],
    *,
    title: str | None = None,
    results_subtitle: bool = True,
    theme: StatsTheme | None = None,
) -> GroupedStatsPlot[ComparisonResult]:
    """Render one independent comparison per outer group."""

    plots = tuple(
        render_ggbetweenstats(
            item.analysis,
            title=f"{analysis.result.group_column} = {item.group}",
            results_subtitle=results_subtitle,
            theme=theme,
        )
        for item in analysis.groups
    )
    rendered_title = title or (
        f"Grouped independent comparisons by {analysis.result.group_column}"
    )
    return GroupedStatsPlot(
        plots=plots,
        result=analysis.result,
        annotations=group_annotations(analysis.result, rendered_title),
    )


def render_grouped_ggwithinstats(
    analysis: GroupedAnalysis[ComparisonAnalysis],
    *,
    title: str | None = None,
    results_subtitle: bool = True,
    show_subject_paths: bool = True,
    theme: StatsTheme | None = None,
) -> GroupedStatsPlot[ComparisonResult]:
    """Render one repeated comparison per outer group."""

    plots = tuple(
        render_ggwithinstats(
            item.analysis,
            title=f"{analysis.result.group_column} = {item.group}",
            results_subtitle=results_subtitle,
            show_subject_paths=show_subject_paths,
            theme=theme,
        )
        for item in analysis.groups
    )
    rendered_title = title or (
        f"Grouped repeated comparisons by {analysis.result.group_column}"
    )
    return GroupedStatsPlot(
        plots=plots,
        result=analysis.result,
        annotations=group_annotations(analysis.result, rendered_title),
    )


def grouped_ggbetweenstats(
    data: object,
    x: str,
    y: str,
    group: str,
    *,
    type: str = "parametric",
    alternative: str = "two-sided",
    conf_level: float = 0.95,
    p_adjust: str = "holm",
    pairwise_alpha: float = 0.05,
    pairwise_display: str = "significant",
    maximum_rows: int = DEFAULT_MAX_ROWS,
    maximum_groups: int = DEFAULT_MAX_GROUPS,
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
) -> GroupedStatsPlot[ComparisonResult]:
    """Analyze and render independent comparisons by outer group."""

    analysis = analyze_grouped_ggbetweenstats(
        data,
        x,
        y,
        group,
        type=type,
        alternative=alternative,
        conf_level=conf_level,
        p_adjust=p_adjust,
        pairwise_alpha=pairwise_alpha,
        pairwise_display=pairwise_display,
        maximum_rows=maximum_rows,
        maximum_groups=maximum_groups,
        maximum_levels=maximum_levels,
        maximum_rendered_observations=maximum_rendered_observations,
        trim_fraction=trim_fraction,
        prior_location=prior_location,
        prior_scale=prior_scale,
        credible_level=credible_level,
        random_seed=random_seed,
        maximum_bayesian_work=maximum_bayesian_work,
    )
    return render_grouped_ggbetweenstats(
        analysis,
        title=title,
        results_subtitle=results_subtitle,
        theme=theme,
    )


def grouped_ggwithinstats(
    data: object,
    x: str,
    y: str,
    group: str,
    *,
    subject_id: str,
    type: str = "parametric",
    alternative: str = "two-sided",
    conf_level: float = 0.95,
    p_adjust: str = "holm",
    pairwise_alpha: float = 0.05,
    pairwise_display: str = "significant",
    maximum_rows: int = DEFAULT_MAX_ROWS,
    maximum_groups: int = DEFAULT_MAX_GROUPS,
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
) -> GroupedStatsPlot[ComparisonResult]:
    """Analyze and render repeated comparisons by outer group."""

    analysis = analyze_grouped_ggwithinstats(
        data,
        x,
        y,
        group,
        subject_id=subject_id,
        type=type,
        alternative=alternative,
        conf_level=conf_level,
        p_adjust=p_adjust,
        pairwise_alpha=pairwise_alpha,
        pairwise_display=pairwise_display,
        maximum_rows=maximum_rows,
        maximum_groups=maximum_groups,
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
    return render_grouped_ggwithinstats(
        analysis,
        title=title,
        results_subtitle=results_subtitle,
        show_subject_paths=show_subject_paths,
        theme=theme,
    )
