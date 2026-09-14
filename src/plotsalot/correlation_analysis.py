"""Approved Pearson scatter and correlation-matrix analyses."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from math import atanh, isclose, sqrt, tanh
from typing import Protocol, cast
from warnings import catch_warnings, simplefilter

import numpy as np
import polars as pl

from plotsalot.data import (
    DEFAULT_MAX_ROWS,
    FloatArray,
    PairedNumericSample,
    select_numeric_pair,
)
from plotsalot.result import (
    CorrelationMatrixCell,
    CorrelationMatrixResult,
    CorrelationResult,
    CorrelationTestResult,
    IntervalResult,
    ResourceLimits,
)


class _PearsonResult(Protocol):
    statistic: float
    pvalue: float


class _NormalDistribution(Protocol):
    def ppf(self, probability: float) -> float: ...


class _ScipyStats(Protocol):
    norm: _NormalDistribution

    def pearsonr(self, x: FloatArray, y: FloatArray) -> _PearsonResult: ...


class _StatsmodelsMultitest(Protocol):
    def multipletests(
        self, pvals: list[float], *, method: str
    ) -> tuple[np.ndarray, np.ndarray, float, float]: ...


scipy_stats = cast(_ScipyStats, import_module("scipy.stats"))
statsmodels_multitest = cast(
    _StatsmodelsMultitest, import_module("statsmodels.stats.multitest")
)


@dataclass(frozen=True, slots=True)
class CorrelationAnalysis:
    """One correlation result and the exact paired sample used for it."""

    sample: PairedNumericSample
    result: CorrelationResult

    def __post_init__(self) -> None:
        if (self.sample.x, self.sample.y) != (self.result.x, self.result.y):
            raise ValueError("paired sample and correlation columns must match")
        if self.sample.audit != self.result.sample:
            raise ValueError("paired sample and correlation audits must match")


@dataclass(frozen=True, slots=True)
class CorrelationMatrixAnalysis:
    """A renderer-independent correlation-matrix result."""

    result: CorrelationMatrixResult


def analyze_ggscatterstats(
    data: pl.DataFrame,
    x: str,
    y: str,
    *,
    conf_level: float = 0.95,
    maximum_rows: int = DEFAULT_MAX_ROWS,
) -> CorrelationAnalysis:
    """Analyze a two-sided Pearson correlation without rendering."""

    if not 0.0 < conf_level < 1.0:
        raise ValueError("conf_level must be strictly between 0 and 1")
    sample = select_numeric_pair(
        data,
        x,
        y,
        minimum_size=4,
        require_variation=True,
        maximum_rows=maximum_rows,
    )
    with catch_warnings():
        simplefilter("error")
        try:
            scipy_result = scipy_stats.pearsonr(sample.x_values, sample.y_values)
        except Warning as warning:
            raise ValueError(
                f"Pearson correlation is unreliable: {warning}"
            ) from warning
    estimate = max(-1.0, min(1.0, float(scipy_result.statistic)))
    p_value = max(0.0, min(1.0, float(scipy_result.pvalue)))
    df = sample.audit.analyzed_rows - 2
    perfect = abs(estimate) == 1.0
    warnings: tuple[str, ...] = ()
    if perfect:
        estimate = 1.0 if estimate > 0.0 else -1.0
        statistic = None
        low = estimate
        high = estimate
        warnings = ("perfect correlation has no finite Student statistic",)
    else:
        statistic = estimate * sqrt(df / (1.0 - (estimate * estimate)))
        critical = float(scipy_stats.norm.ppf(0.5 + (conf_level / 2.0)))
        margin = critical / sqrt(sample.audit.analyzed_rows - 3)
        transformed = atanh(estimate)
        low = tanh(transformed - margin)
        high = tanh(transformed + margin)

    result = CorrelationResult(
        schema_version=1,
        analysis="ggscatterstats_pearson",
        x=x,
        y=y,
        sample=sample.audit,
        estimate=estimate,
        test=CorrelationTestResult(
            name="pearson_correlation",
            alternative="two-sided",
            statistic=statistic,
            df=df,
            p_value=p_value,
        ),
        interval=IntervalResult(
            target="population_pearson_r",
            method="fisher_z_two_sided",
            level=conf_level,
            low=low,
            high=high,
        ),
        limits=ResourceLimits(maximum_rows=maximum_rows),
        warnings=warnings,
    )
    return CorrelationAnalysis(sample=sample, result=result)


def _holm_adjust(p_values: list[float]) -> list[float]:
    if not p_values:
        return []
    order = sorted(range(len(p_values)), key=p_values.__getitem__)
    adjusted = [0.0] * len(p_values)
    running = 0.0
    total = len(p_values)
    for rank, index in enumerate(order):
        running = max(running, (total - rank) * p_values[index])
        adjusted[index] = min(1.0, running)
    return adjusted


def analyze_ggcorrmat(
    data: object,
    columns: object,
    *,
    conf_level: float = 0.95,
    sig_level: float = 0.05,
    p_adjust: str = "holm",
    maximum_rows: int = DEFAULT_MAX_ROWS,
) -> CorrelationMatrixAnalysis:
    """Analyze a pairwise-complete Pearson correlation matrix."""

    if not isinstance(columns, (list, tuple)):
        raise TypeError("columns must be a list or tuple of column names")
    raw_columns = cast(list[object] | tuple[object, ...], columns)
    selected_values = tuple(raw_columns)
    if any(not isinstance(column, str) or not column for column in selected_values):
        raise ValueError("columns must contain non-empty strings")
    selected = cast(tuple[str, ...], selected_values)
    if not 2 <= len(selected) <= 50 or len(set(selected)) != len(selected):
        raise ValueError("columns must contain 2-50 unique names")
    if p_adjust not in {"holm", "none"}:
        raise ValueError("p_adjust must be 'holm' or 'none'")
    if not 0.0 < sig_level < 1.0:
        raise ValueError("sig_level must be strictly between 0 and 1")
    if not isinstance(data, pl.DataFrame):
        raise TypeError("data must be a polars.DataFrame")
    if data.height > maximum_rows:
        raise ValueError(f"data exceeds maximum_rows={maximum_rows}")
    for column in selected:
        if column not in data.columns:
            raise ValueError(f"column not found: {column!r}")
        series = data.get_column(column)
        if not series.dtype.is_numeric():
            raise TypeError(f"column {column!r} must have a numeric dtype")
        finite_values = series.drop_nulls().to_numpy().astype(np.float64, copy=False)
        if not bool(np.isfinite(finite_values).all()):
            raise ValueError(f"column {column!r} contains NaN or infinite values")

    pair_results: dict[tuple[str, str], CorrelationResult] = {}
    pair_order: list[tuple[str, str]] = []
    raw_p_values: list[float] = []
    for left_index, x in enumerate(selected):
        for y in selected[left_index + 1 :]:
            try:
                pair_result = analyze_ggscatterstats(
                    data,
                    x,
                    y,
                    conf_level=conf_level,
                    maximum_rows=maximum_rows,
                ).result
            except (TypeError, ValueError) as error:
                raise ValueError(
                    f"correlation pair ({x!r}, {y!r}) failed: {error}"
                ) from error
            pair_results[(x, y)] = pair_result
            pair_order.append((x, y))
            raw_p_values.append(pair_result.test.p_value)

    if p_adjust == "holm":
        adjusted_values = [
            float(value)
            for value in statsmodels_multitest.multipletests(
                raw_p_values, method="holm"
            )[1]
        ]
        independent = _holm_adjust(raw_p_values)
        if not all(
            isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-15)
            for actual, expected in zip(adjusted_values, independent, strict=True)
        ):
            raise RuntimeError("Holm adjustment failed its independent cross-check")
    else:
        adjusted_values = list(raw_p_values)
    adjusted_by_pair = dict(zip(pair_order, adjusted_values, strict=True))

    cells: list[CorrelationMatrixCell] = []
    for x in selected:
        for y in selected:
            if x == y:
                n_obs = data.get_column(x).drop_nulls().len()
                cells.append(
                    CorrelationMatrixCell(
                        x=x,
                        y=y,
                        n_obs=n_obs,
                        estimate=1.0,
                        interval=None,
                        statistic=None,
                        df=None,
                        p_value=None,
                        adjusted_p_value=None,
                        significant=None,
                    )
                )
                continue
            pair = (x, y) if (x, y) in pair_results else (y, x)
            pair_result = pair_results[pair]
            adjusted = adjusted_by_pair[pair]
            cells.append(
                CorrelationMatrixCell(
                    x=x,
                    y=y,
                    n_obs=pair_result.sample.analyzed_rows,
                    estimate=pair_result.estimate,
                    interval=pair_result.interval,
                    statistic=pair_result.test.statistic,
                    df=pair_result.test.df,
                    p_value=pair_result.test.p_value,
                    adjusted_p_value=adjusted,
                    significant=adjusted <= sig_level,
                )
            )

    return CorrelationMatrixAnalysis(
        result=CorrelationMatrixResult(
            schema_version=1,
            analysis="ggcorrmat_pearson",
            columns=selected,
            p_adjust=p_adjust,
            sig_level=float(sig_level),
            cells=tuple(cells),
            limits=ResourceLimits(
                maximum_rows=maximum_rows,
                maximum_variables=50,
            ),
            warnings=(),
        )
    )
