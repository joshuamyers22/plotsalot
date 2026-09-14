"""Approved classical categorical analyses shared by bar and pie renderers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from importlib import import_module
from math import sqrt
from typing import Literal, Protocol, cast

import numpy as np
import polars as pl

from plotsalot.categorical_data import (
    DEFAULT_MAX_CELLS,
    DEFAULT_MAX_LEVELS,
    DEFAULT_MAX_TOTAL_COUNT,
    CategoricalTable,
    select_categorical_table,
)
from plotsalot.categorical_result import (
    CategoricalCellResult,
    CategoricalDesign,
    CategoricalDisplay,
    CategoricalEffectResult,
    CategoricalFollowupResult,
    CategoricalResult,
    CategoricalTestResult,
    ExpectedCountResult,
)
from plotsalot.data import DEFAULT_MAX_ROWS
from plotsalot.result import IntervalResult, ResourceLimits, ScalarIdentity

DEFAULT_MAX_LABELS = 400


class _ContinuousDistribution(Protocol):
    def cdf(self, value: float, *parameters: float) -> float: ...

    def sf(self, value: float, *parameters: float) -> float: ...


class _ConfidenceInterval(Protocol):
    low: float
    high: float


class _BinomialResult(Protocol):
    pvalue: float

    def proportion_ci(
        self, *, confidence_level: float, method: str
    ) -> _ConfidenceInterval: ...


class _ScipyStats(Protocol):
    chi2: _ContinuousDistribution
    ncx2: _ContinuousDistribution

    def binomtest(
        self, k: int, n: int, p: float, *, alternative: str
    ) -> _BinomialResult: ...


class _ScipyOptimize(Protocol):
    def brentq(
        self,
        function: object,
        low: float,
        high: float,
        *,
        xtol: float,
        rtol: float,
    ) -> float: ...


class _StatsmodelsMultitest(Protocol):
    def multipletests(
        self, pvals: list[float], *, method: str
    ) -> tuple[np.ndarray, np.ndarray, float, float]: ...


scipy_stats = cast(_ScipyStats, import_module("scipy.stats"))
scipy_optimize = cast(_ScipyOptimize, import_module("scipy.optimize"))
statsmodels_multitest = cast(
    _StatsmodelsMultitest, import_module("statsmodels.stats.multitest")
)


@dataclass(frozen=True, slots=True)
class CategoricalAnalysis:
    table: CategoricalTable
    result: CategoricalResult

    def __post_init__(self) -> None:
        if (
            self.table.audit != self.result.sample
            or self.table.x != self.result.x
            or self.table.y != self.result.y
            or self.table.counts_column != self.result.counts
            or self.table.x_levels != self.result.x_levels
            or self.table.y_levels != self.result.y_levels
            or tuple(cell.observed for cell in self.result.cells)
            != tuple(int(value) for value in self.table.observed.flat)
        ):
            raise ValueError("categorical analysis table and result must match")


def _validate_options(
    *,
    method_type: str,
    alternative: str,
    conf_level: float,
    p_adjust: str,
    alpha: float,
    pairwise_display: str,
    maximum_labels: int,
) -> CategoricalDisplay:
    if method_type != "parametric":
        raise ValueError("only type='parametric' is supported")
    if alternative != "two-sided":
        raise ValueError("only alternative='two-sided' is supported")
    conf_value = cast(object, conf_level)
    if isinstance(conf_value, bool) or not isinstance(conf_value, (int, float)):
        raise ValueError("conf_level must lie within (0, 1)")
    if not 0.0 < float(conf_value) < 1.0:
        raise ValueError("conf_level must lie within (0, 1)")
    if p_adjust not in {"holm", "none"}:
        raise ValueError("p_adjust must be 'holm' or 'none'")
    alpha_value = cast(object, alpha)
    if isinstance(alpha_value, bool) or not isinstance(alpha_value, (int, float)):
        raise ValueError("alpha must lie within (0, 1)")
    if not 0.0 < float(alpha_value) < 1.0:
        raise ValueError("alpha must lie within (0, 1)")
    if pairwise_display not in {"significant", "non-significant", "all", "none"}:
        raise ValueError("pairwise_display is unsupported")
    labels_value = cast(object, maximum_labels)
    if type(labels_value) is not int:
        raise ValueError("maximum_labels must be a positive integer")
    if maximum_labels < 1:
        raise ValueError("maximum_labels must be a positive integer")
    return cast(CategoricalDisplay, pairwise_display)


def _ratio(
    levels: tuple[ScalarIdentity, ...],
    ratio: Mapping[ScalarIdentity, float] | None,
) -> np.ndarray:
    if ratio is None:
        return np.full(len(levels), 1.0 / len(levels), dtype=np.float64)
    items: dict[tuple[type[object], ScalarIdentity], float] = {}
    for key, raw_value in ratio.items():
        value = cast(object, raw_value)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("ratio probabilities must be numeric and not boolean")
        items[(type(key), key)] = float(value)
    expected_keys = {(type(level), level) for level in levels}
    if set(items) != expected_keys:
        raise ValueError("ratio must contain every x level exactly once")
    values = np.array([items[(type(level), level)] for level in levels])
    if not bool(np.isfinite(values).all()) or bool((values <= 0.0).any()):
        raise ValueError("ratio probabilities must be finite and positive")
    if abs(float(values.sum()) - 1.0) > 1e-12:
        raise ValueError("ratio probabilities must sum to one")
    return values


def _adequacy(expected: np.ndarray) -> ExpectedCountResult:
    if not bool(np.isfinite(expected).all()) or float(np.min(expected)) < 1.0:
        raise ValueError("sparse table: every expected count must be at least one")
    below = sum(float(value) < 5.0 for value in expected.flat)
    total = int(expected.size)
    if expected.shape == (2, 2):
        if below:
            raise ValueError(
                "sparse 2x2 table: every expected count must be at least five"
            )
        rule = "all_at_least_five_2x2"
    else:
        if (total - below) / total < 0.8:
            raise ValueError(
                "sparse table: at least 80% of expected counts must be at least five"
            )
        rule = "at_least_80_percent_at_least_five"
    return ExpectedCountResult(float(np.min(expected)), below, total, rule)


def _root_for_cdf(q: float, df: float, target: float) -> float:
    upper = max(1.0, q + df)
    while scipy_stats.ncx2.cdf(q, df, upper) > target:
        upper *= 2.0
        if upper > 1e12:
            raise ValueError("noncentral chi-square interval could not be bracketed")

    def objective(value: float) -> float:
        return scipy_stats.ncx2.cdf(q, df, value) - target

    return float(
        scipy_optimize.brentq(
            objective,
            0.0,
            upper,
            xtol=1e-12,
            rtol=1e-12,
        )
    )


def _effect_interval(
    q: float,
    df: float,
    n: int,
    scale: float,
    maximum: float,
    level: float,
    target: str,
) -> IntervalResult:
    alpha = 1.0 - level
    cdf0 = scipy_stats.chi2.cdf(q, df)
    lower_lambda = (
        0.0 if cdf0 <= 1.0 - alpha / 2.0 else _root_for_cdf(q, df, 1.0 - alpha / 2.0)
    )
    if cdf0 <= alpha / 2.0:
        upper = maximum
    else:
        upper_lambda = _root_for_cdf(q, df, alpha / 2.0)
        upper = min(maximum, sqrt(upper_lambda / (n * scale)))
    return IntervalResult(
        target=target,
        method="noncentral_chi_square_equal_tail_bounded",
        level=level,
        low=min(maximum, sqrt(lower_lambda / (n * scale))),
        high=upper,
    )


def _pearson(
    observed: np.ndarray,
    *,
    goodness_of_fit_ratio: np.ndarray | None,
    conf_level: float,
) -> tuple[
    CategoricalTestResult, CategoricalEffectResult, ExpectedCountResult, np.ndarray
]:
    n = int(observed.sum())
    if goodness_of_fit_ratio is not None:
        expected = n * goodness_of_fit_ratio.reshape(-1, 1)
        name = "pearson_chi_square_goodness_of_fit"
        df = float(observed.shape[0] - 1)
        effect_name = "cohen_w"
        scale = 1.0
        maximum = sqrt(1.0 / float(np.min(goodness_of_fit_ratio)) - 1.0)
    else:
        rows = observed.sum(axis=1, keepdims=True)
        columns = observed.sum(axis=0, keepdims=True)
        if bool((rows == 0).any()) or bool((columns == 0).any()):
            raise ValueError("categorical table contains an empty margin")
        expected = rows @ columns / n
        name = "pearson_chi_square_independence"
        df = float((observed.shape[0] - 1) * (observed.shape[1] - 1))
        effect_name = "cramers_v"
        scale = float(min(observed.shape[0] - 1, observed.shape[1] - 1))
        maximum = 1.0
    adequacy = _adequacy(expected)
    q = float(np.sum((observed - expected) ** 2 / expected))
    p_value = float(scipy_stats.chi2.sf(q, df))
    effect_value = sqrt(q / (n * scale))
    return (
        CategoricalTestResult(name, q, df, p_value),
        CategoricalEffectResult(
            effect_name,
            effect_value,
            _effect_interval(q, df, n, scale, maximum, conf_level, effect_name),
        ),
        adequacy,
        expected,
    )


def _adjust(
    items: list[
        tuple[
            object,
            tuple[int, ...],
            tuple[int, int],
            CategoricalTestResult,
            CategoricalEffectResult,
            ExpectedCountResult,
        ]
    ],
    p_adjust: str,
    alpha: float,
    family: Literal["pairwise", "stratum"],
) -> tuple[CategoricalFollowupResult, ...]:
    if not items:
        return ()
    raw = [item[3].p_value for item in items]
    adjusted = (
        np.asarray(raw, dtype=np.float64)
        if p_adjust == "none"
        else statsmodels_multitest.multipletests(raw, method="holm")[1]
    )
    results: list[CategoricalFollowupResult] = []
    for item, adjusted_p in zip(items, adjusted, strict=True):
        identity, observed, shape, test, effect, adequacy = item
        if family == "pairwise":
            left, right = cast(tuple[ScalarIdentity, ScalarIdentity], identity)
        else:
            left, right = cast(ScalarIdentity, identity), None
        results.append(
            CategoricalFollowupResult(
                family,
                left,
                right,
                observed,
                shape,
                test,
                effect,
                float(adjusted_p),
                bool(adjusted_p <= alpha),
                adequacy,
            )
        )
    return tuple(results)


def _cells(
    table: CategoricalTable, expected: np.ndarray | None
) -> tuple[CategoricalCellResult, ...]:
    observed = table.observed
    total = int(observed.sum())
    columns = observed.sum(axis=0)
    cells: list[CategoricalCellResult] = []
    for i, x_level in enumerate(table.x_levels):
        for j in range(observed.shape[1]):
            value = int(observed[i, j])
            expected_value = None if expected is None else float(expected[i, j])
            cells.append(
                CategoricalCellResult(
                    x_level=x_level,
                    y_level=None if table.y is None else table.y_levels[j],
                    observed=value,
                    expected=expected_value,
                    displayed_proportion=value / int(columns[j]),
                    joint_proportion=value / total,
                    pearson_residual=None
                    if expected_value is None
                    else (value - expected_value) / sqrt(expected_value),
                    contribution=None
                    if expected_value is None
                    else (value - expected_value) ** 2 / expected_value,
                )
            )
    return tuple(cells)


def analyze_categorical(
    data: pl.DataFrame,
    x: str,
    y: str | None = None,
    *,
    counts: str | None = None,
    type: str = "parametric",
    paired: bool = False,
    ratio: Mapping[ScalarIdentity, float] | None = None,
    alternative: str = "two-sided",
    conf_level: float = 0.95,
    p_adjust: str = "holm",
    alpha: float = 0.05,
    pairwise_display: str = "significant",
    proportion_test: bool = True,
    maximum_rows: int = DEFAULT_MAX_ROWS,
    maximum_levels: int = DEFAULT_MAX_LEVELS,
    maximum_cells: int = DEFAULT_MAX_CELLS,
    maximum_total_count: int = DEFAULT_MAX_TOTAL_COUNT,
    maximum_labels: int = DEFAULT_MAX_LABELS,
) -> CategoricalAnalysis:
    display = _validate_options(
        method_type=type,
        alternative=alternative,
        conf_level=conf_level,
        p_adjust=p_adjust,
        alpha=alpha,
        pairwise_display=pairwise_display,
        maximum_labels=maximum_labels,
    )
    paired_value = cast(object, paired)
    proportion_value = cast(object, proportion_test)
    if paired_value.__class__ is not bool or proportion_value.__class__ is not bool:
        raise TypeError("paired and proportion_test must be boolean")
    table = select_categorical_table(
        data,
        x,
        y,
        counts=counts,
        maximum_rows=maximum_rows,
        maximum_levels=maximum_levels,
        maximum_cells=maximum_cells,
        maximum_total_count=maximum_total_count,
    )
    if len(table.x_levels) * max(1, len(table.y_levels)) > maximum_labels:
        raise ValueError(f"categorical labels exceed maximum_labels={maximum_labels}")
    resolved_ratio = (
        _ratio(table.x_levels, ratio)
        if y is None or proportion_test or ratio is not None
        else None
    )
    pairwise: tuple[CategoricalFollowupResult, ...] = ()
    strata: tuple[CategoricalFollowupResult, ...] = ()
    if y is None:
        if paired:
            raise ValueError("paired=True requires y")
        omnibus, effect, adequacy, expected = _pearson(
            table.observed, goodness_of_fit_ratio=resolved_ratio, conf_level=conf_level
        )
        design: CategoricalDesign = "one_way"
    elif paired:
        if ratio is not None:
            raise ValueError("ratio is unsupported for paired analysis")
        if proportion_test:
            raise ValueError("proportion_test must be False for paired analysis")
        if len(table.x_levels) != 2 or table.x_levels != table.y_levels:
            raise ValueError("paired analysis requires the same two x and y levels")
        if bool((table.observed.sum(axis=0) == 0).any()) or bool(
            (table.observed.sum(axis=1) == 0).any()
        ):
            raise ValueError("paired categorical table contains an empty margin")
        b, c = int(table.observed[0, 1]), int(table.observed[1, 0])
        discordant = b + c
        if discordant < 1:
            raise ValueError("paired analysis requires a discordant observation")
        binomial = scipy_stats.binomtest(b, discordant, 0.5, alternative="two-sided")
        interval = binomial.proportion_ci(confidence_level=conf_level, method="exact")
        value = b / discordant - 0.5
        omnibus = CategoricalTestResult(
            "exact_binomial_paired", float(b), 0.0, float(binomial.pvalue)
        )
        effect = CategoricalEffectResult(
            "cohen_g",
            value,
            IntervalResult(
                "cohen_g",
                "clopper_pearson_transformed",
                conf_level,
                float(interval.low) - 0.5,
                float(interval.high) - 0.5,
            ),
        )
        adequacy, expected, resolved_ratio, design = None, None, None, "paired"
    else:
        if ratio is not None and not proportion_test:
            raise ValueError("ratio requires proportion_test=True in a two-way design")
        omnibus, effect, adequacy, expected = _pearson(
            table.observed, goodness_of_fit_ratio=None, conf_level=conf_level
        )
        design = "independent"
        pair_items: list[
            tuple[
                object,
                tuple[int, ...],
                tuple[int, int],
                CategoricalTestResult,
                CategoricalEffectResult,
                ExpectedCountResult,
            ]
        ] = []
        if len(table.x_levels) >= 3:
            for left in range(len(table.x_levels)):
                for right in range(left + 1, len(table.x_levels)):
                    pair_observed = table.observed[[left, right], :]
                    test, pair_effect, pair_adequacy, _ = _pearson(
                        pair_observed,
                        goodness_of_fit_ratio=None,
                        conf_level=conf_level,
                    )
                    pair_items.append(
                        (
                            (table.x_levels[left], table.x_levels[right]),
                            tuple(int(value) for value in pair_observed.flat),
                            (2, pair_observed.shape[1]),
                            test,
                            pair_effect,
                            pair_adequacy,
                        )
                    )
        pairwise = _adjust(pair_items, p_adjust, alpha, "pairwise")
        if proportion_test:
            stratum_items: list[
                tuple[
                    object,
                    tuple[int, ...],
                    tuple[int, int],
                    CategoricalTestResult,
                    CategoricalEffectResult,
                    ExpectedCountResult,
                ]
            ] = []
            for index, level in enumerate(table.y_levels):
                test, stratum_effect, stratum_adequacy, _ = _pearson(
                    table.observed[:, index : index + 1],
                    goodness_of_fit_ratio=resolved_ratio,
                    conf_level=conf_level,
                )
                stratum_items.append(
                    (
                        level,
                        tuple(int(value) for value in table.observed[:, index]),
                        (len(table.x_levels), 1),
                        test,
                        stratum_effect,
                        stratum_adequacy,
                    )
                )
            strata = _adjust(stratum_items, p_adjust, alpha, "stratum")
    row_totals = tuple(int(value) for value in table.observed.sum(axis=1))
    column_totals = (
        () if y is None else tuple(int(value) for value in table.observed.sum(axis=0))
    )
    result = CategoricalResult(
        schema_version=1,
        analysis="categorical_classical",
        design=design,
        x=x,
        y=y,
        counts=counts,
        sample=table.audit,
        x_levels=table.x_levels,
        y_levels=table.y_levels,
        cells=_cells(table, expected),
        row_totals=row_totals,
        column_totals=column_totals,
        ratio=None
        if resolved_ratio is None
        else tuple(float(value) for value in resolved_ratio),
        omnibus=omnibus,
        effect=effect,
        adequacy=adequacy,
        pairwise=pairwise,
        strata=strata,
        p_adjust=p_adjust,
        alpha=float(alpha),
        conf_level=float(conf_level),
        pairwise_display=display,
        proportion_test=proportion_test,
        limits=ResourceLimits(
            maximum_rows=maximum_rows,
            maximum_groups=20,
            maximum_variables=maximum_levels,
            maximum_labels=maximum_labels,
            maximum_levels=maximum_levels,
            maximum_pairwise_hypotheses=maximum_levels * (maximum_levels - 1) // 2,
            maximum_cells=maximum_cells,
            maximum_total_count=maximum_total_count,
        ),
        warnings=(
            (
                "paired exact-binomial inference adapts upstream asymptotic McNemar"
                if design == "paired"
                else "noncentral chi-square intervals are plotsalot-native"
            ),
            *(
                ("pairwise Pearson tests adapt upstream Fisher exact tests",)
                if design == "independent" and len(pairwise) > 0
                else ()
            ),
            *(
                ("stratum p-values use a separate Holm family",)
                if design == "independent" and len(strata) > 0
                else ()
            ),
        ),
    )
    return CategoricalAnalysis(table, result)


analyze_ggbarstats = analyze_categorical
analyze_ggpiestats = analyze_categorical
