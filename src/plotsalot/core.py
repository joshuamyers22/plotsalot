"""Stable result objects shared by analysis and rendering."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any

from matplotlib.axes import Axes
from matplotlib.figure import Figure


@dataclass(frozen=True, slots=True)
class SampleAudit:
    """Counts that reconcile the caller's input with the analyzed sample."""

    input_rows: int
    analyzed_rows: int
    dropped_null_rows: int


@dataclass(frozen=True, slots=True)
class EstimateResult:
    """Point estimate and the sample scale used by the prototype."""

    name: str
    value: float
    standard_deviation: float


@dataclass(frozen=True, slots=True)
class TestResult:
    """One-sample hypothesis-test result."""

    name: str
    null_value: float
    alternative: str
    statistic: float
    df: float
    p_value: float


@dataclass(frozen=True, slots=True)
class IntervalResult:
    """Confidence interval with explicit target and construction method."""

    target: str
    method: str
    level: float
    low: float
    high: float


@dataclass(frozen=True, slots=True)
class EffectSizeResult:
    """Effect-size estimate and its standardization convention."""

    name: str
    value: float
    standardizer: str


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    """Versioned, renderer-independent result for the M0 walking skeleton."""

    schema_version: int
    analysis: str
    column: str
    sample: SampleAudit
    estimate: EstimateResult
    test: TestResult
    interval: IntervalResult
    effect_size: EffectSizeResult
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        return asdict(self)


@dataclass(slots=True)
class StatsPlot:
    """A Matplotlib figure paired with its structured statistical result."""

    figure: Figure
    axes: Mapping[str, Axes]
    result: AnalysisResult
    subtitle: str
    caption: str
