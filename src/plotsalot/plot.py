"""Renderer-facing contracts for figures, axes, and annotations."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Generic, TypeVar

from matplotlib.axes import Axes
from matplotlib.figure import Figure

from plotsalot.result import StructuredResult

ResultT = TypeVar("ResultT", bound=StructuredResult)


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


def extract_stats(plot: StatsPlot[ResultT]) -> ResultT:
    """Return the renderer-independent result attached to a plot."""

    return plot.result


def extract_subtitle(plot: StatsPlot[ResultT]) -> str:
    """Return the rendered statistical subtitle source."""

    return plot.subtitle


def extract_caption(plot: StatsPlot[ResultT]) -> str:
    """Return the rendered caption source."""

    return plot.caption
