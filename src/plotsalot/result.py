"""Versioned, renderer-independent statistical result contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any, Protocol, TypeAlias

ScalarIdentity: TypeAlias = str | int | float | bool
GroupIdentity: TypeAlias = ScalarIdentity


class StructuredResult(Protocol):
    """Minimum behavior required for a result attached to a plot."""

    @property
    def schema_version(self) -> int: ...

    @property
    def analysis(self) -> str: ...

    def to_dict(self) -> dict[str, Any]: ...


@dataclass(frozen=True, slots=True)
class ResourceLimits:
    """Configured workload ceilings retained with an M2 result."""

    maximum_rows: int
    maximum_groups: int | None = None
    maximum_variables: int | None = None
    maximum_labels: int | None = None
    maximum_levels: int | None = None
    maximum_pairwise_hypotheses: int | None = None
    maximum_rendered_observations: int | None = None
    maximum_subject_paths: int | None = None
    maximum_panels: int | None = None

    def __post_init__(self) -> None:
        values = (
            self.maximum_rows,
            self.maximum_groups,
            self.maximum_variables,
            self.maximum_labels,
            self.maximum_levels,
            self.maximum_pairwise_hypotheses,
            self.maximum_rendered_observations,
            self.maximum_subject_paths,
            self.maximum_panels,
        )
        if any(
            value is not None and (type(value) is not int or value < 1)
            for value in values
        ):
            raise ValueError("resource limits must be positive when present")


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
        if self.analysis not in {
            "gghistostats_one_sample_parametric",
            "ggdotplotstats_one_sample_parametric",
        }:
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


@dataclass(frozen=True, slots=True)
class DotEstimateResult:
    """One labeled mean and its optional estimation interval."""

    label: ScalarIdentity
    sample: SampleAudit
    value: float
    standard_deviation: float | None
    interval: IntervalResult | None
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        if isinstance(self.label, str) and not self.label:
            raise ValueError("dot estimate label must be non-empty")
        if isinstance(self.label, float) and not isfinite(self.label):
            raise ValueError("numeric dot estimate label must be finite")
        if not isfinite(self.value):
            raise ValueError("dot estimate value must be finite")
        if self.standard_deviation is not None and (
            not isfinite(self.standard_deviation) or self.standard_deviation <= 0.0
        ):
            raise ValueError(
                "dot estimate standard_deviation must be finite and positive"
            )
        if (self.standard_deviation is None) != (self.interval is None):
            raise ValueError(
                "dot estimate deviation and interval must both be present or absent"
            )
        if self.interval is not None:
            if self.interval.target != "population_mean":
                raise ValueError("dot estimate interval must target population_mean")
            if not self.interval.low <= self.value <= self.interval.high:
                raise ValueError("dot estimate must lie within its interval")
        if any(not warning for warning in self.warnings):
            raise ValueError("dot estimate warnings must not contain empty strings")


@dataclass(frozen=True, slots=True)
class DotPlotResult:
    """Schema-v1 result for a parametric labeled dot plot."""

    schema_version: int
    analysis: str
    x: str
    label_column: str
    sample: SampleAudit
    one_sample: AnalysisResult
    estimates: tuple[DotEstimateResult, ...]
    limits: ResourceLimits
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("dot plot schema_version must be 1")
        if self.analysis != "ggdotplotstats_one_sample_parametric":
            raise ValueError("dot plot analysis identity is unsupported")
        if not self.x or not self.label_column:
            raise ValueError("dot plot columns must be non-empty")
        if self.x == self.label_column:
            raise ValueError("dot plot value and label columns must differ")
        if self.sample != self.one_sample.sample:
            raise ValueError("dot plot and one-sample audits must match")
        if (
            self.one_sample.analysis != self.analysis
            or self.one_sample.column != self.x
        ):
            raise ValueError("dot plot one-sample result identity must match")
        if not self.estimates:
            raise ValueError("dot plot requires at least one labeled estimate")
        labels = tuple(
            (type(estimate.label), estimate.label) for estimate in self.estimates
        )
        if len(set(labels)) != len(labels):
            raise ValueError("dot plot labels must be unique")
        if sum(estimate.sample.analyzed_rows for estimate in self.estimates) != (
            self.sample.analyzed_rows
        ):
            raise ValueError("dot estimates must partition the analyzed sample")
        if any(not warning for warning in self.warnings):
            raise ValueError("dot plot warnings must not contain empty strings")

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-serializable representation."""

        return asdict(self)


@dataclass(frozen=True, slots=True)
class CorrelationTestResult:
    """Two-sided test of zero Pearson correlation."""

    name: str
    alternative: str
    statistic: float | None
    df: int
    p_value: float

    def __post_init__(self) -> None:
        if self.name != "pearson_correlation":
            raise ValueError("correlation test name is unsupported")
        if self.alternative != "two-sided":
            raise ValueError("correlation alternative is unsupported")
        if self.statistic is not None and not isfinite(self.statistic):
            raise ValueError("correlation statistic must be finite when present")
        if self.df < 2:
            raise ValueError("correlation test df must be at least two")
        if not isfinite(self.p_value) or not 0.0 <= self.p_value <= 1.0:
            raise ValueError("correlation p_value must be between zero and one")


@dataclass(frozen=True, slots=True)
class CorrelationResult:
    """Schema-v1 result for one Pearson correlation analysis."""

    schema_version: int
    analysis: str
    x: str
    y: str
    sample: SampleAudit
    estimate: float
    test: CorrelationTestResult
    interval: IntervalResult
    limits: ResourceLimits
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("correlation schema_version must be 1")
        if self.analysis != "ggscatterstats_pearson":
            raise ValueError("correlation analysis identity is unsupported")
        if not self.x or not self.y or self.x == self.y:
            raise ValueError("correlation columns must be distinct and non-empty")
        if not isfinite(self.estimate) or not -1.0 <= self.estimate <= 1.0:
            raise ValueError("correlation estimate must be finite and within [-1, 1]")
        if self.test.df != self.sample.analyzed_rows - 2:
            raise ValueError("correlation df must equal analyzed pairs minus two")
        if self.interval.target != "population_pearson_r":
            raise ValueError("correlation interval target is unsupported")
        if not -1.0 <= self.interval.low <= self.interval.high <= 1.0:
            raise ValueError("correlation interval must lie within [-1, 1]")
        if not self.interval.low <= self.estimate <= self.interval.high:
            raise ValueError("correlation estimate must lie within its interval")
        perfect = abs(self.estimate) == 1.0
        if perfect != (self.test.statistic is None):
            raise ValueError("only perfect correlation has no finite statistic")
        if any(not warning for warning in self.warnings):
            raise ValueError("correlation warnings must not contain empty strings")

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-serializable representation."""

        return asdict(self)


@dataclass(frozen=True, slots=True)
class CorrelationMatrixCell:
    """One diagonal or off-diagonal correlation-matrix cell."""

    x: str
    y: str
    n_obs: int
    estimate: float
    interval: IntervalResult | None
    statistic: float | None
    df: int | None
    p_value: float | None
    adjusted_p_value: float | None
    significant: bool | None

    def __post_init__(self) -> None:
        if not self.x or not self.y or self.n_obs < 1:
            raise ValueError("matrix cell identity and sample size are required")
        if not isfinite(self.estimate) or not -1.0 <= self.estimate <= 1.0:
            raise ValueError("matrix cell estimate must lie within [-1, 1]")
        diagonal = self.x == self.y
        inferential = (
            self.interval,
            self.df,
            self.p_value,
            self.adjusted_p_value,
            self.significant,
        )
        if diagonal:
            if self.estimate != 1.0 or self.statistic is not None:
                raise ValueError("matrix diagonal must be an estimate-only identity")
            if any(value is not None for value in inferential):
                raise ValueError("matrix diagonal must not contain inference")
        else:
            if any(value is None for value in inferential):
                raise ValueError("off-diagonal matrix cells require inference")
            if self.df != self.n_obs - 2:
                raise ValueError("matrix cell df must equal n_obs minus two")
            if self.p_value is not None and not 0.0 <= self.p_value <= 1.0:
                raise ValueError("matrix cell p_value must be within [0, 1]")
            if self.adjusted_p_value is not None and not (
                0.0 <= self.adjusted_p_value <= 1.0
            ):
                raise ValueError("matrix adjusted p_value must be within [0, 1]")


@dataclass(frozen=True, slots=True)
class CorrelationMatrixResult:
    """Schema-v1 long-form result for a Pearson correlation matrix."""

    schema_version: int
    analysis: str
    columns: tuple[str, ...]
    p_adjust: str
    sig_level: float
    cells: tuple[CorrelationMatrixCell, ...]
    limits: ResourceLimits
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("correlation matrix schema_version must be 1")
        if self.analysis != "ggcorrmat_pearson":
            raise ValueError("correlation matrix analysis identity is unsupported")
        if not 2 <= len(self.columns) <= 50 or len(set(self.columns)) != len(
            self.columns
        ):
            raise ValueError("correlation matrix requires 2-50 unique columns")
        if self.p_adjust not in {"holm", "none"}:
            raise ValueError("correlation matrix p_adjust is unsupported")
        if not isfinite(self.sig_level) or not 0.0 < self.sig_level < 1.0:
            raise ValueError("correlation matrix sig_level must lie within (0, 1)")
        if len(self.cells) != len(self.columns) ** 2:
            raise ValueError("correlation matrix must contain every ordered cell")
        identities = {(cell.x, cell.y) for cell in self.cells}
        expected = {(x, y) for x in self.columns for y in self.columns}
        if identities != expected:
            raise ValueError("correlation matrix cell identities are incomplete")
        by_identity = {(cell.x, cell.y): cell for cell in self.cells}
        for x in self.columns:
            for y in self.columns:
                cell = by_identity[(x, y)]
                mirror = by_identity[(y, x)]
                if (
                    cell.n_obs,
                    cell.estimate,
                    cell.interval,
                    cell.statistic,
                    cell.df,
                    cell.p_value,
                    cell.adjusted_p_value,
                    cell.significant,
                ) != (
                    mirror.n_obs,
                    mirror.estimate,
                    mirror.interval,
                    mirror.statistic,
                    mirror.df,
                    mirror.p_value,
                    mirror.adjusted_p_value,
                    mirror.significant,
                ):
                    raise ValueError("correlation matrix cells must be symmetric")
        if any(not warning for warning in self.warnings):
            raise ValueError("matrix warnings must not contain empty strings")

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-serializable representation."""

        return asdict(self)


@dataclass(frozen=True, slots=True)
class GroupSampleAudit:
    """Rows retained or dropped at the grouping boundary."""

    input_rows: int
    analyzed_rows: int
    dropped_null_group_rows: int

    def __post_init__(self) -> None:
        if min(self.input_rows, self.analyzed_rows, self.dropped_null_group_rows) < 0:
            raise ValueError("group sample counts must be non-negative")
        if self.input_rows != self.analyzed_rows + self.dropped_null_group_rows:
            raise ValueError("group sample counts must reconcile")


@dataclass(frozen=True, slots=True)
class GroupResultItem:
    """One named result within a grouped operation."""

    group: GroupIdentity
    result: StructuredResult

    def __post_init__(self) -> None:
        if isinstance(self.group, str) and not self.group:
            raise ValueError("group identity must be non-empty")
        if isinstance(self.group, float) and not isfinite(self.group):
            raise ValueError("numeric group identity must be finite")


@dataclass(frozen=True, slots=True)
class GroupedResult:
    """Schema-v1 result container for an atomic grouped operation."""

    schema_version: int
    analysis: str
    group_column: str
    sample: GroupSampleAudit
    correction_scope: str
    groups: tuple[GroupResultItem, ...]
    limits: ResourceLimits
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("grouped result schema_version must be 1")
        if self.analysis not in {
            "grouped_gghistostats_one_sample_parametric",
            "grouped_ggdotplotstats_one_sample_parametric",
            "grouped_ggscatterstats_pearson",
            "grouped_ggcorrmat_pearson",
            "grouped_ggbetweenstats_welch",
            "grouped_ggwithinstats_parametric",
        }:
            raise ValueError("grouped analysis identity is unsupported")
        if not self.group_column or not self.groups:
            raise ValueError("grouped result requires a column and groups")
        identities = tuple((type(item.group), item.group) for item in self.groups)
        if len(set(identities)) != len(identities):
            raise ValueError("group identities must be unique")
        if self.correction_scope not in {
            "none_across_groups",
            "within_group_matrix",
            "within_each_comparison_result_none_across_outer_groups",
            "within_each_repeated_result_none_across_outer_groups",
        }:
            raise ValueError("grouped correction scope is unsupported")
        if any(not warning for warning in self.warnings):
            raise ValueError("grouped warnings must not contain empty strings")

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-serializable representation."""

        return {
            "schema_version": self.schema_version,
            "analysis": self.analysis,
            "group_column": self.group_column,
            "sample": asdict(self.sample),
            "correction_scope": self.correction_scope,
            "groups": [
                {"group": item.group, "result": item.result.to_dict()}
                for item in self.groups
            ],
            "limits": asdict(self.limits),
            "warnings": list(self.warnings),
        }
