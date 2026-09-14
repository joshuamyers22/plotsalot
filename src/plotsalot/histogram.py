"""M0 walking skeleton for a histogram with one-sample statistics."""

from __future__ import annotations

from importlib import import_module
from typing import Literal, Protocol, cast

import numpy as np
import polars as pl
from matplotlib.figure import Figure
from numpy.typing import NDArray

from plotsalot.core import (
    AnalysisResult,
    EffectSizeResult,
    EstimateResult,
    IntervalResult,
    SampleAudit,
    StatsPlot,
    TestResult,
)

Alternative = Literal["two-sided", "less", "greater"]
FloatArray = NDArray[np.float64]


class _TtestResult(Protocol):
    statistic: float
    pvalue: float


class _TDistribution(Protocol):
    def ppf(self, probability: float, df: float) -> float: ...


class _ScipyStats(Protocol):
    t: _TDistribution

    def ttest_1samp(
        self,
        values: FloatArray,
        *,
        popmean: float,
        alternative: Alternative,
    ) -> _TtestResult: ...


class _AxesRenderer(Protocol):
    transAxes: object

    def hist(
        self,
        values: FloatArray,
        *,
        bins: str | int,
        color: str,
        edgecolor: str,
        alpha: float,
    ) -> object: ...

    def axvline(
        self, x: float, *, color: str, linestyle: str, label: str
    ) -> object: ...

    def set_xlabel(self, label: str) -> object: ...

    def set_ylabel(self, label: str) -> object: ...

    def set_title(self, label: str) -> object: ...

    def legend(self) -> object: ...

    def text(
        self,
        x: float,
        y: float,
        text: str,
        *,
        ha: str,
        va: str,
        transform: object,
    ) -> object: ...


class _FigureRenderer(Protocol):
    def text(
        self,
        x: float,
        y: float,
        text: str,
        *,
        ha: str,
        va: str,
        fontsize: str,
    ) -> object: ...


scipy_stats = cast(_ScipyStats, import_module("scipy.stats"))

_PROTOTYPE_WARNING = (
    "M0 prototype: effect-size uncertainty and nonparametric, robust, Bayesian, "
    "and grouped modes are not implemented."
)


def _numeric_sample(data: object, column: str) -> tuple[FloatArray, SampleAudit]:
    if not isinstance(data, pl.DataFrame):
        raise TypeError("data must be a polars.DataFrame")
    if column not in data.columns:
        raise ValueError(f"column not found: {column!r}")

    series = data.get_column(column)
    if not series.dtype.is_numeric():
        raise TypeError(f"column {column!r} must have a numeric dtype")

    dropped_null_rows = series.null_count()
    values: FloatArray = series.drop_nulls().to_numpy().astype(np.float64, copy=True)
    if values.ndim != 1:
        raise ValueError("selected column must convert to a one-dimensional array")
    if values.size < 2:
        raise ValueError("one-sample t-test requires at least two non-null values")
    if not bool(np.isfinite(values).all()):
        raise ValueError("selected column contains NaN or infinite values")

    standard_deviation = float(np.std(values, ddof=1))
    if standard_deviation <= 0.0:
        raise ValueError("one-sample t-test requires nonzero sample variation")

    return values, SampleAudit(
        input_rows=data.height,
        analyzed_rows=int(values.size),
        dropped_null_rows=dropped_null_rows,
    )


def _p_value_text(p_value: float) -> str:
    return "p < 0.001" if p_value < 0.001 else f"p = {p_value:.3f}"


def gghistostats(
    data: pl.DataFrame,
    x: str,
    *,
    test_value: float = 0.0,
    alternative: Alternative = "two-sided",
    conf_level: float = 0.95,
    binwidth: float | None = None,
    title: str | None = None,
) -> StatsPlot:
    """Create the M0 parametric histogram prototype.

    The complete upstream-compatible function is not implemented yet. This
    slice proves validated Polars input, an explicit NumPy/SciPy boundary,
    structured results, traceable annotations, and Matplotlib rendering.
    """

    if not 0.0 < conf_level < 1.0:
        raise ValueError("conf_level must be strictly between 0 and 1")
    if alternative not in {"two-sided", "less", "greater"}:
        raise ValueError("alternative must be 'two-sided', 'less', or 'greater'")
    if not np.isfinite(test_value):
        raise ValueError("test_value must be finite")
    if binwidth is not None and (not np.isfinite(binwidth) or binwidth <= 0.0):
        raise ValueError("binwidth must be finite and greater than zero")

    values, sample = _numeric_sample(data, x)
    mean = float(np.mean(values))
    standard_deviation = float(np.std(values, ddof=1))
    test = scipy_stats.ttest_1samp(
        values, popmean=float(test_value), alternative=alternative
    )
    statistic = float(test.statistic)
    p_value = float(test.pvalue)
    df = float(values.size - 1)

    standard_error = standard_deviation / float(np.sqrt(values.size))
    critical = float(scipy_stats.t.ppf(0.5 + (conf_level / 2.0), df))
    margin = critical * standard_error
    effect_size = (mean - test_value) / standard_deviation

    result = AnalysisResult(
        schema_version=1,
        analysis="gghistostats_one_sample_parametric",
        column=x,
        sample=sample,
        estimate=EstimateResult(
            name="mean",
            value=mean,
            standard_deviation=standard_deviation,
        ),
        test=TestResult(
            name="one_sample_t",
            null_value=float(test_value),
            alternative=alternative,
            statistic=statistic,
            df=df,
            p_value=p_value,
        ),
        interval=IntervalResult(
            target="population_mean",
            method="student_t_two_sided",
            level=conf_level,
            low=mean - margin,
            high=mean + margin,
        ),
        effect_size=EffectSizeResult(
            name="cohen_d",
            value=effect_size,
            standardizer="sample_standard_deviation_ddof_1",
        ),
        warnings=(_PROTOTYPE_WARNING,),
    )

    if binwidth is None:
        bins: str | int = "auto"
    else:
        data_range = float(np.max(values) - np.min(values))
        bins = max(1, int(np.ceil(data_range / binwidth)))

    figure = Figure(layout="constrained")
    axes = figure.subplots()
    renderer = cast(_AxesRenderer, axes)
    renderer.hist(values, bins=bins, color="0.55", edgecolor="black", alpha=0.75)
    renderer.axvline(test_value, color="black", linestyle=":", label="test value")
    renderer.axvline(mean, color="#1f77b4", linestyle="--", label="sample mean")
    renderer.set_xlabel(x)
    renderer.set_ylabel("Count")
    renderer.set_title(title if title is not None else f"Distribution of {x}")
    renderer.legend()

    subtitle = (
        f"t({df:.0f}) = {statistic:.2f}, {_p_value_text(p_value)}, "
        f"Cohen's d = {effect_size:.2f}"
    )
    caption = (
        f"n = {sample.analyzed_rows}; {sample.dropped_null_rows} null row(s) "
        f"excluded; {conf_level:.0%} mean CI "
        f"[{result.interval.low:.2f}, {result.interval.high:.2f}]"
    )
    renderer.text(
        0.5,
        1.01,
        subtitle,
        ha="center",
        va="bottom",
        transform=renderer.transAxes,
    )
    cast(_FigureRenderer, figure).text(
        0.01, 0.01, caption, ha="left", va="bottom", fontsize="small"
    )

    return StatsPlot(
        figure=figure,
        axes={"main": axes},
        result=result,
        subtitle=subtitle,
        caption=caption,
    )


def extract_stats(plot: StatsPlot) -> AnalysisResult:
    """Return the structured result attached to a plot."""

    return plot.result


def extract_subtitle(plot: StatsPlot) -> str:
    """Return the rendered statistical subtitle source."""

    return plot.subtitle


def extract_caption(plot: StatsPlot) -> str:
    """Return the rendered caption source."""

    return plot.caption
