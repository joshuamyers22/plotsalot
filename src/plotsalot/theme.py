"""Owned Matplotlib styling for plotsalot figures."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol, cast

from matplotlib.axes import Axes


class _ThemeFigure(Protocol):
    def set_facecolor(self, color: str) -> None: ...


class _ThemeText(Protocol):
    def set_color(self, color: str) -> None: ...

    def set_fontsize(self, size: float) -> None: ...

    def set_fontweight(self, weight: str) -> None: ...


class _ThemeAxis(Protocol):
    label: _ThemeText


class _ThemeSpine(Protocol):
    def set_visible(self, visible: bool) -> None: ...


class _ThemeAxes(Protocol):
    figure: _ThemeFigure
    title: _ThemeText
    xaxis: _ThemeAxis
    yaxis: _ThemeAxis
    spines: Mapping[str, _ThemeSpine]

    def set_facecolor(self, color: str) -> None: ...

    def grid(self, *, axis: str, color: str, alpha: float) -> None: ...

    def set_axisbelow(self, below: bool) -> None: ...

    def tick_params(self, *, colors: str) -> None: ...


@dataclass(frozen=True, slots=True)
class StatsTheme:
    """A local style contract that never mutates process-global rcParams."""

    axes_facecolor: str = "white"
    figure_facecolor: str = "white"
    grid_color: str = "#d9d9d9"
    text_color: str = "#222222"
    accent_color: str = "#8b1a1a"
    grid_alpha: float = 0.55
    title_size: float = 12.0
    label_size: float = 10.0

    def __post_init__(self) -> None:
        colors = (
            self.axes_facecolor,
            self.figure_facecolor,
            self.grid_color,
            self.text_color,
            self.accent_color,
        )
        if any(not color for color in colors):
            raise ValueError("theme colors must be non-empty")
        if not 0.0 <= self.grid_alpha <= 1.0:
            raise ValueError("theme grid_alpha must lie within [0, 1]")
        if self.title_size <= 0.0 or self.label_size <= 0.0:
            raise ValueError("theme text sizes must be positive")

    def apply(self, axes: Axes) -> None:
        """Apply this theme only to the supplied axis and its owning figure."""

        renderer = cast(_ThemeAxes, axes)
        renderer.figure.set_facecolor(self.figure_facecolor)
        renderer.set_facecolor(self.axes_facecolor)
        renderer.grid(axis="y", color=self.grid_color, alpha=self.grid_alpha)
        renderer.set_axisbelow(True)
        renderer.title.set_color(self.text_color)
        renderer.title.set_fontsize(self.title_size)
        renderer.title.set_fontweight("bold")
        renderer.xaxis.label.set_color(self.text_color)
        renderer.yaxis.label.set_color(self.text_color)
        renderer.xaxis.label.set_fontsize(self.label_size)
        renderer.yaxis.label.set_fontsize(self.label_size)
        renderer.tick_params(colors=self.text_color)
        for spine in renderer.spines.values():
            spine.set_visible(False)


def theme_ggstatsplot() -> StatsTheme:
    """Return the default owned theme used by M3 plots."""

    return StatsTheme()
