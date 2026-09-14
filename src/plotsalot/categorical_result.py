"""Typed result contracts for approved M4 categorical analyses."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any, Literal

from plotsalot.result import IntervalResult, ResourceLimits, ScalarIdentity

CategoricalDesign = Literal["one_way", "independent", "paired"]
CategoricalDisplay = Literal["significant", "non-significant", "all", "none"]


@dataclass(frozen=True, slots=True)
class CategoricalSampleAudit:
    input_rows: int
    analyzed_rows: int
    weighted_total: int
    dropped_null_x_rows: int
    dropped_null_y_rows: int
    dropped_null_count_rows: int

    def __post_init__(self) -> None:
        values = asdict(self).values()
        if any(type(value) is not int or value < 0 for value in values):
            raise ValueError("categorical audit counts must be non-negative integers")
        if (
            self.input_rows
            != self.analyzed_rows
            + self.dropped_null_x_rows
            + self.dropped_null_y_rows
            + self.dropped_null_count_rows
        ):
            raise ValueError("categorical physical-row counts must reconcile")
        if self.analyzed_rows < 1 or self.weighted_total < 1:
            raise ValueError("categorical analysis requires positive retained totals")


@dataclass(frozen=True, slots=True)
class CategoricalCellResult:
    x_level: ScalarIdentity
    y_level: ScalarIdentity | None
    observed: int
    expected: float | None
    displayed_proportion: float
    joint_proportion: float
    pearson_residual: float | None
    contribution: float | None

    def __post_init__(self) -> None:
        if type(self.observed) is not int or self.observed < 0:
            raise ValueError("categorical observed count must be non-negative")
        numeric = (self.displayed_proportion, self.joint_proportion)
        if not all(isfinite(value) and 0.0 <= value <= 1.0 for value in numeric):
            raise ValueError("categorical proportions must lie within [0, 1]")
        optional = (self.expected, self.pearson_residual, self.contribution)
        if any(value is not None and not isfinite(value) for value in optional):
            raise ValueError("categorical cell statistics must be finite")
        if self.expected is not None and self.expected <= 0.0:
            raise ValueError("categorical expected count must be positive")
        if self.contribution is not None and self.contribution < 0.0:
            raise ValueError("categorical contribution must be non-negative")


@dataclass(frozen=True, slots=True)
class ExpectedCountResult:
    minimum: float
    cells_below_five: int
    total_cells: int
    rule: str

    def __post_init__(self) -> None:
        if not isfinite(self.minimum) or self.minimum < 1.0:
            raise ValueError("minimum expected count must be at least one")
        if not 0 <= self.cells_below_five <= self.total_cells or self.total_cells < 1:
            raise ValueError("expected-count cell totals are invalid")
        if self.rule not in {
            "all_at_least_five_2x2",
            "at_least_80_percent_at_least_five",
        }:
            raise ValueError("expected-count rule is unsupported")


@dataclass(frozen=True, slots=True)
class CategoricalTestResult:
    name: str
    statistic: float
    df: float
    p_value: float

    def __post_init__(self) -> None:
        supported = {
            "pearson_chi_square_goodness_of_fit",
            "pearson_chi_square_independence",
            "exact_binomial_paired",
        }
        if self.name not in supported:
            raise ValueError("categorical test is unsupported")
        if not isfinite(self.statistic) or self.statistic < 0.0:
            raise ValueError("categorical statistic must be finite and non-negative")
        if not isfinite(self.df) or self.df < 0.0:
            raise ValueError("categorical df must be finite and non-negative")
        if not isfinite(self.p_value) or not 0.0 <= self.p_value <= 1.0:
            raise ValueError("categorical p_value must lie within [0, 1]")


@dataclass(frozen=True, slots=True)
class CategoricalEffectResult:
    name: str
    value: float
    interval: IntervalResult

    def __post_init__(self) -> None:
        if self.name not in {"cohen_w", "cramers_v", "cohen_g"}:
            raise ValueError("categorical effect is unsupported")
        if not isfinite(self.value):
            raise ValueError("categorical effect must be finite")
        if self.name in {"cohen_w", "cramers_v"} and self.value < 0.0:
            raise ValueError("unsigned categorical effect must be non-negative")
        if self.name == "cohen_g" and not -0.5 <= self.value <= 0.5:
            raise ValueError("Cohen's g must lie within [-0.5, 0.5]")
        if not self.interval.low <= self.value <= self.interval.high:
            raise ValueError("categorical effect must lie within its interval")


@dataclass(frozen=True, slots=True)
class CategoricalFollowupResult:
    family: Literal["pairwise", "stratum"]
    left: ScalarIdentity
    right: ScalarIdentity | None
    observed: tuple[int, ...]
    shape: tuple[int, int]
    test: CategoricalTestResult
    effect: CategoricalEffectResult
    adjusted_p_value: float
    significant: bool
    adequacy: ExpectedCountResult

    def __post_init__(self) -> None:
        if self.family not in {"pairwise", "stratum"}:
            raise ValueError("categorical follow-up family is unsupported")
        if self.family == "pairwise" and self.right is None:
            raise ValueError("pairwise result requires two levels")
        if self.family == "stratum" and self.right is not None:
            raise ValueError("stratum result requires one identity")
        if (
            len(self.shape) != 2
            or any(type(value) is not int or value < 1 for value in self.shape)
            or len(self.observed) != self.shape[0] * self.shape[1]
            or any(type(value) is not int or value < 0 for value in self.observed)
            or sum(self.observed) < 1
        ):
            raise ValueError("categorical follow-up subtable is invalid")
        if self.family == "pairwise" and self.shape[0] != 2:
            raise ValueError("pairwise follow-up must retain two rows")
        if self.family == "stratum" and self.shape[1] != 1:
            raise ValueError("stratum follow-up must retain one column")
        if (
            not isfinite(self.adjusted_p_value)
            or not 0.0 <= self.adjusted_p_value <= 1.0
        ):
            raise ValueError("adjusted p_value must lie within [0, 1]")


@dataclass(frozen=True, slots=True)
class CategoricalResult:
    schema_version: int
    analysis: str
    design: CategoricalDesign
    x: str
    y: str | None
    counts: str | None
    sample: CategoricalSampleAudit
    x_levels: tuple[ScalarIdentity, ...]
    y_levels: tuple[ScalarIdentity, ...]
    cells: tuple[CategoricalCellResult, ...]
    row_totals: tuple[int, ...]
    column_totals: tuple[int, ...]
    ratio: tuple[float, ...] | None
    omnibus: CategoricalTestResult
    effect: CategoricalEffectResult
    adequacy: ExpectedCountResult | None
    pairwise: tuple[CategoricalFollowupResult, ...]
    strata: tuple[CategoricalFollowupResult, ...]
    p_adjust: str
    alpha: float
    conf_level: float
    pairwise_display: CategoricalDisplay
    proportion_test: bool
    limits: ResourceLimits
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.schema_version != 1 or self.analysis != "categorical_classical":
            raise ValueError("categorical result identity is unsupported")
        if not self.x or self.y == self.x or self.counts in {self.x, self.y}:
            raise ValueError("categorical columns must be distinct")
        if self.design == "one_way" and (self.y is not None or self.y_levels):
            raise ValueError("one-way result must not contain y levels")
        if self.design != "one_way" and (not self.y or len(self.y_levels) < 2):
            raise ValueError("two-way result requires y levels")
        if not 2 <= len(self.x_levels) <= 20:
            raise ValueError("categorical result requires 2-20 x levels")
        x_keys = tuple((type(level), level) for level in self.x_levels)
        y_keys = tuple((type(level), level) for level in self.y_levels)
        if len(set(x_keys)) != len(x_keys) or len(set(y_keys)) != len(y_keys):
            raise ValueError("categorical levels must be unique by typed identity")
        expected_cells = len(self.x_levels) * max(1, len(self.y_levels))
        if len(self.cells) != expected_cells:
            raise ValueError("categorical result cell family is incomplete")
        expected_identities = tuple(
            (x_level, None if self.design == "one_way" else y_level)
            for x_level in self.x_levels
            for y_level in (self.y_levels or (None,))
        )
        actual_identities = tuple((cell.x_level, cell.y_level) for cell in self.cells)
        if actual_identities != expected_identities:
            raise ValueError("categorical cells must follow declared level order")
        observed = tuple(cell.observed for cell in self.cells)
        if len(self.row_totals) != len(self.x_levels):
            raise ValueError("categorical row total family is incomplete")
        if self.design == "one_way":
            computed_rows = observed
        else:
            width = len(self.y_levels)
            computed_rows = tuple(
                sum(observed[start : start + width])
                for start in range(0, len(observed), width)
            )
        if self.row_totals != computed_rows:
            raise ValueError("categorical row totals must match cells")
        if sum(self.row_totals) != self.sample.weighted_total:
            raise ValueError("categorical row totals must reconcile")
        if self.design == "one_way":
            if self.column_totals:
                raise ValueError("one-way result cannot contain column totals")
            denominators = (self.sample.weighted_total,)
        else:
            computed_columns = tuple(
                sum(observed[index :: len(self.y_levels)])
                for index in range(len(self.y_levels))
            )
            if self.column_totals != computed_columns:
                raise ValueError("categorical column totals must match cells")
            denominators = self.column_totals
        for index, cell in enumerate(self.cells):
            denominator = denominators[index % len(denominators)]
            if (
                abs(cell.displayed_proportion - cell.observed / denominator) > 1e-15
                or abs(
                    cell.joint_proportion - cell.observed / self.sample.weighted_total
                )
                > 1e-15
            ):
                raise ValueError("categorical cell proportions must reconcile")
        if self.ratio is not None and (
            len(self.ratio) != len(self.x_levels)
            or any(not isfinite(value) or value <= 0.0 for value in self.ratio)
            or abs(sum(self.ratio) - 1.0) > 1e-12
        ):
            raise ValueError("categorical ratio is invalid")
        if self.p_adjust not in {"holm", "none"}:
            raise ValueError("categorical p_adjust is unsupported")
        if not 0.0 < self.alpha < 1.0:
            raise ValueError("categorical alpha must lie within (0, 1)")
        if not 0.0 < self.conf_level < 1.0:
            raise ValueError("categorical conf_level must lie within (0, 1)")
        if abs(self.effect.interval.level - self.conf_level) > 1e-15 or any(
            abs(item.effect.interval.level - self.conf_level) > 1e-15
            for item in (*self.pairwise, *self.strata)
        ):
            raise ValueError("categorical interval level must match conf_level")
        if self.pairwise_display not in {
            "significant",
            "non-significant",
            "all",
            "none",
        }:
            raise ValueError("categorical pairwise_display is unsupported")
        if any(
            item.significant != (item.adjusted_p_value <= self.alpha)
            for item in (*self.pairwise, *self.strata)
        ):
            raise ValueError("categorical significance must use adjusted p-values")
        if self.design == "paired" and (
            self.adequacy is not None
            or self.pairwise
            or self.strata
            or self.ratio is not None
            or self.proportion_test
        ):
            raise ValueError("paired result cannot contain Pearson follow-ups")
        if self.design != "paired" and self.adequacy is None:
            raise ValueError("Pearson result requires adequacy metadata")
        expected_pairwise = (
            len(self.x_levels) * (len(self.x_levels) - 1) // 2
            if self.design == "independent" and len(self.x_levels) >= 3
            else 0
        )
        if len(self.pairwise) != expected_pairwise:
            raise ValueError("categorical pairwise family is incomplete")
        expected_pairs = (
            tuple(
                (left, right)
                for left in range(len(self.x_levels))
                for right in range(left + 1, len(self.x_levels))
            )
            if self.design == "independent" and len(self.x_levels) >= 3
            else ()
        )
        width = max(1, len(self.y_levels))
        for item, (left, right) in zip(self.pairwise, expected_pairs, strict=True):
            expected_observed = (
                *observed[left * width : (left + 1) * width],
                *observed[right * width : (right + 1) * width],
            )
            if (
                item.family != "pairwise"
                or (item.left, item.right)
                != (self.x_levels[left], self.x_levels[right])
                or item.observed != expected_observed
                or item.shape != (2, width)
            ):
                raise ValueError("categorical pairwise subtable does not reconcile")
        expected_strata = (
            len(self.y_levels)
            if self.design == "independent" and self.proportion_test
            else 0
        )
        if len(self.strata) != expected_strata:
            raise ValueError("categorical stratum family is incomplete")
        for index, item in enumerate(self.strata):
            expected_observed = observed[index::width]
            if (
                item.family != "stratum"
                or item.left != self.y_levels[index]
                or item.observed != expected_observed
                or item.shape != (len(self.x_levels), 1)
            ):
                raise ValueError("categorical stratum subtable does not reconcile")
        if any(not warning for warning in self.warnings):
            raise ValueError("categorical warnings must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
