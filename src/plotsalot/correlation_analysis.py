"""Approved Pearson scatter and correlation-matrix analyses."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from math import atanh, isclose, sqrt, tanh
from typing import Protocol, cast
from warnings import catch_warnings, simplefilter

import numpy as np
import polars as pl

from plotsalot.bayesian import (
    CORRELATION_RESERVED_WORK,
    DEFAULT_MAX_BAYESIAN_WORK,
    correlation_posterior,
    correlation_prior,
    validate_work_limit,
)
from plotsalot.bayesian import (
    method_result as bayesian_method_result,
)
from plotsalot.bayesian_result import (
    BayesianCorrelationMatrixCell,
    BayesianCorrelationMatrixResult,
    BayesianCorrelationResult,
)
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
from plotsalot.robust import (
    DEFAULT_BOOTSTRAP_RESAMPLES,
    DEFAULT_MAX_RESAMPLE_WORK,
    TRIM_FRACTION,
    bootstrap_winsorized_correlation,
    child_seed,
    method_result,
    validate_resampling,
    winsorized_correlation,
)
from plotsalot.robust_result import (
    RobustCorrelationMatrixCell,
    RobustCorrelationMatrixResult,
    RobustCorrelationResult,
    RobustTestResult,
)


class _PearsonResult(Protocol):
    statistic: float
    pvalue: float


class _NormalDistribution(Protocol):
    def ppf(self, probability: float) -> float: ...


class _TDistribution(Protocol):
    def sf(self, value: float, df: float) -> float: ...


class _ScipyStats(Protocol):
    norm: _NormalDistribution
    t: _TDistribution

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


def _robust_pair(
    sample: PairedNumericSample,
    *,
    conf_level: float,
    bootstrap_resamples: int,
    root_seed: int,
    derived_seed: int,
    seed_identity: str,
    maximum_rows: int,
    maximum_resample_work: int,
) -> RobustCorrelationResult:
    estimate, covariance, x_kernel, y_kernel = winsorized_correlation(
        sample.x_values, sample.y_values
    )
    if x_kernel.h < 4:
        raise ValueError("robust association requires effective count h>=4")
    df = float(x_kernel.h - 2)
    warnings: tuple[str, ...] = (
        "marginal Winsorization is not a high-breakdown bivariate estimator",
    )
    if abs(estimate) == 1.0:
        statistic = None
        p_value = 0.0
        warnings += ("perfect_winsorized_correlation",)
    else:
        statistic = estimate * sqrt(
            (sample.audit.analyzed_rows - 2) / (1.0 - (estimate * estimate))
        )
        p_value = min(1.0, 2.0 * float(scipy_stats.t.sf(abs(statistic), df)))
    low, high, resampling = bootstrap_winsorized_correlation(
        sample.x_values,
        sample.y_values,
        conf_level=conf_level,
        bootstrap_resamples=bootstrap_resamples,
        root_seed=root_seed,
        derived_seed=derived_seed,
        child_identity=seed_identity,
        maximum_resample_work=maximum_resample_work,
    )
    return RobustCorrelationResult(
        schema_version=2,
        analysis="ggscatterstats_winsorized",
        mode="robust",
        x=sample.x,
        y=sample.y,
        sample=sample.audit,
        method=method_result("marginal_twenty_percent_winsorized_pearson"),
        x_kernel=x_kernel,
        y_kernel=y_kernel,
        winsorized_covariance=covariance,
        estimate=estimate,
        test=RobustTestResult(
            name="winsorized_correlation_t",
            target="population_winsorized_pearson_r",
            null_value=0.0,
            alternative="two-sided",
            statistic=statistic,
            df1=None,
            df2=df,
            p_value=p_value,
            reference_distribution="student_t",
        ),
        interval=IntervalResult(
            target="population_winsorized_pearson_r",
            method="paired_percentile_bootstrap_type7_pointwise",
            level=conf_level,
            low=low,
            high=high,
        ),
        resampling=resampling,
        limits=ResourceLimits(maximum_rows=maximum_rows),
        warnings=warnings,
    )


def analyze_ggscatterstats(
    data: pl.DataFrame,
    x: str,
    y: str,
    *,
    conf_level: float = 0.95,
    maximum_rows: int = DEFAULT_MAX_ROWS,
    type: str = "parametric",
    trim_fraction: float = TRIM_FRACTION,
    bootstrap_resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
    random_seed: int | None = None,
    maximum_resample_work: int = DEFAULT_MAX_RESAMPLE_WORK,
    correlation_prior_shape: float = 1.0,
    credible_level: float = 0.95,
    maximum_bayesian_work: int = DEFAULT_MAX_BAYESIAN_WORK,
) -> CorrelationAnalysis:
    """Analyze an approved classical, robust, or Bayesian correlation."""

    if not 0.0 < conf_level < 1.0:
        raise ValueError("conf_level must be strictly between 0 and 1")
    if type not in {"parametric", "robust", "bayes"}:
        raise ValueError("type must be 'parametric', 'robust', or 'bayes'")
    if type == "parametric" and (
        trim_fraction != TRIM_FRACTION
        or bootstrap_resamples != DEFAULT_BOOTSTRAP_RESAMPLES
        or random_seed is not None
        or maximum_resample_work != DEFAULT_MAX_RESAMPLE_WORK
        or correlation_prior_shape != 1.0
        or credible_level != 0.95
        or maximum_bayesian_work != DEFAULT_MAX_BAYESIAN_WORK
    ):
        raise ValueError("robust/Bayesian options are unused for parametric analysis")
    if type == "robust" and (
        correlation_prior_shape != 1.0
        or credible_level != 0.95
        or maximum_bayesian_work != DEFAULT_MAX_BAYESIAN_WORK
    ):
        raise ValueError("Bayesian options are unused for robust analysis")
    if type == "bayes" and (
        conf_level != 0.95
        or trim_fraction != TRIM_FRACTION
        or bootstrap_resamples != DEFAULT_BOOTSTRAP_RESAMPLES
        or random_seed is not None
        or maximum_resample_work != DEFAULT_MAX_RESAMPLE_WORK
    ):
        raise ValueError("classical/robust options are unused for Bayesian analysis")
    sample = select_numeric_pair(
        data,
        x,
        y,
        minimum_size=8 if type == "robust" else 4,
        require_variation=True,
        maximum_rows=maximum_rows,
    )
    if type == "robust":
        if trim_fraction != TRIM_FRACTION:
            raise ValueError("trim_fraction must equal 0.20 for M6A robust methods")
        work = sample.audit.analyzed_rows * bootstrap_resamples
        root_seed = validate_resampling(
            bootstrap_resamples=bootstrap_resamples,
            random_seed=random_seed,
            maximum_resample_work=maximum_resample_work,
            calculated_work=work,
        )
        result = _robust_pair(
            sample,
            conf_level=conf_level,
            bootstrap_resamples=bootstrap_resamples,
            root_seed=root_seed,
            derived_seed=root_seed,
            seed_identity=f"direct:{x}|{y}",
            maximum_rows=maximum_rows,
            maximum_resample_work=maximum_resample_work,
        )
        return CorrelationAnalysis(
            sample=sample, result=cast(CorrelationResult, result)
        )
    if type == "bayes":
        sample_r, prior, posterior, evidence, computation = correlation_posterior(
            sample.x_values,
            sample.y_values,
            prior_shape=correlation_prior_shape,
            credible_level=credible_level,
            maximum_work=maximum_bayesian_work,
        )
        return CorrelationAnalysis(
            sample=sample,
            result=cast(
                CorrelationResult,
                BayesianCorrelationResult(
                    schema_version=3,
                    analysis="ggscatterstats_bayesian_pearson",
                    mode="bayes",
                    x=x,
                    y=y,
                    sample=sample.audit,
                    method=bayesian_method_result("exact_sample_correlation"),
                    prior=prior,
                    posterior=posterior,
                    evidence=evidence,
                    computation=computation,
                    sample_correlation=sample_r,
                    limits=ResourceLimits(maximum_rows=maximum_rows),
                    warnings=(
                        "pointwise adapted Bayesian correlation under "
                        "bivariate normality",
                    ),
                ),
            ),
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
    type: str = "parametric",
    trim_fraction: float = TRIM_FRACTION,
    bootstrap_resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
    random_seed: int | None = None,
    maximum_resample_work: int = DEFAULT_MAX_RESAMPLE_WORK,
    correlation_prior_shape: float = 1.0,
    credible_level: float = 0.95,
    maximum_bayesian_work: int = DEFAULT_MAX_BAYESIAN_WORK,
) -> CorrelationMatrixAnalysis:
    """Analyze a classical, robust, or Bayesian correlation matrix."""

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
    if type not in {"parametric", "robust", "bayes"}:
        raise ValueError("type must be 'parametric', 'robust', or 'bayes'")
    if type == "parametric" and (
        trim_fraction != TRIM_FRACTION
        or bootstrap_resamples != DEFAULT_BOOTSTRAP_RESAMPLES
        or random_seed is not None
        or maximum_resample_work != DEFAULT_MAX_RESAMPLE_WORK
        or correlation_prior_shape != 1.0
        or credible_level != 0.95
        or maximum_bayesian_work != DEFAULT_MAX_BAYESIAN_WORK
    ):
        raise ValueError("robust/Bayesian options are unused for parametric analysis")
    if type == "robust" and (
        correlation_prior_shape != 1.0
        or credible_level != 0.95
        or maximum_bayesian_work != DEFAULT_MAX_BAYESIAN_WORK
    ):
        raise ValueError("Bayesian options are unused for robust analysis")
    if type == "bayes" and (
        conf_level != 0.95
        or sig_level != 0.05
        or p_adjust != "none"
        or trim_fraction != TRIM_FRACTION
        or bootstrap_resamples != DEFAULT_BOOTSTRAP_RESAMPLES
        or random_seed is not None
        or maximum_resample_work != DEFAULT_MAX_RESAMPLE_WORK
    ):
        raise ValueError(
            "classical/robust options are unused for Bayesian matrix analysis; "
            "p_adjust must be 'none'"
        )
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

    if type == "bayes":
        unique_pair_count = len(selected) * (len(selected) - 1) // 2
        validate_work_limit(
            maximum_bayesian_work,
            unique_pair_count * CORRELATION_RESERVED_WORK,
        )
        bayesian_pairs: dict[tuple[str, str], BayesianCorrelationResult] = {}
        actual_work = 0
        for left_index, x in enumerate(selected):
            for y in selected[left_index + 1 :]:
                try:
                    pair = analyze_ggscatterstats(
                        data,
                        x,
                        y,
                        type="bayes",
                        correlation_prior_shape=correlation_prior_shape,
                        credible_level=credible_level,
                        maximum_bayesian_work=maximum_bayesian_work,
                        maximum_rows=maximum_rows,
                    ).result
                except (TypeError, ValueError) as error:
                    raise ValueError(
                        f"correlation pair ({x!r}, {y!r}) failed: {error}"
                    ) from error
                if not isinstance(pair, BayesianCorrelationResult):
                    raise RuntimeError(
                        "Bayesian matrix pair construction is inconsistent"
                    )
                bayesian_pairs[(x, y)] = pair
                actual_work += pair.computation.calculated_work
        validate_work_limit(maximum_bayesian_work, actual_work)
        bayesian_cells: list[BayesianCorrelationMatrixCell] = []
        for x in selected:
            for y in selected:
                if x == y:
                    bayesian_cells.append(
                        BayesianCorrelationMatrixCell(
                            x=x,
                            y=y,
                            n_obs=data.get_column(x).drop_nulls().len(),
                            posterior=None,
                            evidence=None,
                        )
                    )
                    continue
                key = (x, y) if (x, y) in bayesian_pairs else (y, x)
                pair = bayesian_pairs[key]
                bayesian_cells.append(
                    BayesianCorrelationMatrixCell(
                        x=x,
                        y=y,
                        n_obs=pair.sample.analyzed_rows,
                        posterior=pair.posterior,
                        evidence=pair.evidence,
                    )
                )
        result = BayesianCorrelationMatrixResult(
            schema_version=3,
            analysis="ggcorrmat_bayesian_pearson",
            mode="bayes",
            columns=selected,
            method=bayesian_method_result("exact_sample_correlation_matrix"),
            prior=correlation_prior(correlation_prior_shape),
            cells=tuple(bayesian_cells),
            evidence_scope="pointwise_no_multiplicity_adjustment",
            calculated_bayesian_work=actual_work,
            maximum_bayesian_work=maximum_bayesian_work,
            limits=ResourceLimits(maximum_rows=maximum_rows, maximum_variables=50),
            warnings=(
                "Bayes factors and credible intervals are pointwise",
                "no frequentist multiplicity adjustment is applied",
            ),
        )
        return CorrelationMatrixAnalysis(result=cast(CorrelationMatrixResult, result))

    if type == "robust" and trim_fraction != TRIM_FRACTION:
        raise ValueError("trim_fraction must equal 0.20 for M6A robust methods")
    pair_samples: dict[tuple[str, str], PairedNumericSample] = {}
    if type == "robust":
        total_work = 0
        for left_index, x in enumerate(selected):
            for y in selected[left_index + 1 :]:
                try:
                    pair_sample = select_numeric_pair(
                        data,
                        x,
                        y,
                        minimum_size=8,
                        require_variation=True,
                        maximum_rows=maximum_rows,
                    )
                    winsorized_correlation(pair_sample.x_values, pair_sample.y_values)
                except (TypeError, ValueError) as error:
                    raise ValueError(
                        f"correlation pair ({x!r}, {y!r}) failed: {error}"
                    ) from error
                pair_samples[(x, y)] = pair_sample
                total_work += pair_sample.audit.analyzed_rows * bootstrap_resamples
        root_seed = validate_resampling(
            bootstrap_resamples=bootstrap_resamples,
            random_seed=random_seed,
            maximum_resample_work=maximum_resample_work,
            calculated_work=total_work,
        )
    else:
        total_work = 0
        root_seed = 0

    pair_results: dict[
        tuple[str, str], CorrelationResult | RobustCorrelationResult
    ] = {}
    pair_order: list[tuple[str, str]] = []
    raw_p_values: list[float] = []
    for left_index, x in enumerate(selected):
        for y in selected[left_index + 1 :]:
            try:
                if type == "robust":
                    derived, identity = child_seed(
                        root_seed,
                        "ggcorrmat_winsorized",
                        tuple(sorted((x, y))),
                    )
                    pair_result = _robust_pair(
                        pair_samples[(x, y)],
                        conf_level=conf_level,
                        bootstrap_resamples=bootstrap_resamples,
                        root_seed=root_seed,
                        derived_seed=derived,
                        seed_identity=identity,
                        maximum_rows=maximum_rows,
                        maximum_resample_work=maximum_resample_work,
                    )
                else:
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

    if type == "robust":
        robust_cells: list[RobustCorrelationMatrixCell] = []
        for x in selected:
            for y in selected:
                if x == y:
                    n_obs = data.get_column(x).drop_nulls().len()
                    robust_cells.append(
                        RobustCorrelationMatrixCell(
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
                            x_kernel=None,
                            y_kernel=None,
                            winsorized_covariance=None,
                            resampling=None,
                        )
                    )
                    continue
                pair = (x, y) if (x, y) in pair_results else (y, x)
                pair_result = pair_results[pair]
                if not isinstance(pair_result, RobustCorrelationResult):
                    raise RuntimeError(
                        "robust matrix pair construction is inconsistent"
                    )
                adjusted = adjusted_by_pair[pair]
                forward = pair == (x, y)
                robust_cells.append(
                    RobustCorrelationMatrixCell(
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
                        x_kernel=(
                            pair_result.x_kernel if forward else pair_result.y_kernel
                        ),
                        y_kernel=(
                            pair_result.y_kernel if forward else pair_result.x_kernel
                        ),
                        winsorized_covariance=pair_result.winsorized_covariance,
                        resampling=pair_result.resampling,
                    )
                )
        robust_matrix = RobustCorrelationMatrixResult(
            schema_version=2,
            analysis="ggcorrmat_winsorized",
            mode="robust",
            columns=selected,
            method=method_result("marginal_twenty_percent_winsorized_pearson"),
            p_adjust=p_adjust,
            sig_level=float(sig_level),
            cells=tuple(robust_cells),
            limits=ResourceLimits(maximum_rows=maximum_rows, maximum_variables=50),
            maximum_resample_work=maximum_resample_work,
            calculated_resample_work=total_work,
            warnings=(
                "intervals are pointwise and unadjusted",
                "marginal Winsorization is not a high-breakdown bivariate estimator",
            ),
        )
        return CorrelationMatrixAnalysis(
            result=cast(CorrelationMatrixResult, robust_matrix)
        )

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
            if not isinstance(pair_result, CorrelationResult):
                raise RuntimeError(
                    "parametric matrix pair construction is inconsistent"
                )
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
