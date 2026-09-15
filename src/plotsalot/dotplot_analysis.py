"""Renderer-independent labeled dot-plot analysis."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import cast

import numpy as np
import polars as pl

from plotsalot.bayesian import (
    DEFAULT_MAX_BAYESIAN_WORK,
    one_sample_posterior,
)
from plotsalot.bayesian import (
    method_result as bayesian_method_result,
)
from plotsalot.bayesian_result import (
    BayesianDotEstimateResult,
    BayesianDotPlotResult,
    BayesianOneSampleResult,
)
from plotsalot.data import DEFAULT_MAX_ROWS, NumericSample, select_numeric_sample
from plotsalot.histogram_analysis import (
    Alternative,
    analyze_one_sample_sample,
    scipy_stats,
)
from plotsalot.result import (
    DotEstimateResult,
    DotPlotResult,
    IntervalResult,
    ResourceLimits,
    SampleAudit,
    ScalarIdentity,
)
from plotsalot.robust import TRIM_FRACTION, method_result, trimmed_kernel
from plotsalot.robust_result import (
    RobustDotEstimateResult,
    RobustDotPlotResult,
    RobustOneSampleResult,
)

DEFAULT_MAX_LABELS = 200


@dataclass(frozen=True, slots=True)
class DotPlotAnalysis:
    """Labeled estimates and exact overall sample used by the dot plot."""

    sample: NumericSample
    result: DotPlotResult

    def __post_init__(self) -> None:
        if self.sample.column != self.result.x:
            raise ValueError("dot plot sample and result columns must match")
        if self.sample.audit != self.result.sample:
            raise ValueError("dot plot sample and result audits must match")


def _label_identity(value: object) -> ScalarIdentity:
    if isinstance(value, bool):
        return value
    if isinstance(value, (str, int)):
        if isinstance(value, str) and not value:
            raise ValueError("dot plot labels must not be empty")
        return value
    if isinstance(value, float) and isfinite(value):
        return value
    raise TypeError("dot labels must be finite strings, integers, floats, or booleans")


def analyze_ggdotplotstats(
    data: object,
    x: str,
    y: str,
    *,
    test_value: float = 0.0,
    alternative: Alternative = "two-sided",
    conf_level: float = 0.95,
    type: str = "parametric",
    trim_fraction: float = TRIM_FRACTION,
    prior_scale: float | None = None,
    credible_level: float = 0.95,
    maximum_bayesian_work: int = DEFAULT_MAX_BAYESIAN_WORK,
    maximum_rows: int = DEFAULT_MAX_ROWS,
    maximum_labels: int = DEFAULT_MAX_LABELS,
) -> DotPlotAnalysis:
    """Analyze an approved classical, robust, or Bayesian dot-plot method."""

    if not isinstance(data, pl.DataFrame):
        raise TypeError("data must be a polars.DataFrame")
    if not 0.0 < conf_level < 1.0:
        raise ValueError("conf_level must be strictly between 0 and 1")
    if alternative not in {"two-sided", "less", "greater"}:
        raise ValueError("alternative must be 'two-sided', 'less', or 'greater'")
    if not np.isfinite(test_value):
        raise ValueError("test_value must be finite")
    if type not in {"parametric", "robust", "bayes"}:
        raise ValueError("type must be 'parametric', 'robust', or 'bayes'")
    if type == "robust" and trim_fraction != TRIM_FRACTION:
        raise ValueError("trim_fraction must equal 0.20 for M6A robust methods")
    if type == "bayes":
        if prior_scale is None:
            raise ValueError("prior_scale is required for Bayesian analysis")
        if alternative != "two-sided":
            raise ValueError("Bayesian dot alternative must be 'two-sided'")
        if conf_level != 0.95 or trim_fraction != TRIM_FRACTION:
            raise ValueError(
                "classical/robust options are unused for Bayesian analysis"
            )
    elif (
        prior_scale is not None
        or credible_level != 0.95
        or maximum_bayesian_work != DEFAULT_MAX_BAYESIAN_WORK
    ):
        raise ValueError("Bayesian options are unused for non-Bayesian analysis")
    if maximum_rows < 2:
        raise ValueError("maximum_rows must be at least two")
    if maximum_labels < 1:
        raise ValueError("maximum_labels must be at least one")
    if not x or not y or x == y:
        raise ValueError("dot plot columns must be distinct and non-empty")
    if data.height > maximum_rows:
        raise ValueError(f"data exceeds maximum_rows={maximum_rows}")
    for column in (x, y):
        if column not in data.columns:
            raise ValueError(f"column not found: {column!r}")
    if not data.get_column(x).dtype.is_numeric():
        raise TypeError(f"column {x!r} must have a numeric dtype")

    label_rows = data.select(x, y).filter(pl.col(y).is_not_null())
    partitions = label_rows.partition_by(y, maintain_order=True)
    if not partitions:
        raise ValueError("dot plot requires at least one non-null label")
    if len(partitions) > maximum_labels:
        raise ValueError(f"label count exceeds maximum_labels={maximum_labels}")

    estimates: list[
        DotEstimateResult | RobustDotEstimateResult | BayesianDotEstimateResult
    ] = []
    seen_labels: set[tuple[type[object], ScalarIdentity]] = set()
    for partition in partitions:
        label = _label_identity(partition.get_column(y)[0])
        label_key = (label.__class__, label)
        if label_key in seen_labels:
            raise ValueError(f"dot plot label is not unique after encoding: {label!r}")
        seen_labels.add(label_key)
        try:
            label_sample = select_numeric_sample(
                partition,
                x,
                minimum_size=5 if type == "robust" else (3 if type == "bayes" else 1),
                maximum_rows=maximum_rows,
            )
        except (TypeError, ValueError) as error:
            raise ValueError(f"dot plot label {label!r} is invalid: {error}") from error

        values = label_sample.values
        if type == "bayes":
            assert prior_scale is not None
            _prior, location, _effect, evidence, computation = one_sample_posterior(
                values,
                test_value=float(test_value),
                prior_scale=prior_scale,
                credible_level=credible_level,
                maximum_work=maximum_bayesian_work,
            )
            estimates.append(
                BayesianDotEstimateResult(
                    label=label,
                    sample=label_sample.audit,
                    posterior=location,
                    evidence=evidence,
                    computation=computation,
                    warnings=(),
                )
            )
            continue
        if type == "robust":
            try:
                kernel, _ = trimmed_kernel(values, trim_fraction=trim_fraction)
            except ValueError as error:
                raise ValueError(
                    f"dot plot label {label!r} is invalid: {error}"
                ) from error
            df = float(kernel.h - 1)
            critical = float(scipy_stats.t.ppf(0.5 + (conf_level / 2.0), df))
            margin = critical * float(np.sqrt(kernel.q))
            estimates.append(
                RobustDotEstimateResult(
                    label=label,
                    sample=label_sample.audit,
                    value=kernel.trimmed_mean,
                    standard_deviation=float(np.sqrt(kernel.winsorized_variance)),
                    interval=IntervalResult(
                        target="population_20pct_trimmed_location",
                        method="trimmed_mean_student_t_two_sided",
                        level=conf_level,
                        low=kernel.trimmed_mean - margin,
                        high=kernel.trimmed_mean + margin,
                    ),
                    kernel=kernel,
                    warnings=(),
                )
            )
            continue
        mean = float(np.mean(values))
        warnings: tuple[str, ...] = ()
        deviation: float | None = None
        interval: IntervalResult | None = None
        if values.size >= 2:
            candidate_deviation = float(np.std(values, ddof=1))
            if candidate_deviation > 0.0:
                deviation = candidate_deviation
                df = float(values.size - 1)
                critical = float(scipy_stats.t.ppf(0.5 + (conf_level / 2.0), df))
                margin = critical * deviation / float(np.sqrt(values.size))
                interval = IntervalResult(
                    target="population_mean",
                    method="student_t_two_sided",
                    level=conf_level,
                    low=mean - margin,
                    high=mean + margin,
                )
            else:
                warnings = ("confidence interval omitted for constant label",)
        else:
            warnings = ("confidence interval omitted for singleton label",)

        estimates.append(
            DotEstimateResult(
                label=label,
                sample=label_sample.audit,
                value=mean,
                standard_deviation=deviation,
                interval=interval,
                warnings=warnings,
            )
        )

    complete = data.select(x, y).drop_nulls()
    overall_selected = select_numeric_sample(
        complete,
        x,
        minimum_size=5 if type == "robust" else (3 if type == "bayes" else 2),
        require_variation=type != "bayes",
        maximum_rows=maximum_rows,
    )
    overall_sample = NumericSample(
        column=x,
        values=overall_selected.values,
        audit=SampleAudit(
            input_rows=data.height,
            analyzed_rows=complete.height,
            dropped_null_rows=data.height - complete.height,
        ),
    )
    one_sample = analyze_one_sample_sample(
        overall_sample,
        analysis=(
            "ggdotplotstats_one_sample_robust"
            if type == "robust"
            else (
                "ggdotplotstats_one_sample_bayesian"
                if type == "bayes"
                else "ggdotplotstats_one_sample_parametric"
            )
        ),
        test_value=test_value,
        alternative=alternative,
        conf_level=conf_level,
        trim_fraction=trim_fraction,
        prior_scale=prior_scale,
        credible_level=credible_level,
        maximum_bayesian_work=maximum_bayesian_work,
        maximum_rows=maximum_rows,
    ).result
    ordered_estimates = tuple(sorted(estimates, key=lambda estimate: estimate.value))
    warnings = tuple(
        f"{estimate.label}: {warning}"
        for estimate in ordered_estimates
        for warning in estimate.warnings
    )
    if type == "robust":
        if not isinstance(one_sample, RobustOneSampleResult) or any(
            not isinstance(estimate, RobustDotEstimateResult)
            for estimate in ordered_estimates
        ):
            raise RuntimeError("robust dot result construction is inconsistent")
        robust_result = RobustDotPlotResult(
            schema_version=2,
            analysis="ggdotplotstats_one_sample_robust",
            mode="robust",
            x=x,
            label_column=y,
            sample=overall_sample.audit,
            method=method_result("twenty_percent_trimmed_labeled_location"),
            one_sample=one_sample,
            estimates=tuple(
                estimate
                for estimate in ordered_estimates
                if isinstance(estimate, RobustDotEstimateResult)
            ),
            limits=ResourceLimits(
                maximum_rows=maximum_rows,
                maximum_labels=maximum_labels,
            ),
            warnings=warnings,
        )
        return DotPlotAnalysis(
            sample=overall_sample, result=cast(DotPlotResult, robust_result)
        )
    if type == "bayes":
        if not isinstance(one_sample, BayesianOneSampleResult) or any(
            not isinstance(estimate, BayesianDotEstimateResult)
            for estimate in ordered_estimates
        ):
            raise RuntimeError("Bayesian dot result construction is inconsistent")
        bayesian_result = BayesianDotPlotResult(
            schema_version=3,
            analysis="ggdotplotstats_one_sample_bayesian",
            mode="bayes",
            x=x,
            label_column=y,
            sample=overall_sample.audit,
            method=bayesian_method_result("conjugate_normal_labeled_location"),
            prior=one_sample.prior,
            one_sample=one_sample,
            estimates=tuple(
                estimate
                for estimate in ordered_estimates
                if isinstance(estimate, BayesianDotEstimateResult)
            ),
            limits=ResourceLimits(
                maximum_rows=maximum_rows,
                maximum_labels=maximum_labels,
            ),
            warnings=("label-level Bayes factors are pointwise",),
        )
        return DotPlotAnalysis(
            sample=overall_sample,
            result=cast(DotPlotResult, bayesian_result),
        )
    if not all(
        isinstance(estimate, DotEstimateResult) for estimate in ordered_estimates
    ):
        raise RuntimeError("parametric dot result construction is inconsistent")
    result = DotPlotResult(
        schema_version=1,
        analysis="ggdotplotstats_one_sample_parametric",
        x=x,
        label_column=y,
        sample=overall_sample.audit,
        one_sample=one_sample,
        estimates=tuple(
            estimate
            for estimate in ordered_estimates
            if isinstance(estimate, DotEstimateResult)
        ),
        limits=ResourceLimits(
            maximum_rows=maximum_rows,
            maximum_labels=maximum_labels,
        ),
        warnings=warnings,
    )
    return DotPlotAnalysis(sample=overall_sample, result=result)
