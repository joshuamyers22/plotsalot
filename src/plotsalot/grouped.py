"""Atomic grouped analyses and per-group plot containers."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Generic, TypeVar, cast

import polars as pl

from plotsalot.bayesian import (
    CORRELATION_RESERVED_WORK,
    DEFAULT_MAX_BAYESIAN_WORK,
    validate_work_limit,
)
from plotsalot.bayesian_result import (
    BayesianCorrelationMatrixResult,
    BayesianCorrelationResult,
    BayesianDotPlotResult,
    BayesianOneSampleResult,
)
from plotsalot.correlation import render_ggcorrmat, render_ggscatterstats
from plotsalot.correlation_analysis import (
    CorrelationAnalysis,
    CorrelationMatrixAnalysis,
    analyze_ggcorrmat,
    analyze_ggscatterstats,
)
from plotsalot.data import (
    DEFAULT_MAX_ROWS,
    select_numeric_pair,
)
from plotsalot.dotplot import render_ggdotplotstats
from plotsalot.dotplot_analysis import (
    DEFAULT_MAX_LABELS,
    DotPlotAnalysis,
    analyze_ggdotplotstats,
)
from plotsalot.histogram import render_gghistostats
from plotsalot.histogram_analysis import (
    Alternative,
    HistogramAnalysis,
    analyze_gghistostats,
)
from plotsalot.plot import GroupedStatsPlot, PlotAnnotations
from plotsalot.result import (
    AnalysisResult,
    CorrelationMatrixResult,
    CorrelationResult,
    DotPlotResult,
    GroupedResult,
    GroupIdentity,
    GroupResultItem,
    GroupSampleAudit,
    ResourceLimits,
)
from plotsalot.robust import (
    DEFAULT_BOOTSTRAP_RESAMPLES,
    DEFAULT_MAX_RESAMPLE_WORK,
    TRIM_FRACTION,
    child_seed,
    validate_resampling,
)

AnalysisT = TypeVar("AnalysisT")
DEFAULT_MAX_GROUPS = 20


@dataclass(frozen=True, slots=True)
class GroupAnalysisItem(Generic[AnalysisT]):
    """One encoded group identity and its renderer-independent analysis."""

    group: GroupIdentity
    analysis: AnalysisT

    def __post_init__(self) -> None:
        if isinstance(self.group, str) and not self.group:
            raise ValueError("group identity must be non-empty")
        if isinstance(self.group, float) and not isfinite(self.group):
            raise ValueError("numeric group identity must be finite")


@dataclass(frozen=True, slots=True)
class GroupedAnalysis(Generic[AnalysisT]):
    """Atomic grouped result and its ordered per-group analyses."""

    groups: tuple[GroupAnalysisItem[AnalysisT], ...]
    result: GroupedResult

    def __post_init__(self) -> None:
        if not self.groups or len(self.groups) != len(self.result.groups):
            raise ValueError("grouped analyses must match grouped results")
        for analysis_item, result_item in zip(
            self.groups, self.result.groups, strict=True
        ):
            if (
                type(analysis_item.group),
                analysis_item.group,
            ) != (type(result_item.group), result_item.group):
                raise ValueError("grouped analysis identities must match")


@dataclass(frozen=True, slots=True)
class _GroupPartition:
    group: GroupIdentity
    data: pl.DataFrame


def _group_identity(value: object) -> GroupIdentity:
    if isinstance(value, bool):
        return value
    if isinstance(value, (str, int)):
        if isinstance(value, str) and not value:
            raise ValueError("group identity must not be empty")
        return value
    if isinstance(value, float) and isfinite(value):
        return value
    raise TypeError(
        "group values must be finite strings, integers, floats, or booleans"
    )


def split_groups(
    data: object,
    group: str,
    *,
    maximum_rows: int,
    maximum_groups: int,
) -> tuple[tuple[_GroupPartition, ...], GroupSampleAudit]:
    if not isinstance(data, pl.DataFrame):
        raise TypeError("data must be a polars.DataFrame")
    if not group:
        raise ValueError("group column must be non-empty")
    if group not in data.columns:
        raise ValueError(f"column not found: {group!r}")
    if maximum_rows < 1 or data.height > maximum_rows:
        raise ValueError(f"data exceeds maximum_rows={maximum_rows}")
    if maximum_groups < 1:
        raise ValueError("maximum_groups must be at least one")

    retained = data.filter(pl.col(group).is_not_null())
    if retained.is_empty():
        raise ValueError("grouped analysis requires a non-null group")
    frames = retained.partition_by(group, maintain_order=True)
    if len(frames) > maximum_groups:
        raise ValueError(f"group count exceeds maximum_groups={maximum_groups}")

    partitions: list[_GroupPartition] = []
    seen: set[tuple[type[object], GroupIdentity]] = set()
    for frame in frames:
        identity = _group_identity(frame.get_column(group)[0])
        identity_key = (type(identity), identity)
        if identity_key in seen:
            raise ValueError(
                f"group identity is not unique after encoding: {identity!r}"
            )
        seen.add(identity_key)
        partitions.append(_GroupPartition(group=identity, data=frame))

    return (
        tuple(partitions),
        GroupSampleAudit(
            input_rows=data.height,
            analyzed_rows=retained.height,
            dropped_null_group_rows=data.height - retained.height,
        ),
    )


def grouped_result(
    *,
    analysis: str,
    group_column: str,
    sample: GroupSampleAudit,
    correction_scope: str,
    items: tuple[GroupResultItem, ...],
    limits: ResourceLimits,
    resampling_root_seed: int | None = None,
    calculated_resample_work: int | None = None,
    maximum_resample_work: int | None = None,
    bayesian_root_seed: int | None = None,
    calculated_bayesian_work: int | None = None,
    maximum_bayesian_work: int | None = None,
) -> GroupedResult:
    return GroupedResult(
        schema_version=1,
        analysis=analysis,
        group_column=group_column,
        sample=sample,
        correction_scope=correction_scope,
        groups=items,
        limits=limits,
        warnings=(),
        resampling_root_seed=resampling_root_seed,
        calculated_resample_work=calculated_resample_work,
        maximum_resample_work=maximum_resample_work,
        bayesian_root_seed=bayesian_root_seed,
        calculated_bayesian_work=calculated_bayesian_work,
        maximum_bayesian_work=maximum_bayesian_work,
    )


def group_error(group: GroupIdentity, error: Exception) -> ValueError:
    return ValueError(f"group {group!r} failed: {error}")


def analyze_grouped_gghistostats(
    data: object,
    x: str,
    group: str,
    *,
    test_value: float = 0.0,
    alternative: Alternative = "two-sided",
    conf_level: float = 0.95,
    maximum_rows: int = DEFAULT_MAX_ROWS,
    maximum_groups: int = DEFAULT_MAX_GROUPS,
    type: str = "parametric",
    trim_fraction: float = TRIM_FRACTION,
    prior_scale: float | None = None,
    credible_level: float = 0.95,
    maximum_bayesian_work: int = DEFAULT_MAX_BAYESIAN_WORK,
) -> GroupedAnalysis[HistogramAnalysis]:
    """Apply the approved histogram analysis atomically by group."""

    if type not in {"parametric", "robust", "bayes"}:
        raise ValueError("type must be 'parametric', 'robust', or 'bayes'")

    partitions, sample = split_groups(
        data,
        group,
        maximum_rows=maximum_rows,
        maximum_groups=maximum_groups,
    )
    if type == "bayes":
        validate_work_limit(
            maximum_bayesian_work,
            sum(3 * partition.data.height for partition in partitions),
        )
    groups: list[GroupAnalysisItem[HistogramAnalysis]] = []
    results: list[GroupResultItem] = []
    for partition in partitions:
        try:
            item_analysis = analyze_gghistostats(
                partition.data,
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
        except (TypeError, ValueError) as error:
            raise group_error(partition.group, error) from error
        groups.append(GroupAnalysisItem(partition.group, item_analysis))
        results.append(GroupResultItem(partition.group, item_analysis.result))
    bayesian_work = (
        sum(
            item.analysis.result.computation.calculated_work
            for item in groups
            if isinstance(item.analysis.result, BayesianOneSampleResult)
        )
        if type == "bayes"
        else None
    )
    return GroupedAnalysis(
        groups=tuple(groups),
        result=grouped_result(
            analysis=(
                "grouped_gghistostats_one_sample_bayesian"
                if type == "bayes"
                else (
                    "grouped_gghistostats_one_sample_robust"
                    if type == "robust"
                    else "grouped_gghistostats_one_sample_parametric"
                )
            ),
            group_column=group,
            sample=sample,
            correction_scope="none_across_groups",
            items=tuple(results),
            limits=ResourceLimits(
                maximum_rows=maximum_rows,
                maximum_groups=maximum_groups,
            ),
            calculated_bayesian_work=bayesian_work,
            maximum_bayesian_work=(maximum_bayesian_work if type == "bayes" else None),
        ),
    )


def analyze_grouped_ggdotplotstats(
    data: object,
    x: str,
    y: str,
    group: str,
    *,
    test_value: float = 0.0,
    alternative: Alternative = "two-sided",
    conf_level: float = 0.95,
    maximum_rows: int = DEFAULT_MAX_ROWS,
    maximum_groups: int = DEFAULT_MAX_GROUPS,
    maximum_labels: int = DEFAULT_MAX_LABELS,
    type: str = "parametric",
    trim_fraction: float = TRIM_FRACTION,
    prior_scale: float | None = None,
    credible_level: float = 0.95,
    maximum_bayesian_work: int = DEFAULT_MAX_BAYESIAN_WORK,
) -> GroupedAnalysis[DotPlotAnalysis]:
    """Apply the approved labeled dot-plot analysis atomically by group."""

    partitions, sample = split_groups(
        data,
        group,
        maximum_rows=maximum_rows,
        maximum_groups=maximum_groups,
    )
    if type == "bayes":
        validate_work_limit(
            maximum_bayesian_work,
            sum(6 * partition.data.height for partition in partitions),
        )
    groups: list[GroupAnalysisItem[DotPlotAnalysis]] = []
    results: list[GroupResultItem] = []
    for partition in partitions:
        try:
            item_analysis = analyze_ggdotplotstats(
                partition.data,
                x,
                y,
                test_value=test_value,
                alternative=alternative,
                conf_level=conf_level,
                maximum_rows=maximum_rows,
                maximum_labels=maximum_labels,
                type=type,
                trim_fraction=trim_fraction,
                prior_scale=prior_scale,
                credible_level=credible_level,
                maximum_bayesian_work=maximum_bayesian_work,
            )
        except (TypeError, ValueError) as error:
            raise group_error(partition.group, error) from error
        groups.append(GroupAnalysisItem(partition.group, item_analysis))
        results.append(GroupResultItem(partition.group, item_analysis.result))
    bayesian_work: int | None = None
    if type == "bayes":
        bayesian_work = 0
        for item in groups:
            result = cast(BayesianDotPlotResult, item.analysis.result)
            bayesian_work += result.one_sample.computation.calculated_work
            bayesian_work += sum(
                estimate.computation.calculated_work for estimate in result.estimates
            )
    return GroupedAnalysis(
        groups=tuple(groups),
        result=grouped_result(
            analysis=(
                "grouped_ggdotplotstats_one_sample_bayesian"
                if type == "bayes"
                else (
                    "grouped_ggdotplotstats_one_sample_robust"
                    if type == "robust"
                    else "grouped_ggdotplotstats_one_sample_parametric"
                )
            ),
            group_column=group,
            sample=sample,
            correction_scope="none_across_groups",
            items=tuple(results),
            limits=ResourceLimits(
                maximum_rows=maximum_rows,
                maximum_groups=maximum_groups,
                maximum_labels=maximum_labels,
            ),
            calculated_bayesian_work=bayesian_work,
            maximum_bayesian_work=(maximum_bayesian_work if type == "bayes" else None),
        ),
    )


def analyze_grouped_ggscatterstats(
    data: object,
    x: str,
    y: str,
    group: str,
    *,
    conf_level: float = 0.95,
    maximum_rows: int = DEFAULT_MAX_ROWS,
    maximum_groups: int = DEFAULT_MAX_GROUPS,
    type: str = "parametric",
    trim_fraction: float = TRIM_FRACTION,
    bootstrap_resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
    random_seed: int | None = None,
    maximum_resample_work: int = DEFAULT_MAX_RESAMPLE_WORK,
    correlation_prior_shape: float = 1.0,
    credible_level: float = 0.95,
    maximum_bayesian_work: int = DEFAULT_MAX_BAYESIAN_WORK,
) -> GroupedAnalysis[CorrelationAnalysis]:
    """Apply the approved Pearson scatter analysis atomically by group."""

    partitions, sample = split_groups(
        data,
        group,
        maximum_rows=maximum_rows,
        maximum_groups=maximum_groups,
    )
    if type == "bayes":
        validate_work_limit(
            maximum_bayesian_work,
            len(partitions) * CORRELATION_RESERVED_WORK,
        )
    total_work = 0
    if type == "robust":
        for partition in partitions:
            pair = select_numeric_pair(
                partition.data,
                x,
                y,
                minimum_size=8,
                maximum_rows=maximum_rows,
            )
            total_work += pair.audit.analyzed_rows * bootstrap_resamples
        root_seed = validate_resampling(
            bootstrap_resamples=bootstrap_resamples,
            random_seed=random_seed,
            maximum_resample_work=maximum_resample_work,
            calculated_work=total_work,
        )
    else:
        root_seed = 0
    groups: list[GroupAnalysisItem[CorrelationAnalysis]] = []
    results: list[GroupResultItem] = []
    for partition in partitions:
        try:
            derived_seed = random_seed
            if type == "robust":
                derived_seed = child_seed(
                    root_seed,
                    "grouped_ggscatterstats_winsorized",
                    (partition.group, *tuple(sorted((x, y)))),
                )[0]
            item_analysis = analyze_ggscatterstats(
                partition.data,
                x,
                y,
                conf_level=conf_level,
                maximum_rows=maximum_rows,
                type=type,
                trim_fraction=trim_fraction,
                bootstrap_resamples=bootstrap_resamples,
                random_seed=derived_seed,
                maximum_resample_work=maximum_resample_work,
                correlation_prior_shape=correlation_prior_shape,
                credible_level=credible_level,
                maximum_bayesian_work=maximum_bayesian_work,
            )
        except (TypeError, ValueError) as error:
            raise group_error(partition.group, error) from error
        groups.append(GroupAnalysisItem(partition.group, item_analysis))
        results.append(GroupResultItem(partition.group, item_analysis.result))
    bayesian_work = (
        sum(
            item.analysis.result.computation.calculated_work
            for item in groups
            if isinstance(item.analysis.result, BayesianCorrelationResult)
        )
        if type == "bayes"
        else None
    )
    return GroupedAnalysis(
        groups=tuple(groups),
        result=grouped_result(
            analysis=(
                "grouped_ggscatterstats_bayesian_pearson"
                if type == "bayes"
                else (
                    "grouped_ggscatterstats_winsorized"
                    if type == "robust"
                    else "grouped_ggscatterstats_pearson"
                )
            ),
            group_column=group,
            sample=sample,
            correction_scope="none_across_groups",
            items=tuple(results),
            limits=ResourceLimits(
                maximum_rows=maximum_rows,
                maximum_groups=maximum_groups,
            ),
            resampling_root_seed=root_seed if type == "robust" else None,
            calculated_resample_work=total_work if type == "robust" else None,
            maximum_resample_work=(maximum_resample_work if type == "robust" else None),
            calculated_bayesian_work=bayesian_work,
            maximum_bayesian_work=(maximum_bayesian_work if type == "bayes" else None),
        ),
    )


def analyze_grouped_ggcorrmat(
    data: object,
    columns: list[str] | tuple[str, ...],
    group: str,
    *,
    conf_level: float = 0.95,
    sig_level: float = 0.05,
    p_adjust: str = "holm",
    maximum_rows: int = DEFAULT_MAX_ROWS,
    maximum_groups: int = DEFAULT_MAX_GROUPS,
    type: str = "parametric",
    trim_fraction: float = TRIM_FRACTION,
    bootstrap_resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
    random_seed: int | None = None,
    maximum_resample_work: int = DEFAULT_MAX_RESAMPLE_WORK,
    correlation_prior_shape: float = 1.0,
    credible_level: float = 0.95,
    maximum_bayesian_work: int = DEFAULT_MAX_BAYESIAN_WORK,
) -> GroupedAnalysis[CorrelationMatrixAnalysis]:
    """Apply the approved Pearson matrix analysis atomically by group."""

    partitions, sample = split_groups(
        data,
        group,
        maximum_rows=maximum_rows,
        maximum_groups=maximum_groups,
    )
    if type == "bayes":
        pair_count = len(columns) * (len(columns) - 1) // 2
        validate_work_limit(
            maximum_bayesian_work,
            len(partitions) * pair_count * CORRELATION_RESERVED_WORK,
        )
    total_work = 0
    if type == "robust":
        for partition in partitions:
            for index, left in enumerate(columns):
                for right in columns[index + 1 :]:
                    pair = select_numeric_pair(
                        partition.data,
                        left,
                        right,
                        minimum_size=8,
                        maximum_rows=maximum_rows,
                    )
                    total_work += pair.audit.analyzed_rows * bootstrap_resamples
        root_seed = validate_resampling(
            bootstrap_resamples=bootstrap_resamples,
            random_seed=random_seed,
            maximum_resample_work=maximum_resample_work,
            calculated_work=total_work,
        )
    else:
        root_seed = 0
    groups: list[GroupAnalysisItem[CorrelationMatrixAnalysis]] = []
    results: list[GroupResultItem] = []
    for partition in partitions:
        try:
            derived_seed = random_seed
            if type == "robust":
                derived_seed = child_seed(
                    root_seed,
                    "grouped_ggcorrmat_winsorized",
                    (partition.group,),
                )[0]
            item_analysis = analyze_ggcorrmat(
                partition.data,
                columns,
                conf_level=conf_level,
                sig_level=sig_level,
                p_adjust=p_adjust,
                maximum_rows=maximum_rows,
                type=type,
                trim_fraction=trim_fraction,
                bootstrap_resamples=bootstrap_resamples,
                random_seed=derived_seed,
                maximum_resample_work=maximum_resample_work,
                correlation_prior_shape=correlation_prior_shape,
                credible_level=credible_level,
                maximum_bayesian_work=maximum_bayesian_work,
            )
        except (TypeError, ValueError) as error:
            raise group_error(partition.group, error) from error
        groups.append(GroupAnalysisItem(partition.group, item_analysis))
        results.append(GroupResultItem(partition.group, item_analysis.result))
    bayesian_work = (
        sum(
            item.analysis.result.calculated_bayesian_work
            for item in groups
            if isinstance(item.analysis.result, BayesianCorrelationMatrixResult)
        )
        if type == "bayes"
        else None
    )
    return GroupedAnalysis(
        groups=tuple(groups),
        result=grouped_result(
            analysis=(
                "grouped_ggcorrmat_bayesian_pearson"
                if type == "bayes"
                else (
                    "grouped_ggcorrmat_winsorized"
                    if type == "robust"
                    else "grouped_ggcorrmat_pearson"
                )
            ),
            group_column=group,
            sample=sample,
            correction_scope="within_group_matrix",
            items=tuple(results),
            limits=ResourceLimits(
                maximum_rows=maximum_rows,
                maximum_groups=maximum_groups,
                maximum_variables=50,
            ),
            resampling_root_seed=root_seed if type == "robust" else None,
            calculated_resample_work=total_work if type == "robust" else None,
            maximum_resample_work=(maximum_resample_work if type == "robust" else None),
            calculated_bayesian_work=bayesian_work,
            maximum_bayesian_work=(maximum_bayesian_work if type == "bayes" else None),
        ),
    )


def group_annotations(result: GroupedResult, title: str) -> PlotAnnotations:
    return PlotAnnotations(
        title=title,
        subtitle=f"{len(result.groups)} group(s); {result.correction_scope}",
        caption=(f"{result.sample.dropped_null_group_rows} null group row(s) excluded"),
    )


def render_grouped_gghistostats(
    analysis: GroupedAnalysis[HistogramAnalysis],
    *,
    binwidth: float | None = None,
    title: str | None = None,
) -> GroupedStatsPlot[AnalysisResult]:
    """Render one histogram plot per retained group."""

    plots = tuple(
        render_gghistostats(
            item.analysis,
            binwidth=binwidth,
            title=f"{analysis.result.group_column} = {item.group}",
        )
        for item in analysis.groups
    )
    rendered_title = title or f"Grouped distributions by {analysis.result.group_column}"
    return GroupedStatsPlot(
        plots=plots,
        result=analysis.result,
        annotations=group_annotations(analysis.result, rendered_title),
    )


def render_grouped_ggdotplotstats(
    analysis: GroupedAnalysis[DotPlotAnalysis],
    *,
    show_intervals: bool = True,
    title: str | None = None,
) -> GroupedStatsPlot[DotPlotResult]:
    """Render one labeled dot plot per retained group."""

    plots = tuple(
        render_ggdotplotstats(
            item.analysis,
            show_intervals=show_intervals,
            title=f"{analysis.result.group_column} = {item.group}",
        )
        for item in analysis.groups
    )
    rendered_title = title or f"Grouped dot plots by {analysis.result.group_column}"
    return GroupedStatsPlot(
        plots=plots,
        result=analysis.result,
        annotations=group_annotations(analysis.result, rendered_title),
    )


def render_grouped_ggscatterstats(
    analysis: GroupedAnalysis[CorrelationAnalysis],
    *,
    title: str | None = None,
) -> GroupedStatsPlot[CorrelationResult]:
    """Render one Pearson scatter plot per retained group."""

    plots = tuple(
        render_ggscatterstats(
            item.analysis,
            title=f"{analysis.result.group_column} = {item.group}",
        )
        for item in analysis.groups
    )
    rendered_title = title or f"Grouped associations by {analysis.result.group_column}"
    return GroupedStatsPlot(
        plots=plots,
        result=analysis.result,
        annotations=group_annotations(analysis.result, rendered_title),
    )


def render_grouped_ggcorrmat(
    analysis: GroupedAnalysis[CorrelationMatrixAnalysis],
    *,
    title: str | None = None,
) -> GroupedStatsPlot[CorrelationMatrixResult]:
    """Render one Pearson correlation matrix per retained group."""

    plots = tuple(
        render_ggcorrmat(
            item.analysis,
            title=f"{analysis.result.group_column} = {item.group}",
        )
        for item in analysis.groups
    )
    rendered_title = (
        title or f"Grouped correlation matrices by {analysis.result.group_column}"
    )
    return GroupedStatsPlot(
        plots=plots,
        result=analysis.result,
        annotations=group_annotations(analysis.result, rendered_title),
    )


def grouped_gghistostats(
    data: object,
    x: str,
    group: str,
    *,
    test_value: float = 0.0,
    alternative: Alternative = "two-sided",
    conf_level: float = 0.95,
    maximum_rows: int = DEFAULT_MAX_ROWS,
    maximum_groups: int = DEFAULT_MAX_GROUPS,
    type: str = "parametric",
    trim_fraction: float = TRIM_FRACTION,
    prior_scale: float | None = None,
    credible_level: float = 0.95,
    maximum_bayesian_work: int = DEFAULT_MAX_BAYESIAN_WORK,
    binwidth: float | None = None,
    title: str | None = None,
) -> GroupedStatsPlot[AnalysisResult]:
    """Analyze and render parametric histograms by group."""

    analysis = analyze_grouped_gghistostats(
        data,
        x,
        group,
        test_value=test_value,
        alternative=alternative,
        conf_level=conf_level,
        maximum_rows=maximum_rows,
        maximum_groups=maximum_groups,
        type=type,
        trim_fraction=trim_fraction,
        prior_scale=prior_scale,
        credible_level=credible_level,
        maximum_bayesian_work=maximum_bayesian_work,
    )
    return render_grouped_gghistostats(
        analysis,
        binwidth=binwidth,
        title=title,
    )


def grouped_ggdotplotstats(
    data: object,
    x: str,
    y: str,
    group: str,
    *,
    test_value: float = 0.0,
    alternative: Alternative = "two-sided",
    conf_level: float = 0.95,
    maximum_rows: int = DEFAULT_MAX_ROWS,
    maximum_groups: int = DEFAULT_MAX_GROUPS,
    maximum_labels: int = DEFAULT_MAX_LABELS,
    type: str = "parametric",
    trim_fraction: float = TRIM_FRACTION,
    prior_scale: float | None = None,
    credible_level: float = 0.95,
    maximum_bayesian_work: int = DEFAULT_MAX_BAYESIAN_WORK,
    show_intervals: bool = True,
    title: str | None = None,
) -> GroupedStatsPlot[DotPlotResult]:
    """Analyze and render parametric labeled dot plots by group."""

    analysis = analyze_grouped_ggdotplotstats(
        data,
        x,
        y,
        group,
        test_value=test_value,
        alternative=alternative,
        conf_level=conf_level,
        maximum_rows=maximum_rows,
        maximum_groups=maximum_groups,
        maximum_labels=maximum_labels,
        type=type,
        trim_fraction=trim_fraction,
        prior_scale=prior_scale,
        credible_level=credible_level,
        maximum_bayesian_work=maximum_bayesian_work,
    )
    return render_grouped_ggdotplotstats(
        analysis,
        show_intervals=show_intervals,
        title=title,
    )


def grouped_ggscatterstats(
    data: object,
    x: str,
    y: str,
    group: str,
    *,
    conf_level: float = 0.95,
    maximum_rows: int = DEFAULT_MAX_ROWS,
    maximum_groups: int = DEFAULT_MAX_GROUPS,
    type: str = "parametric",
    trim_fraction: float = TRIM_FRACTION,
    bootstrap_resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
    random_seed: int | None = None,
    maximum_resample_work: int = DEFAULT_MAX_RESAMPLE_WORK,
    correlation_prior_shape: float = 1.0,
    credible_level: float = 0.95,
    maximum_bayesian_work: int = DEFAULT_MAX_BAYESIAN_WORK,
    title: str | None = None,
) -> GroupedStatsPlot[CorrelationResult]:
    """Analyze and render Pearson scatter plots by group."""

    analysis = analyze_grouped_ggscatterstats(
        data,
        x,
        y,
        group,
        conf_level=conf_level,
        maximum_rows=maximum_rows,
        maximum_groups=maximum_groups,
        type=type,
        trim_fraction=trim_fraction,
        bootstrap_resamples=bootstrap_resamples,
        random_seed=random_seed,
        maximum_resample_work=maximum_resample_work,
        correlation_prior_shape=correlation_prior_shape,
        credible_level=credible_level,
        maximum_bayesian_work=maximum_bayesian_work,
    )
    return render_grouped_ggscatterstats(analysis, title=title)


def grouped_ggcorrmat(
    data: object,
    columns: list[str] | tuple[str, ...],
    group: str,
    *,
    conf_level: float = 0.95,
    sig_level: float = 0.05,
    p_adjust: str = "holm",
    maximum_rows: int = DEFAULT_MAX_ROWS,
    maximum_groups: int = DEFAULT_MAX_GROUPS,
    type: str = "parametric",
    trim_fraction: float = TRIM_FRACTION,
    bootstrap_resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
    random_seed: int | None = None,
    maximum_resample_work: int = DEFAULT_MAX_RESAMPLE_WORK,
    correlation_prior_shape: float = 1.0,
    credible_level: float = 0.95,
    maximum_bayesian_work: int = DEFAULT_MAX_BAYESIAN_WORK,
    title: str | None = None,
) -> GroupedStatsPlot[CorrelationMatrixResult]:
    """Analyze and render Pearson correlation matrices by group."""

    analysis = analyze_grouped_ggcorrmat(
        data,
        columns,
        group,
        conf_level=conf_level,
        sig_level=sig_level,
        p_adjust=p_adjust,
        maximum_rows=maximum_rows,
        maximum_groups=maximum_groups,
        type=type,
        trim_fraction=trim_fraction,
        bootstrap_resamples=bootstrap_resamples,
        random_seed=random_seed,
        maximum_resample_work=maximum_resample_work,
        correlation_prior_shape=correlation_prior_shape,
        credible_level=credible_level,
        maximum_bayesian_work=maximum_bayesian_work,
    )
    return render_grouped_ggcorrmat(analysis, title=title)
