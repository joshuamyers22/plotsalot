"""Renderer-facing contracts for figures, axes, and annotations."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Generic, Protocol, TypeVar

from matplotlib.axes import Axes
from matplotlib.figure import Figure

from plotsalot.result import GroupedResult, StructuredResult

ResultT = TypeVar("ResultT", bound=StructuredResult)
ResultT_co = TypeVar("ResultT_co", bound=StructuredResult, covariant=True)


class PlotResultContainer(Protocol[ResultT_co]):
    """Common extraction surface for individual and grouped plot containers."""

    @property
    def result(self) -> ResultT_co: ...

    @property
    def title(self) -> str: ...

    @property
    def subtitle(self) -> str: ...

    @property
    def caption(self) -> str: ...


@dataclass(frozen=True, slots=True)
class PlotAnnotations:
    """Text rendered from structured result fields."""

    title: str
    subtitle: str
    caption: str

    def __post_init__(self) -> None:
        if not self.title:
            raise ValueError("plot title must be non-empty")


@dataclass(frozen=True, slots=True)
class StatsPlot(Generic[ResultT]):
    """A validated Matplotlib figure paired with a structured result."""

    figure: Figure
    axes: Mapping[str, Axes]
    result: ResultT
    annotations: PlotAnnotations

    def __post_init__(self) -> None:
        if not self.axes:
            raise ValueError("axes must contain at least one named axis")

        owned_axes = dict(self.axes)
        for name, axis in owned_axes.items():
            if not name:
                raise ValueError("axis names must be non-empty")
            if axis.figure is not self.figure:
                raise ValueError(f"axis {name!r} does not belong to figure")
        object.__setattr__(self, "axes", MappingProxyType(owned_axes))

    @property
    def title(self) -> str:
        """Return the rendered title source."""

        return self.annotations.title

    @property
    def subtitle(self) -> str:
        """Return the rendered subtitle source."""

        return self.annotations.subtitle

    @property
    def caption(self) -> str:
        """Return the rendered caption source."""

        return self.annotations.caption


@dataclass(frozen=True, slots=True)
class GroupedStatsPlot(Generic[ResultT]):
    """An atomic grouped result paired with one validated plot per group."""

    plots: tuple[StatsPlot[ResultT], ...]
    result: GroupedResult
    annotations: PlotAnnotations

    def __post_init__(self) -> None:
        if not self.plots:
            raise ValueError("grouped plot requires at least one plot")
        if len(self.plots) != len(self.result.groups):
            raise ValueError("grouped plot and result counts must match")
        for plot, item in zip(self.plots, self.result.groups, strict=True):
            if plot.result is not item.result:
                raise ValueError("grouped plot results must match by identity")

    @property
    def title(self) -> str:
        """Return the grouped title source."""

        return self.annotations.title

    @property
    def subtitle(self) -> str:
        """Return the grouped subtitle source."""

        return self.annotations.subtitle

    @property
    def caption(self) -> str:
        """Return the grouped caption source."""

        return self.annotations.caption


def extract_stats(plot: PlotResultContainer[ResultT]) -> ResultT:
    """Return the renderer-independent result attached to a plot."""

    return plot.result


def extract_subtitle(plot: PlotResultContainer[StructuredResult]) -> str:
    """Return the rendered statistical subtitle source."""

    return plot.subtitle


def extract_caption(plot: PlotResultContainer[StructuredResult]) -> str:
    """Return the rendered caption source."""

    return plot.caption
