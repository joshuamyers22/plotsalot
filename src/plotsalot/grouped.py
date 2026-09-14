"""Atomic grouped analyses and per-group plot containers."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Generic, TypeVar

import polars as pl

from plotsalot.correlation import render_ggcorrmat, render_ggscatterstats
from plotsalot.correlation_analysis import (
    CorrelationAnalysis,
    CorrelationMatrixAnalysis,
    analyze_ggcorrmat,
    analyze_ggscatterstats,
)
from plotsalot.data import DEFAULT_MAX_ROWS, select_numeric_sample
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
    analyze_one_sample_sample,
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


def _split_groups(
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


def _grouped_result(
    *,
    analysis: str,
    group_column: str,
    sample: GroupSampleAudit,
    correction_scope: str,
    items: tuple[GroupResultItem, ...],
    limits: ResourceLimits,
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
    )


def _group_error(group: GroupIdentity, error: Exception) -> ValueError:
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
) -> GroupedAnalysis[HistogramAnalysis]:
    """Apply the approved histogram analysis atomically by group."""

    partitions, sample = _split_groups(
        data,
        group,
        maximum_rows=maximum_rows,
        maximum_groups=maximum_groups,
    )
    groups: list[GroupAnalysisItem[HistogramAnalysis]] = []
    results: list[GroupResultItem] = []
    for partition in partitions:
        try:
            item_sample = select_numeric_sample(
                partition.data,
                x,
                minimum_size=2,
                require_variation=True,
                maximum_rows=maximum_rows,
            )
            item_analysis = analyze_one_sample_sample(
                item_sample,
                analysis="gghistostats_one_sample_parametric",
                test_value=test_value,
                alternative=alternative,
                conf_level=conf_level,
            )
        except (TypeError, ValueError) as error:
            raise _group_error(partition.group, error) from error
        groups.append(GroupAnalysisItem(partition.group, item_analysis))
        results.append(GroupResultItem(partition.group, item_analysis.result))
    return GroupedAnalysis(
        groups=tuple(groups),
        result=_grouped_result(
            analysis="grouped_gghistostats_one_sample_parametric",
            group_column=group,
            sample=sample,
            correction_scope="none_across_groups",
            items=tuple(results),
            limits=ResourceLimits(
                maximum_rows=maximum_rows,
                maximum_groups=maximum_groups,
            ),
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
) -> GroupedAnalysis[DotPlotAnalysis]:
    """Apply the approved labeled dot-plot analysis atomically by group."""

    partitions, sample = _split_groups(
        data,
        group,
        maximum_rows=maximum_rows,
        maximum_groups=maximum_groups,
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
            )
        except (TypeError, ValueError) as error:
            raise _group_error(partition.group, error) from error
        groups.append(GroupAnalysisItem(partition.group, item_analysis))
        results.append(GroupResultItem(partition.group, item_analysis.result))
    return GroupedAnalysis(
        groups=tuple(groups),
        result=_grouped_result(
            analysis="grouped_ggdotplotstats_one_sample_parametric",
            group_column=group,
            sample=sample,
            correction_scope="none_across_groups",
            items=tuple(results),
            limits=ResourceLimits(
                maximum_rows=maximum_rows,
                maximum_groups=maximum_groups,
                maximum_labels=maximum_labels,
            ),
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
) -> GroupedAnalysis[CorrelationAnalysis]:
    """Apply the approved Pearson scatter analysis atomically by group."""

    partitions, sample = _split_groups(
        data,
        group,
        maximum_rows=maximum_rows,
        maximum_groups=maximum_groups,
    )
    groups: list[GroupAnalysisItem[CorrelationAnalysis]] = []
    results: list[GroupResultItem] = []
    for partition in partitions:
        try:
            item_analysis = analyze_ggscatterstats(
                partition.data,
                x,
                y,
                conf_level=conf_level,
                maximum_rows=maximum_rows,
            )
        except (TypeError, ValueError) as error:
            raise _group_error(partition.group, error) from error
        groups.append(GroupAnalysisItem(partition.group, item_analysis))
        results.append(GroupResultItem(partition.group, item_analysis.result))
    return GroupedAnalysis(
        groups=tuple(groups),
        result=_grouped_result(
            analysis="grouped_ggscatterstats_pearson",
            group_column=group,
            sample=sample,
            correction_scope="none_across_groups",
            items=tuple(results),
            limits=ResourceLimits(
                maximum_rows=maximum_rows,
                maximum_groups=maximum_groups,
            ),
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
) -> GroupedAnalysis[CorrelationMatrixAnalysis]:
    """Apply the approved Pearson matrix analysis atomically by group."""

    partitions, sample = _split_groups(
        data,
        group,
        maximum_rows=maximum_rows,
        maximum_groups=maximum_groups,
    )
    groups: list[GroupAnalysisItem[CorrelationMatrixAnalysis]] = []
    results: list[GroupResultItem] = []
    for partition in partitions:
        try:
            item_analysis = analyze_ggcorrmat(
                partition.data,
                columns,
                conf_level=conf_level,
                sig_level=sig_level,
                p_adjust=p_adjust,
                maximum_rows=maximum_rows,
            )
        except (TypeError, ValueError) as error:
            raise _group_error(partition.group, error) from error
        groups.append(GroupAnalysisItem(partition.group, item_analysis))
        results.append(GroupResultItem(partition.group, item_analysis.result))
    return GroupedAnalysis(
        groups=tuple(groups),
        result=_grouped_result(
            analysis="grouped_ggcorrmat_pearson",
            group_column=group,
            sample=sample,
            correction_scope="within_group_matrix",
            items=tuple(results),
            limits=ResourceLimits(
                maximum_rows=maximum_rows,
                maximum_groups=maximum_groups,
                maximum_variables=50,
            ),
        ),
    )


def _group_annotations(result: GroupedResult, title: str) -> PlotAnnotations:
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
        annotations=_group_annotations(analysis.result, rendered_title),
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
        annotations=_group_annotations(analysis.result, rendered_title),
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
        annotations=_group_annotations(analysis.result, rendered_title),
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
        annotations=_group_annotations(analysis.result, rendered_title),
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
    )
    return render_grouped_ggcorrmat(analysis, title=title)
