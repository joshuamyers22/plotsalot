"""Result-preserving composition for plotsalot plot containers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from math import ceil, isfinite, sqrt
from types import MappingProxyType
from typing import Any, Protocol, cast

import numpy as np
from matplotlib.axes import Axes
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from numpy.typing import NDArray

from plotsalot.plot import GroupedStatsPlot, PlotAnnotations, StatsPlot
from plotsalot.result import GroupIdentity, ResourceLimits, StructuredResult

DEFAULT_MAX_PANELS = 20


class _PanelAxes(Protocol):
    transAxes: object

    def imshow(self, image: object) -> object: ...

    def set_axis_off(self) -> None: ...

    def text(
        self,
        x: float,
        y: float,
        text: str,
        *,
        transform: object,
        ha: str,
        va: str,
        fontweight: str,
    ) -> object: ...


class _CompositionFigure(Protocol):
    def suptitle(self, title: str) -> object: ...

    def supxlabel(self, label: str) -> object: ...

    def supylabel(self, label: str) -> object: ...


@dataclass(frozen=True, slots=True)
class CompositionPanelResult:
    """One source result and its deterministic composed-panel identity."""

    panel: str
    source_index: int
    group: GroupIdentity | None
    title: str
    tag: str | None
    result: StructuredResult

    def __post_init__(self) -> None:
        if not self.panel or not self.title:
            raise ValueError("composition panel identity and title must be non-empty")
        if type(self.source_index) is not int or self.source_index < 0:
            raise ValueError("composition source_index must be non-negative")
        if isinstance(self.group, str) and not self.group:
            raise ValueError("composition group identity must be non-empty")
        if isinstance(self.group, float) and not isfinite(self.group):
            raise ValueError("composition numeric group identity must be finite")
        if self.tag is not None and not self.tag:
            raise ValueError("composition panel tag must be non-empty when present")


@dataclass(frozen=True, slots=True)
class CompositionResult:
    """Schema-v1 layout metadata retaining every source statistical result."""

    schema_version: int
    analysis: str
    rows: int
    columns: int
    guides: str
    x_label: str | None
    y_label: str | None
    panel_tags: str | None
    panels: tuple[CompositionPanelResult, ...]
    limits: ResourceLimits
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.schema_version != 1 or self.analysis != "combine_plots":
            raise ValueError("composition result identity is unsupported")
        if min(self.rows, self.columns) < 1:
            raise ValueError("composition dimensions must be positive")
        if not self.panels or self.rows * self.columns < len(self.panels):
            raise ValueError("composition grid must contain every panel")
        if self.guides != "keep":
            raise ValueError("only guides='keep' is supported")
        if self.x_label is not None and not self.x_label:
            raise ValueError("composition x_label must be non-empty when supplied")
        if self.y_label is not None and not self.y_label:
            raise ValueError("composition y_label must be non-empty when supplied")
        if self.panel_tags not in {None, "A", "a", "1"}:
            raise ValueError("panel_tags must be None, 'A', 'a', or '1'")
        if any(
            (panel.tag is not None) != (self.panel_tags is not None)
            for panel in self.panels
        ):
            raise ValueError("composition panel tags must match the tag policy")
        if self.limits.maximum_panels is None:
            raise ValueError("composition result must retain maximum_panels")
        if len(self.panels) > self.limits.maximum_panels:
            raise ValueError("composition panels exceed the retained ceiling")
        panel_names = tuple(panel.panel for panel in self.panels)
        if len(set(panel_names)) != len(panel_names):
            raise ValueError("composition panel names must be unique")
        if any(not warning for warning in self.warnings):
            raise ValueError("composition warnings must not contain empty strings")

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-serializable representation."""

        return {
            "schema_version": self.schema_version,
            "analysis": self.analysis,
            "rows": self.rows,
            "columns": self.columns,
            "guides": self.guides,
            "x_label": self.x_label,
            "y_label": self.y_label,
            "panel_tags": self.panel_tags,
            "panels": [
                {
                    "panel": panel.panel,
                    "source_index": panel.source_index,
                    "group": panel.group,
                    "title": panel.title,
                    "tag": panel.tag,
                    "result": panel.result.to_dict(),
                }
                for panel in self.panels
            ],
            "limits": {
                "maximum_rows": self.limits.maximum_rows,
                "maximum_groups": self.limits.maximum_groups,
                "maximum_variables": self.limits.maximum_variables,
                "maximum_labels": self.limits.maximum_labels,
                "maximum_levels": self.limits.maximum_levels,
                "maximum_pairwise_hypotheses": (
                    self.limits.maximum_pairwise_hypotheses
                ),
                "maximum_rendered_observations": (
                    self.limits.maximum_rendered_observations
                ),
                "maximum_subject_paths": self.limits.maximum_subject_paths,
                "maximum_panels": self.limits.maximum_panels,
            },
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True, slots=True)
class ComposedStatsPlot:
    """A composed figure paired with every retained source result."""

    figure: Figure
    axes: Mapping[str, Axes]
    result: CompositionResult
    annotations: PlotAnnotations

    def __post_init__(self) -> None:
        owned_axes = dict(self.axes)
        if tuple(owned_axes) != tuple(panel.panel for panel in self.result.panels):
            raise ValueError("composed axes must match result panel order")
        if any(axis.figure is not self.figure for axis in owned_axes.values()):
            raise ValueError("composed axes must belong to the composed figure")
        object.__setattr__(self, "axes", MappingProxyType(owned_axes))

    @property
    def title(self) -> str:
        return self.annotations.title

    @property
    def subtitle(self) -> str:
        return self.annotations.subtitle

    @property
    def caption(self) -> str:
        return self.annotations.caption


@dataclass(frozen=True, slots=True)
class _SourcePanel:
    source_index: int
    group: GroupIdentity | None
    plot: StatsPlot[StructuredResult]


def _flatten_sources(plotlist: Sequence[object]) -> tuple[_SourcePanel, ...]:
    panels: list[_SourcePanel] = []
    for source_index, candidate in enumerate(plotlist):
        if isinstance(candidate, StatsPlot):
            panels.append(
                _SourcePanel(
                    source_index=source_index,
                    group=None,
                    plot=cast(StatsPlot[StructuredResult], candidate),
                )
            )
            continue
        if isinstance(candidate, GroupedStatsPlot):
            grouped = cast(GroupedStatsPlot[StructuredResult], candidate)
            for item, plot in zip(grouped.result.groups, grouped.plots, strict=True):
                panels.append(
                    _SourcePanel(
                        source_index=source_index,
                        group=item.group,
                        plot=plot,
                    )
                )
            continue
        raise TypeError(
            f"plotlist item {source_index} must be StatsPlot or GroupedStatsPlot"
        )
    return tuple(panels)


def _layout(panel_count: int, rows: int | None, columns: int | None) -> tuple[int, int]:
    for name, value in (("rows", rows), ("columns", columns)):
        if value is not None and (type(value) is not int or value < 1):
            raise ValueError(f"{name} must be a positive integer when supplied")
    if rows is None and columns is None:
        columns = int(ceil(sqrt(panel_count)))
        rows = int(ceil(panel_count / columns))
    elif rows is None:
        if columns is None:
            raise RuntimeError("composition columns unexpectedly absent")
        rows = int(ceil(panel_count / columns))
    elif columns is None:
        columns = int(ceil(panel_count / rows))
    if rows * columns < panel_count:
        raise ValueError("requested composition grid cannot contain every panel")
    return rows, columns


def _rasterize(figure: Figure) -> NDArray[np.uint8]:
    original_canvas = figure.canvas
    canvas = FigureCanvasAgg(figure)
    try:
        canvas.draw()
        image = np.asarray(canvas.buffer_rgba(), dtype=np.uint8).copy()
    finally:
        figure.set_canvas(original_canvas)
    return image


def _panel_tag(policy: str | None, index: int) -> str | None:
    if policy is None:
        return None
    if policy == "1":
        return str(index)
    return chr(ord(policy) + index - 1)


def combine_plots(
    plotlist: Sequence[object],
    *,
    rows: int | None = None,
    columns: int | None = None,
    guides: str = "keep",
    title: str = "Combined plots",
    subtitle: str = "",
    caption: str = "",
    x_label: str | None = None,
    y_label: str | None = None,
    panel_tags: str | None = None,
    maximum_panels: int = DEFAULT_MAX_PANELS,
) -> ComposedStatsPlot:
    """Arrange plots while retaining every source typed result by identity."""

    if isinstance(plotlist, (str, bytes)):
        raise TypeError("plotlist must be a sequence of plotsalot plot containers")
    if not plotlist:
        raise ValueError("plotlist must contain at least one plot")
    if guides != "keep":
        raise ValueError("guides must be 'keep'; guide collection is unsupported")
    if not title:
        raise ValueError("composition title must be non-empty")
    if x_label is not None and not x_label:
        raise ValueError("x_label must be non-empty when supplied")
    if y_label is not None and not y_label:
        raise ValueError("y_label must be non-empty when supplied")
    if panel_tags not in {None, "A", "a", "1"}:
        raise ValueError("panel_tags must be None, 'A', 'a', or '1'")
    if type(maximum_panels) is not int or maximum_panels < 1:
        raise ValueError("maximum_panels must be a positive integer")
    sources = _flatten_sources(plotlist)
    if len(sources) > maximum_panels:
        raise ValueError(f"panel count exceeds maximum_panels={maximum_panels}")
    resolved_rows, resolved_columns = _layout(len(sources), rows, columns)

    figure = Figure(layout="constrained")
    raw_axes = np.asarray(
        figure.subplots(resolved_rows, resolved_columns, squeeze=False),
        dtype=object,
    )
    axes: dict[str, Axes] = {}
    panel_results: list[CompositionPanelResult] = []
    flattened_axes = tuple(raw_axes.flat)
    for index, (source, axis) in enumerate(
        zip(sources, flattened_axes, strict=False), start=1
    ):
        panel_name = f"panel_{index}"
        typed_axis = cast(Axes, axis)
        renderer = cast(_PanelAxes, typed_axis)
        renderer.imshow(_rasterize(source.plot.figure))
        renderer.set_axis_off()
        tag = _panel_tag(panel_tags, index)
        if tag is not None:
            renderer.text(
                0.01,
                0.99,
                tag,
                transform=renderer.transAxes,
                ha="left",
                va="top",
                fontweight="bold",
            )
        axes[panel_name] = typed_axis
        panel_results.append(
            CompositionPanelResult(
                panel=panel_name,
                source_index=source.source_index,
                group=source.group,
                title=source.plot.title,
                tag=tag,
                result=source.plot.result,
            )
        )
    for axis in flattened_axes[len(sources) :]:
        cast(_PanelAxes, axis).set_axis_off()
    figure_renderer = cast(_CompositionFigure, figure)
    figure_renderer.suptitle(title)
    if x_label is not None:
        figure_renderer.supxlabel(x_label)
    if y_label is not None:
        figure_renderer.supylabel(y_label)
    result = CompositionResult(
        schema_version=1,
        analysis="combine_plots",
        rows=resolved_rows,
        columns=resolved_columns,
        guides=guides,
        x_label=x_label,
        y_label=y_label,
        panel_tags=panel_tags,
        panels=tuple(panel_results),
        limits=ResourceLimits(maximum_rows=1, maximum_panels=maximum_panels),
        warnings=("source figures are rasterized into composed panels",),
    )
    return ComposedStatsPlot(
        figure=figure,
        axes=axes,
        result=result,
        annotations=PlotAnnotations(title=title, subtitle=subtitle, caption=caption),
    )
