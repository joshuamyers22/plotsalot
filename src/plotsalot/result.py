"""Versioned, renderer-independent statistical result contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class SampleAudit:
    """Counts that reconcile the caller's input with the analyzed sample."""

    input_rows: int
    analyzed_rows: int
    dropped_null_rows: int

    def __post_init__(self) -> None:
        if min(self.input_rows, self.analyzed_rows, self.dropped_null_rows) < 0:
            raise ValueError("sample counts must be non-negative")
        if self.input_rows != self.analyzed_rows + self.dropped_null_rows:
            raise ValueError(
                "input_rows must equal analyzed_rows plus dropped_null_rows"
            )


@dataclass(frozen=True, slots=True)
class EstimateResult:
    """Point estimate and the sample scale used by the histogram method."""

    name: str
    value: float
    standard_deviation: float

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("estimate name must be non-empty")
        if not isfinite(self.value):
            raise ValueError("estimate value must be finite")
        if not isfinite(self.standard_deviation) or self.standard_deviation <= 0.0:
            raise ValueError("estimate standard_deviation must be finite and positive")


@dataclass(frozen=True, slots=True)
class TestResult:
    """One-sample hypothesis-test result."""

    name: str
    null_value: float
    alternative: str
    statistic: float
    df: float
    p_value: float

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("test name must be non-empty")
        if self.alternative not in {"two-sided", "less", "greater"}:
            raise ValueError("test alternative is unsupported")
        if not all(isfinite(value) for value in (self.null_value, self.statistic)):
            raise ValueError("test values must be finite")
        if not isfinite(self.df) or self.df < 1.0:
            raise ValueError("test df must be finite and at least one")
        if not isfinite(self.p_value) or not 0.0 <= self.p_value <= 1.0:
            raise ValueError("test p_value must be finite and between zero and one")


@dataclass(frozen=True, slots=True)
class IntervalResult:
    """Confidence interval with explicit target and construction method."""

    target: str
    method: str
    level: float
    low: float
    high: float

    def __post_init__(self) -> None:
        if not self.target or not self.method:
            raise ValueError("interval target and method must be non-empty")
        if not isfinite(self.level) or not 0.0 < self.level < 1.0:
            raise ValueError("interval level must be strictly between zero and one")
        if not isfinite(self.low) or not isfinite(self.high) or self.low > self.high:
            raise ValueError("interval bounds must be finite and ordered")


@dataclass(frozen=True, slots=True)
class EffectSizeResult:
    """Effect-size estimate and its standardization convention."""

    name: str
    value: float
    standardizer: str

    def __post_init__(self) -> None:
        if not self.name or not self.standardizer:
            raise ValueError("effect-size name and standardizer must be non-empty")
        if not isfinite(self.value):
            raise ValueError("effect-size value must be finite")


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    """Schema-v1 renderer-independent result for the histogram method."""

    schema_version: int
    analysis: str
    column: str
    sample: SampleAudit
    estimate: EstimateResult
    test: TestResult
    interval: IntervalResult
    effect_size: EffectSizeResult
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("histogram analysis schema_version must be 1")
        if not self.analysis or not self.column:
            raise ValueError("analysis and column must be non-empty")
        if self.analysis != "gghistostats_one_sample_parametric":
            raise ValueError("analysis identity is unsupported by this result schema")
        if self.estimate.name != "mean":
            raise ValueError("histogram estimate must be the mean")
        if self.test.name != "one_sample_t":
            raise ValueError("histogram test must be one_sample_t")
        if not self.interval.low <= self.estimate.value <= self.interval.high:
            raise ValueError("mean estimate must lie within its confidence interval")
        if any(not warning for warning in self.warnings):
            raise ValueError("warnings must not contain empty strings")

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-serializable representation."""

        return asdict(self)


class StructuredResult(Protocol):
    """Minimum behavior required for a result attached to a plot."""

    @property
    def schema_version(self) -> int: ...

    @property
    def analysis(self) -> str: ...

    def to_dict(self) -> dict[str, Any]: ...
