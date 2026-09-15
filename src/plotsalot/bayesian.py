"""Approved native M6B Bayesian numerical kernels."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from hashlib import sha256
from importlib import import_module
from importlib.metadata import version
from math import exp, isfinite, log, pi, sqrt
from typing import Protocol, cast
from warnings import catch_warnings, simplefilter

import numpy as np

from plotsalot.bayesian_result import (
    BayesFactorSensitivity,
    BayesianComparisonLevelResult,
    BayesianComputationResult,
    BayesianEvidenceResult,
    BayesianMethodResult,
    BayesianPairwiseComparisonResult,
    BayesianPosteriorSummary,
    BayesianPriorResult,
    BayesianQmcTargetDiagnostic,
    PriorParameter,
    bounded_bf10_text,
)
from plotsalot.data import FloatArray
from plotsalot.result import IntervalResult, ScalarIdentity

DEFAULT_MAX_BAYESIAN_WORK = 100_000_000
HARD_MAX_BAYESIAN_WORK = 500_000_000
QUAD_EPSABS = 1e-12
QUAD_EPSREL = 1e-10
QUAD_LIMIT = 200
# QUADPACK uses an initial 21-point rule and adds at most 42 evaluations for
# each additional subdivision. Three normalizers plus three 100-iteration
# Brent solves (at most 102 function calls each) and the null-tail probability
# require no more than 310 quadrature calls.
CORRELATION_QUAD_CALL_MAX_EVALUATIONS = 21 + 42 * (QUAD_LIMIT - 1)
CORRELATION_RESERVED_WORK = 310 * CORRELATION_QUAD_CALL_MAX_EVALUATIONS


class _TDistribution(Protocol):
    def ppf(
        self, probability: float, df: float, *, loc: float, scale: float
    ) -> float: ...

    def cdf(self, value: float, df: float, *, loc: float, scale: float) -> float: ...

    def logpdf(self, value: float, df: float, *, loc: float, scale: float) -> float: ...


class _BetaDistribution(Protocol):
    def ppf(self, probability: float, left: float, right: float) -> float: ...

    def cdf(self, value: float, left: float, right: float) -> float: ...


class _Stats(Protocol):
    t: _TDistribution
    beta: _BetaDistribution


class _Special(Protocol):
    def gammaln(self, value: float) -> float: ...

    def log_expit(self, value: float) -> float: ...

    def betaln(self, left: float, right: float) -> float: ...

    def hyp2f1(self, a: float, b: float, c: float, z: float) -> float: ...

    def ndtri(self, value: object) -> object: ...

    def gammainccinv(self, a: float, value: object) -> object: ...


class _OptimizeResult(Protocol):
    success: bool
    fun: float
    x: float


class _Optimize(Protocol):
    def minimize_scalar(
        self,
        function: Callable[[float], float],
        *,
        bounds: tuple[float, float],
        method: str,
        options: dict[str, float],
    ) -> _OptimizeResult: ...

    def brentq(
        self,
        function: Callable[[float], float],
        low: float,
        high: float,
        *,
        xtol: float,
        rtol: float,
        maxiter: int,
    ) -> float: ...


class _Integrate(Protocol):
    IntegrationWarning: type[Warning]

    def quad(
        self,
        function: Callable[[float], float],
        low: float,
        high: float,
        *,
        epsabs: float,
        epsrel: float,
        limit: int,
        full_output: int,
    ) -> tuple[float, float, dict[str, int]]: ...


class _SobolEngine(Protocol):
    def random_base2(self, power: int) -> np.ndarray: ...


class _QMC(Protocol):
    def Sobol(self, dimension: int, *, scramble: bool, seed: int) -> _SobolEngine: ...


scipy_stats = cast(_Stats, import_module("scipy.stats"))
scipy_special = cast(_Special, import_module("scipy.special"))
scipy_optimize = cast(_Optimize, import_module("scipy.optimize"))
scipy_integrate = cast(_Integrate, import_module("scipy.integrate"))
scipy_qmc = cast(_QMC, import_module("scipy.stats.qmc"))


@dataclass(frozen=True, slots=True)
class _NIGPosterior:
    kappa: float
    mean: float
    shape: float
    scale: float
    log_marginal: float


def method_result(name: str) -> BayesianMethodResult:
    """Return locked M6B method/software provenance."""

    return BayesianMethodResult(
        name=name,
        version="m6b-1",
        compatibility="adapted",
        numpy_version=np.__version__,
        scipy_version=version("scipy"),
    )


def validate_credible_level(level: float) -> float:
    """Validate the approved equal-tail credible interval range."""

    if not isfinite(level) or not 0.80 <= level <= 0.99:
        raise ValueError("credible_level must lie within [0.80, 0.99]")
    return float(level)


def validate_prior_scale(prior_scale: float) -> float:
    """Validate an outcome-unit continuous prior scale."""

    if not isfinite(prior_scale) or prior_scale <= 0.0:
        raise ValueError("prior_scale must be finite and positive")
    return float(prior_scale)


def validate_work_limit(maximum_work: int, calculated_work: int) -> None:
    """Preflight an approved Bayesian work request."""

    if type(maximum_work) is not int or not 1 <= maximum_work <= HARD_MAX_BAYESIAN_WORK:
        raise ValueError(
            "maximum_bayesian_work must be an integer from 1 through 500000000"
        )
    if calculated_work < 1 or calculated_work > maximum_work:
        raise ValueError(
            f"Bayesian work {calculated_work} exceeds maximum_bayesian_work="
            f"{maximum_work}"
        )


def continuous_prior(prior_location: float, prior_scale: float) -> BayesianPriorResult:
    """Create the approved outcome-unit normal-inverse-gamma prior record."""

    if not isfinite(prior_location):
        raise ValueError("prior_location must be finite")
    scale = validate_prior_scale(prior_scale)
    return BayesianPriorResult(
        family="standardized_normal_inverse_gamma",
        proper=True,
        parameters=(
            PriorParameter("prior_location", float(prior_location), "outcome_units"),
            PriorParameter("prior_scale", scale, "outcome_units"),
            PriorParameter("variance_shape", 2.0, "dimensionless"),
            PriorParameter("variance_scale", 1.0, "standardized_variance"),
            PriorParameter("location_kappa", 2.0, "dimensionless"),
        ),
    )


def correlation_prior(shape: float) -> BayesianPriorResult:
    """Create the approved symmetric beta prior on transformed correlation."""

    if not isfinite(shape) or shape <= 0.0:
        raise ValueError("correlation_prior_shape must be finite and positive")
    return BayesianPriorResult(
        family="symmetric_beta_transformed_correlation",
        proper=True,
        parameters=(
            PriorParameter("shape_left", float(shape), "dimensionless"),
            PriorParameter("shape_right", float(shape), "dimensionless"),
        ),
    )


def _nig_posterior(values: FloatArray) -> _NIGPosterior:
    n = int(values.size)
    mean = float(np.mean(values))
    centered = values - mean
    sum_squares = float(centered @ centered)
    kappa = 2.0 + n
    posterior_mean = n * mean / kappa
    shape = 2.0 + (n / 2.0)
    scale = 1.0 + 0.5 * sum_squares + (2.0 * n * mean * mean) / (2.0 * kappa)
    log_marginal = (
        scipy_special.gammaln(shape)
        - scipy_special.gammaln(2.0)
        - shape * log(scale)
        + 0.5 * (log(2.0) - log(kappa))
        - 0.5 * n * log(2.0 * pi)
    )
    return _NIGPosterior(
        kappa=kappa,
        mean=posterior_mean,
        shape=shape,
        scale=scale,
        log_marginal=float(log_marginal),
    )


def _fixed_zero_log_marginal(values: FloatArray) -> float:
    n = int(values.size)
    shape = 2.0 + n / 2.0
    scale = 1.0 + 0.5 * float(values @ values)
    return float(
        scipy_special.gammaln(shape)
        - scipy_special.gammaln(2.0)
        - shape * log(scale)
        - 0.5 * n * log(2.0 * pi)
    )


def _one_sample_log_bf(
    values: FloatArray, prior_location: float, prior_scale: float
) -> float:
    standardized = np.asarray((values - prior_location) / prior_scale, dtype=np.float64)
    posterior = _nig_posterior(standardized)
    value = posterior.log_marginal - _fixed_zero_log_marginal(standardized)
    if not isfinite(value):
        raise ValueError("one-sample log BF10 is non-finite")
    return float(value)


def one_sample_posterior(
    values: FloatArray,
    *,
    test_value: float,
    prior_scale: float,
    credible_level: float,
    maximum_work: int = DEFAULT_MAX_BAYESIAN_WORK,
) -> tuple[
    BayesianPriorResult,
    BayesianPosteriorSummary,
    BayesianPosteriorSummary,
    BayesianEvidenceResult,
    BayesianComputationResult,
]:
    """Compute the approved exact Bayesian one-sample analysis."""

    level = validate_credible_level(credible_level)
    scale = validate_prior_scale(prior_scale)
    if not isfinite(test_value):
        raise ValueError("test_value must be finite")
    if values.size < 3 or not bool(np.isfinite(values).all()):
        raise ValueError("Bayesian one-sample analysis requires three finite values")
    validate_work_limit(maximum_work, 3 * int(values.size))
    standardized = np.asarray((values - test_value) / scale, dtype=np.float64)
    posterior = _nig_posterior(standardized)
    degrees = 2.0 * posterior.shape
    posterior_scale = sqrt(posterior.scale / (posterior.shape * posterior.kappa))
    tail = (1.0 - level) / 2.0
    low_z = scipy_stats.t.ppf(tail, degrees, loc=posterior.mean, scale=posterior_scale)
    high_z = scipy_stats.t.ppf(
        1.0 - tail, degrees, loc=posterior.mean, scale=posterior_scale
    )
    below = float(
        scipy_stats.t.cdf(0.0, degrees, loc=posterior.mean, scale=posterior_scale)
    )
    below = min(1.0, max(0.0, below))
    effect_median = scale * posterior.mean
    effect_interval = IntervalResult(
        target="population_mean_difference",
        method="bayesian_equal_tail",
        level=level,
        low=scale * float(low_z),
        high=scale * float(high_z),
    )
    effect = BayesianPosteriorSummary(
        target="population_mean_difference",
        median=effect_median,
        null_value=0.0,
        interval=effect_interval,
        probability_above_null=1.0 - below,
        probability_below_null=below,
        probability_at_null=0.0,
    )
    location = BayesianPosteriorSummary(
        target="population_mean",
        median=test_value + effect_median,
        null_value=float(test_value),
        interval=IntervalResult(
            target="population_mean",
            method="bayesian_equal_tail",
            level=level,
            low=test_value + effect_interval.low,
            high=test_value + effect_interval.high,
        ),
        probability_above_null=effect.probability_above_null,
        probability_below_null=effect.probability_below_null,
        probability_at_null=0.0,
    )
    log_bf10 = posterior.log_marginal - _fixed_zero_log_marginal(standardized)
    sensitivity = tuple(
        BayesFactorSensitivity(
            label, candidate, _one_sample_log_bf(values, test_value, candidate)
        )
        for label, candidate in (("half", scale * 0.5), ("double", scale * 2.0))
    )
    evidence = BayesianEvidenceResult(
        null_hypothesis="population_mean_equals_test_value",
        alternative_hypothesis="population_mean_has_approved_nig_prior",
        sampling_plan="iid_normal_fixed_n",
        log_bf10=float(log_bf10),
        display=bounded_bf10_text(float(log_bf10)),
        prior_model_odds=1.0,
        sensitivity=sensitivity,
    )
    computation = BayesianComputationResult(
        algorithm="closed_form_normal_inverse_gamma",
        evaluations=0,
        absolute_tolerance=None,
        relative_tolerance=None,
        estimated_error=None,
        calculated_work=3 * int(values.size),
        maximum_work=maximum_work,
        hard_maximum_work=HARD_MAX_BAYESIAN_WORK,
        root_seed=None,
        diagnostics=("closed_form_finite", "mcmc_diagnostics_not_applicable"),
    )
    return (
        continuous_prior(float(test_value), scale),
        location,
        effect,
        evidence,
        computation,
    )


def _log_correlation_kernel(u: float, r: float, n: int, shape: float) -> float:
    log_x = float(scipy_special.log_expit(2.0 * u))
    log_one_minus_x = float(scipy_special.log_expit(-2.0 * u))
    rho = float(np.tanh(u))
    log_one_minus_rho_squared = log(4.0) + log_x + log_one_minus_x
    hypergeometric = float(
        scipy_special.hyp2f1(0.5, 0.5, n - 0.5, (1.0 + rho * r) / 2.0)
    )
    if hypergeometric <= 0.0 or not isfinite(hypergeometric):
        return -np.inf
    log_likelihood = (
        ((n - 1.0) / 2.0) * log_one_minus_rho_squared
        - (n - 1.5) * log(1.0 - rho * r)
        + log(hypergeometric)
    )
    log_prior_and_jacobian = (
        log(2.0)
        - float(scipy_special.betaln(shape, shape))
        + shape * (log_x + log_one_minus_x)
    )
    return log_likelihood + log_prior_and_jacobian


def _log_correlation_likelihood_at_zero(r: float, n: int) -> float:
    hypergeometric = float(scipy_special.hyp2f1(0.5, 0.5, n - 0.5, 0.5))
    if hypergeometric <= 0.0 or not isfinite(hypergeometric):
        raise ValueError("correlation null likelihood is non-finite")
    return log(hypergeometric)


@dataclass(frozen=True, slots=True)
class _CorrelationIntegral:
    log_bf10: float
    mode: float
    mode_location: float
    total: float
    error: float
    evaluations: int


def _correlation_integral(r: float, n: int, shape: float) -> _CorrelationIntegral:
    log_null = _log_correlation_likelihood_at_zero(r, n)

    def objective(value: float) -> float:
        return -(_log_correlation_kernel(value, r, n, shape) - log_null)

    optimum = scipy_optimize.minimize_scalar(
        objective, bounds=(-30.0, 30.0), method="bounded", options={"xatol": 1e-12}
    )
    if not optimum.success or not isfinite(float(optimum.fun)):
        raise ValueError("correlation posterior mode search failed")
    mode = -float(optimum.fun)

    def scaled_integrand(value: float) -> float:
        candidate = _log_correlation_kernel(value, r, n, shape) - log_null - mode
        return 0.0 if candidate < -745.0 else exp(candidate)

    with catch_warnings():
        simplefilter("error", scipy_integrate.IntegrationWarning)
        try:
            value, error, info = scipy_integrate.quad(
                scaled_integrand,
                -np.inf,
                np.inf,
                epsabs=QUAD_EPSABS,
                epsrel=QUAD_EPSREL,
                limit=QUAD_LIMIT,
                full_output=1,
            )
        except (Warning, ValueError) as failure:
            raise ValueError(f"correlation quadrature failed: {failure}") from failure
    if value <= 0.0 or not isfinite(value) or not isfinite(error):
        raise ValueError("correlation quadrature returned an invalid integral")
    tolerance = max(QUAD_EPSABS, QUAD_EPSREL * abs(value))
    if error > tolerance:
        raise ValueError("correlation quadrature exceeded its error tolerance")
    log_bf10 = mode + log(value)
    if not isfinite(log_bf10):
        raise ValueError("correlation log BF10 is non-finite")
    return _CorrelationIntegral(
        log_bf10=log_bf10,
        mode=mode,
        mode_location=float(optimum.x),
        total=float(value),
        error=float(error),
        evaluations=int(info["neval"]),
    )


def correlation_posterior(
    x: FloatArray,
    y: FloatArray,
    *,
    prior_shape: float,
    credible_level: float,
    maximum_work: int = DEFAULT_MAX_BAYESIAN_WORK,
) -> tuple[
    float,
    BayesianPriorResult,
    BayesianPosteriorSummary,
    BayesianEvidenceResult,
    BayesianComputationResult,
]:
    """Compute the approved exact-density Bayesian correlation analysis."""

    level = validate_credible_level(credible_level)
    if not isfinite(prior_shape) or prior_shape <= 0.0:
        raise ValueError("correlation_prior_shape must be finite and positive")
    if x.shape != y.shape or x.size < 4:
        raise ValueError("Bayesian correlation requires four aligned pairs")
    if not bool(np.isfinite(x).all()) or not bool(np.isfinite(y).all()):
        raise ValueError("Bayesian correlation values must be finite")
    validate_work_limit(maximum_work, CORRELATION_RESERVED_WORK)
    r = float(np.corrcoef(x, y)[0, 1])
    if not isfinite(r) or not -1.0 < r < 1.0:
        raise ValueError("bayesian_perfect_correlation_unsupported")
    primary = _correlation_integral(r, int(x.size), float(prior_shape))
    half = _correlation_integral(r, int(x.size), float(prior_shape) * 0.5)
    double = _correlation_integral(r, int(x.size), float(prior_shape) * 2.0)

    def primary_scaled(value: float) -> float:
        candidate = (
            _log_correlation_kernel(value, r, int(x.size), float(prior_shape))
            - _log_correlation_likelihood_at_zero(r, int(x.size))
            - primary.mode
        )
        return 0.0 if candidate < -745.0 else exp(candidate)

    evaluations = primary.evaluations + half.evaluations + double.evaluations
    maximum_estimated_error = max(primary.error, half.error, double.error)

    def probability_below(u: float) -> float:
        nonlocal evaluations, maximum_estimated_error
        low, high = (-np.inf, u) if u <= primary.mode_location else (u, np.inf)
        with catch_warnings():
            simplefilter("error", scipy_integrate.IntegrationWarning)
            try:
                value, error, info = scipy_integrate.quad(
                    primary_scaled,
                    low,
                    high,
                    epsabs=QUAD_EPSABS,
                    epsrel=QUAD_EPSREL,
                    limit=QUAD_LIMIT,
                    full_output=1,
                )
            except (Warning, ValueError) as failure:
                raise ValueError(
                    f"correlation tail quadrature failed: {failure}"
                ) from failure
        if value < 0.0 or not isfinite(value) or not isfinite(error):
            raise ValueError("correlation tail quadrature returned an invalid integral")
        tolerance = max(QUAD_EPSABS, QUAD_EPSREL * abs(value))
        if error > tolerance:
            raise ValueError("correlation tail quadrature exceeded its error tolerance")
        maximum_estimated_error = max(maximum_estimated_error, float(error))
        probability = (
            value / primary.total
            if u <= primary.mode_location
            else 1.0 - value / primary.total
        )
        evaluations += int(info["neval"])
        return min(1.0, max(0.0, float(probability)))

    tail = (1.0 - level) / 2.0

    def quantile(probability: float) -> float:
        def objective(value: float) -> float:
            return probability_below(value) - probability

        root = scipy_optimize.brentq(
            objective,
            -30.0,
            30.0,
            xtol=1e-12,
            rtol=1e-12,
            maxiter=100,
        )
        return float(np.tanh(root))

    low = quantile(tail)
    median = quantile(0.5)
    high = quantile(1.0 - tail)
    below = min(1.0, max(0.0, probability_below(0.0)))
    if evaluations > CORRELATION_RESERVED_WORK:
        raise RuntimeError("correlation quadrature exceeded its preflight reservation")
    posterior = BayesianPosteriorSummary(
        target="population_pearson_rho",
        median=median,
        null_value=0.0,
        interval=IntervalResult(
            target="population_pearson_rho",
            method="bayesian_equal_tail",
            level=level,
            low=low,
            high=high,
        ),
        probability_above_null=1.0 - below,
        probability_below_null=below,
        probability_at_null=0.0,
    )
    evidence = BayesianEvidenceResult(
        null_hypothesis="population_pearson_rho_equals_zero",
        alternative_hypothesis="population_pearson_rho_has_symmetric_beta_prior",
        sampling_plan="exact_sample_correlation_fixed_n",
        log_bf10=primary.log_bf10,
        display=bounded_bf10_text(primary.log_bf10),
        prior_model_odds=1.0,
        sensitivity=(
            BayesFactorSensitivity("half", prior_shape * 0.5, half.log_bf10),
            BayesFactorSensitivity("double", prior_shape * 2.0, double.log_bf10),
        ),
    )
    computation = BayesianComputationResult(
        algorithm="adaptive_gauss_kronrod_correlation",
        evaluations=evaluations,
        absolute_tolerance=QUAD_EPSABS,
        relative_tolerance=QUAD_EPSREL,
        estimated_error=maximum_estimated_error,
        calculated_work=evaluations,
        maximum_work=maximum_work,
        hard_maximum_work=HARD_MAX_BAYESIAN_WORK,
        root_seed=None,
        diagnostics=("quadrature_converged", "mcmc_diagnostics_not_applicable"),
    )
    return r, correlation_prior(float(prior_shape)), posterior, evidence, computation


@dataclass(frozen=True, slots=True)
class _LinearPosterior:
    mean: np.ndarray
    covariance_scale: np.ndarray
    shape: float
    scale: float
    log_marginal: float


def _linear_posterior(design: np.ndarray, values: np.ndarray) -> _LinearPosterior:
    """Conjugate normal-inverse-gamma linear-model posterior."""

    rows, columns = design.shape
    precision = design.T @ design + 2.0 * np.eye(columns)
    covariance = np.linalg.inv(precision)
    mean = covariance @ design.T @ values
    shape = 2.0 + rows / 2.0
    scale = 1.0 + 0.5 * float(values @ values - mean @ precision @ mean)
    sign, logdet_covariance = np.linalg.slogdet(covariance)
    if sign <= 0.0 or scale <= 0.0:
        raise ValueError("Bayesian conjugate posterior is numerically invalid")
    log_marginal = (
        float(scipy_special.gammaln(shape))
        - float(scipy_special.gammaln(2.0))
        + 2.0 * log(1.0)
        - shape * log(scale)
        + 0.5 * (logdet_covariance + columns * log(2.0))
        - rows / 2.0 * log(2.0 * pi)
    )
    return _LinearPosterior(mean, covariance, shape, scale, log_marginal)


def _linear_zero_log_marginal(values: np.ndarray) -> float:
    return _fixed_zero_log_marginal(np.asarray(values, dtype=np.float64))


def validate_random_seed(seed: int | None) -> int:
    """Require the approved explicit unsigned 64-bit QMC root seed."""

    if type(seed) is not int or not 0 <= seed <= 2**64 - 1:
        raise ValueError("random_seed must be an unsigned 64-bit integer")
    return seed


def _typed_seed_token(value: ScalarIdentity) -> str:
    if isinstance(value, bool):
        return f"bool:{str(value).lower()}"
    if isinstance(value, int):
        return f"int:{value}"
    if isinstance(value, float) and isfinite(value):
        return f"float:{value.hex()}"
    if isinstance(value, str) and value:
        return f"str:{value}"
    raise TypeError("Bayesian seed identities must be finite scalar identities")


def _seed_scope(
    analysis: str, identities: tuple[tuple[str, ScalarIdentity], ...]
) -> str:
    if not analysis or any(not label for label, _value in identities):
        raise ValueError("Bayesian seed scope must have complete labels")
    tokens = [f"analysis:{analysis}"]
    tokens.extend(f"{label}:{_typed_seed_token(value)}" for label, value in identities)
    return "".join(f"{len(token)}:{token}" for token in tokens)


def bayesian_child_seed(
    root_seed: int,
    analysis: str,
    identities: tuple[tuple[str, ScalarIdentity], ...],
) -> int:
    """Derive one deterministic seed from an unambiguous typed identity scope."""

    seed = validate_random_seed(root_seed)
    encoded = _seed_scope(analysis, identities)
    payload = f"plotsalot-m6b-seed-v1\0{seed}\0{encoded}".encode()
    return int.from_bytes(sha256(payload).digest()[:8], "big")


def _child_seed(root_seed: int, identity: str, replicate: int) -> int:
    return bayesian_child_seed(
        root_seed,
        "rqmc_replicate",
        (("posterior_scope", identity), ("replicate", replicate)),
    )


def _qmc_linear_draws(
    posterior: _LinearPosterior, *, root_seed: int, identity: str
) -> tuple[np.ndarray, tuple[int, ...]]:
    dimensions = posterior.mean.size + 1
    cholesky = np.linalg.cholesky(posterior.covariance_scale)
    draws: list[np.ndarray] = []
    seeds: list[int] = []
    for replicate in range(8):
        child = _child_seed(root_seed, identity, replicate)
        seeds.append(child)
        engine = scipy_qmc.Sobol(dimensions, scramble=True, seed=child)
        uniform = np.clip(  # pyright: ignore[reportUnknownMemberType]
            engine.random_base2(12), 2.0**-53, 1.0 - 2.0**-53
        )
        beta = _linear_draws_from_uniform(posterior, uniform, cholesky)
        if not bool(np.isfinite(beta).all()):
            raise ValueError("scrambled Sobol posterior produced non-finite draws")
        draws.append(beta)
    return np.stack(draws), tuple(seeds)  # pyright: ignore[reportUnknownMemberType]


def _linear_draws_from_uniform(
    posterior: _LinearPosterior,
    uniform: np.ndarray,
    cholesky: np.ndarray | None = None,
) -> np.ndarray:
    factor = (
        np.linalg.cholesky(posterior.covariance_scale) if cholesky is None else cholesky
    )
    inverse_gamma = posterior.scale / np.asarray(
        scipy_special.gammainccinv(posterior.shape, uniform[:, 0]),
        dtype=np.float64,
    )
    normal = np.asarray(scipy_special.ndtri(uniform[:, 1:]), dtype=np.float64)
    return posterior.mean + (normal @ factor.T) * np.sqrt(inverse_gamma[:, None])


def _draw_summary(
    draws: np.ndarray, *, target: str, null_value: float, level: float
) -> BayesianPosteriorSummary:
    flat = np.asarray(draws, dtype=np.float64).reshape(-1)
    tail = (1.0 - level) / 2.0
    low, median, high = np.quantile(  # pyright: ignore[reportUnknownMemberType]
        flat, (tail, 0.5, 1.0 - tail)
    )
    below = float(np.mean(flat < null_value))
    above = float(np.mean(flat > null_value))
    at = max(0.0, 1.0 - below - above)
    return BayesianPosteriorSummary(
        target=target,
        median=float(median),
        null_value=float(null_value),
        interval=IntervalResult(
            target=target,
            method="bayesian_equal_tail",
            level=level,
            low=float(low),
            high=float(high),
        ),
        probability_above_null=above,
        probability_below_null=below,
        probability_at_null=at,
    )


def _qmc_target_diagnostic(
    draws: np.ndarray,
    *,
    target_identity: str,
    null_value: float,
    level: float,
) -> BayesianQmcTargetDiagnostic:
    if draws.shape != (8, 4096):
        raise ValueError("QMC target draws must have shape (8, 4096)")
    tail = (1.0 - level) / 2.0
    replicate_medians = tuple(float(value) for value in np.median(draws, axis=1))
    replicate_probabilities = tuple(
        float(value) for value in np.mean(draws > null_value, axis=1)
    )
    full = np.asarray(
        np.quantile(  # pyright: ignore[reportUnknownMemberType]
            draws.reshape(-1), (tail, 1.0 - tail)
        ),
        dtype=np.float64,
    )
    nested = np.asarray(
        np.quantile(  # pyright: ignore[reportUnknownMemberType]
            draws[:, :2048].reshape(-1), (tail, 1.0 - tail)
        ),
        dtype=np.float64,
    )
    width = max(float(full[1] - full[0]), 1e-15)
    median_relative_se = float(np.std(replicate_medians, ddof=1) / sqrt(8.0) / width)
    probability_absolute_se = float(np.std(replicate_probabilities, ddof=1) / sqrt(8.0))
    endpoint_shift = float(np.max(np.abs(nested - full)) / width)
    return BayesianQmcTargetDiagnostic(
        target_identity=target_identity,
        replicate_medians=replicate_medians,
        replicate_probabilities_above=replicate_probabilities,
        full_interval_low=float(full[0]),
        full_interval_high=float(full[1]),
        nested_interval_low=float(nested[0]),
        nested_interval_high=float(nested[1]),
        median_relative_se=median_relative_se,
        probability_absolute_se=probability_absolute_se,
        endpoint_relative_shift=endpoint_shift,
    )


def _linear_evidence(
    values: np.ndarray,
    design: np.ndarray,
    *,
    raw_values: np.ndarray,
    prior_location: float,
    prior_scale: float,
    null_hypothesis: str,
    alternative_hypothesis: str,
    sampling_plan: str,
    null_design: np.ndarray | None = None,
) -> BayesianEvidenceResult:
    posterior = _linear_posterior(design, values)
    null_log = (
        _linear_zero_log_marginal(values)
        if null_design is None
        else _linear_posterior(null_design, values).log_marginal
    )
    log_bf = posterior.log_marginal - null_log
    sensitivity: list[BayesFactorSensitivity] = []
    for label, scale in (("half", prior_scale * 0.5), ("double", prior_scale * 2.0)):
        standardized = np.asarray(
            (raw_values - prior_location) / scale, dtype=np.float64
        )
        candidate = _linear_posterior(design, standardized).log_marginal
        candidate -= (
            _linear_zero_log_marginal(standardized)
            if null_design is None
            else _linear_posterior(null_design, standardized).log_marginal
        )
        sensitivity.append(BayesFactorSensitivity(label, scale, float(candidate)))
    return BayesianEvidenceResult(
        null_hypothesis=null_hypothesis,
        alternative_hypothesis=alternative_hypothesis,
        sampling_plan=sampling_plan,
        log_bf10=float(log_bf),
        display=bounded_bf10_text(float(log_bf)),
        prior_model_odds=1.0,
        sensitivity=tuple(sensitivity),
    )


def independent_comparison_posterior(
    values: tuple[FloatArray, ...],
    levels: tuple[ScalarIdentity, ...],
    *,
    prior_location: float,
    prior_scale: float,
    credible_level: float,
    random_seed: int | None,
    maximum_work: int = DEFAULT_MAX_BAYESIAN_WORK,
) -> tuple[
    BayesianPriorResult,
    tuple[BayesianComparisonLevelResult, ...],
    BayesianEvidenceResult,
    tuple[BayesianPairwiseComparisonResult, ...],
    BayesianComputationResult,
]:
    """Approved homoscedastic cell-means Bayesian comparison."""

    level = validate_credible_level(credible_level)
    scale = validate_prior_scale(prior_scale)
    seed = validate_random_seed(random_seed)
    if not isfinite(prior_location):
        raise ValueError("prior_location must be finite")
    if len(values) != len(levels) or any(item.size < 3 for item in values):
        raise ValueError("Bayesian comparisons require at least three rows per level")
    raw = np.concatenate(values)  # pyright: ignore[reportUnknownMemberType]
    standardized = np.asarray((raw - prior_location) / scale, dtype=np.float64)
    design = np.zeros((raw.size, len(values)), dtype=np.float64)
    start = 0
    for index, item in enumerate(values):
        design[start : start + item.size, index] = 1.0
        start += item.size
    work = 8 * 4096 * (len(values) + 1)
    validate_work_limit(maximum_work, work)
    posterior = _linear_posterior(design, standardized)
    qmc_identity = _seed_scope(
        "independent_cell_means",
        tuple(("level", value) for value in levels),
    )
    beta, child_seeds = _qmc_linear_draws(
        posterior, root_seed=seed, identity=qmc_identity
    )
    raw_beta = prior_location + scale * beta
    level_results = tuple(
        BayesianComparisonLevelResult(
            identity,
            int(item.size),
            _draw_summary(
                raw_beta[:, :, index],
                target="population_mean",
                null_value=prior_location,
                level=level,
            ),
        )
        for index, (identity, item) in enumerate(zip(levels, values, strict=True))
    )
    omnibus = _linear_evidence(
        standardized,
        design,
        raw_values=raw,
        prior_location=prior_location,
        prior_scale=scale,
        null_hypothesis="all_population_means_equal_prior_location",
        alternative_hypothesis="cell_means_have_approved_nig_prior",
        sampling_plan="independent_homoscedastic_normal_fixed_group_sizes",
        null_design=np.ones((raw.size, 1), dtype=np.float64),
    )
    pairwise: list[BayesianPairwiseComparisonResult] = []
    for left in range(len(values)):
        for right in range(left + 1, len(values)):
            difference = scale * (beta[:, :, left] - beta[:, :, right])
            pair_raw = np.concatenate(  # pyright: ignore[reportUnknownMemberType]
                (values[left], values[right])
            )
            pair_z = (pair_raw - prior_location) / scale
            pair_design = np.zeros((pair_raw.size, 2), dtype=np.float64)
            pair_design[: values[left].size, 0] = 1.0
            pair_design[values[left].size :, 1] = 1.0
            evidence = _linear_evidence(
                pair_z,
                pair_design,
                raw_values=pair_raw,
                prior_location=prior_location,
                prior_scale=scale,
                null_hypothesis="selected_population_means_are_equal",
                alternative_hypothesis="selected_cell_means_have_approved_nig_prior",
                sampling_plan="independent_homoscedastic_normal_fixed_group_sizes",
                null_design=np.ones((pair_raw.size, 1), dtype=np.float64),
            )
            pairwise.append(
                BayesianPairwiseComparisonResult(
                    levels[left],
                    levels[right],
                    _draw_summary(
                        difference,
                        target="population_mean_difference",
                        null_value=0.0,
                        level=level,
                    ),
                    evidence,
                )
            )
    qmc_targets = [
        _qmc_target_diagnostic(
            raw_beta[:, :, index],
            target_identity=_seed_scope("posterior_target", (("level", identity),)),
            null_value=prior_location,
            level=level,
        )
        for index, identity in enumerate(levels)
    ]
    qmc_targets.extend(
        _qmc_target_diagnostic(
            scale * (beta[:, :, left] - beta[:, :, right]),
            target_identity=_seed_scope(
                "posterior_target",
                (("contrast_left", levels[left]), ("contrast_right", levels[right])),
            ),
            null_value=0.0,
            level=level,
        )
        for left in range(len(values))
        for right in range(left + 1, len(values))
    )
    relative_se = max(item.median_relative_se for item in qmc_targets)
    nested = max(item.endpoint_relative_shift for item in qmc_targets)
    computation = BayesianComputationResult(
        algorithm="scrambled_sobol_conjugate_posterior",
        evaluations=8 * 4096,
        absolute_tolerance=None,
        relative_tolerance=None,
        estimated_error=None,
        calculated_work=work,
        maximum_work=maximum_work,
        hard_maximum_work=HARD_MAX_BAYESIAN_WORK,
        root_seed=seed,
        diagnostics=("eight_scrambles_complete", "nested_2048_4096_check_complete"),
        qmc_dimension=len(values) + 1,
        qmc_replicates=8,
        qmc_points_per_replicate=4096,
        child_seeds=child_seeds,
        replicate_max_relative_se=relative_se,
        nested_max_relative_shift=nested,
        qmc_targets=tuple(qmc_targets),
    )
    return (
        continuous_prior(prior_location, scale),
        level_results,
        omnibus,
        tuple(pairwise),
        computation,
    )


def repeated_comparison_posterior(
    values: np.ndarray,
    levels: tuple[ScalarIdentity, ...],
    *,
    prior_location: float,
    prior_scale: float,
    credible_level: float,
    random_seed: int | None,
    maximum_work: int = DEFAULT_MAX_BAYESIAN_WORK,
) -> tuple[
    BayesianPriorResult,
    tuple[BayesianComparisonLevelResult, ...],
    BayesianEvidenceResult,
    tuple[BayesianPairwiseComparisonResult, ...],
    BayesianComputationResult,
]:
    """Approved complete-block Helmert Bayesian comparison."""

    level = validate_credible_level(credible_level)
    scale = validate_prior_scale(prior_scale)
    seed = validate_random_seed(random_seed)
    if not isfinite(prior_location) or values.shape[0] < 3:
        raise ValueError("Bayesian repeated comparison requires three complete blocks")
    subjects, conditions = values.shape
    standardized = np.asarray((values - prior_location) / scale, dtype=np.float64)
    helmert = np.zeros((conditions, conditions - 1), dtype=np.float64)
    for column in range(conditions - 1):
        denominator = sqrt((column + 1) * (column + 2))
        helmert[: column + 1, column] = 1.0 / denominator
        helmert[column + 1, column] = -(column + 1) / denominator
    grand = np.mean(standardized, axis=1)
    contrasts = standardized @ helmert
    contrast_values = contrasts.reshape(-1)
    contrast_design = np.tile(  # pyright: ignore[reportUnknownMemberType]
        np.eye(conditions - 1), (subjects, 1)
    )
    grand_design = np.ones((subjects, 1), dtype=np.float64)
    work = 8 * 4096 * (conditions + 2)
    validate_work_limit(maximum_work, work)
    grand_post = _linear_posterior(grand_design, grand)
    contrast_post = _linear_posterior(contrast_design, contrast_values)
    grand_replicates: list[np.ndarray] = []
    contrast_replicates: list[np.ndarray] = []
    repeated_seeds: list[int] = []
    qmc_identity = _seed_scope(
        "complete_block_joint",
        tuple(("condition", value) for value in levels),
    )
    for replicate in range(8):
        child = _child_seed(seed, qmc_identity, replicate)
        repeated_seeds.append(child)
        engine = scipy_qmc.Sobol(conditions + 2, scramble=True, seed=child)
        uniform = np.clip(  # pyright: ignore[reportUnknownMemberType]
            engine.random_base2(12), 2.0**-53, 1.0 - 2.0**-53
        )
        grand_replicates.append(_linear_draws_from_uniform(grand_post, uniform[:, :2]))
        contrast_replicates.append(
            _linear_draws_from_uniform(contrast_post, uniform[:, 2:])
        )
    grand_draws = np.stack(  # pyright: ignore[reportUnknownMemberType]
        grand_replicates
    )
    contrast_draws = np.stack(  # pyright: ignore[reportUnknownMemberType]
        contrast_replicates
    )
    condition_z = grand_draws[:, :, 0, None] + contrast_draws @ helmert.T
    condition_raw = prior_location + scale * condition_z
    level_results = tuple(
        BayesianComparisonLevelResult(
            identity,
            subjects,
            _draw_summary(
                condition_raw[:, :, index],
                target="population_mean",
                null_value=prior_location,
                level=level,
            ),
        )
        for index, identity in enumerate(levels)
    )
    log_bf = contrast_post.log_marginal - _linear_zero_log_marginal(contrast_values)
    sensitivity: list[BayesFactorSensitivity] = []
    for label, candidate_scale in (("half", scale * 0.5), ("double", scale * 2.0)):
        candidate_z = (values - prior_location) / candidate_scale
        candidate_contrasts = (candidate_z @ helmert).reshape(-1)
        candidate_log = _linear_posterior(
            contrast_design, candidate_contrasts
        ).log_marginal - _linear_zero_log_marginal(candidate_contrasts)
        sensitivity.append(
            BayesFactorSensitivity(label, candidate_scale, float(candidate_log))
        )
    omnibus = BayesianEvidenceResult(
        null_hypothesis="all_complete_block_condition_means_are_equal",
        alternative_hypothesis="helmert_condition_effects_have_approved_nig_prior",
        sampling_plan="complete_block_compound_symmetry_fixed_subjects",
        log_bf10=float(log_bf),
        display=bounded_bf10_text(float(log_bf)),
        prior_model_odds=1.0,
        sensitivity=tuple(sensitivity),
    )
    pairwise: list[BayesianPairwiseComparisonResult] = []
    for left in range(conditions):
        for right in range(left + 1, conditions):
            level_difference = np.zeros(conditions, dtype=np.float64)
            level_difference[left] = 1.0
            level_difference[right] = -1.0
            contrast_vector = helmert.T @ level_difference
            posterior_location = float(contrast_vector @ contrast_post.mean)
            posterior_variance_scale = float(
                contrast_vector @ contrast_post.covariance_scale @ contrast_vector
            )
            posterior_scale = sqrt(
                contrast_post.scale / contrast_post.shape * posterior_variance_scale
            )
            prior_variance_scale = float(contrast_vector @ contrast_vector) / 2.0
            prior_t_scale = sqrt(1.0 / 2.0 * prior_variance_scale)
            pair_log_bf = float(
                scipy_stats.t.logpdf(0.0, 4.0, loc=0.0, scale=prior_t_scale)
                - scipy_stats.t.logpdf(
                    0.0,
                    2.0 * contrast_post.shape,
                    loc=posterior_location,
                    scale=posterior_scale,
                )
            )
            pair_sensitivity: list[BayesFactorSensitivity] = []
            for label, candidate_scale in (
                ("half", scale * 0.5),
                ("double", scale * 2.0),
            ):
                candidate_values = (values - prior_location) / candidate_scale
                candidate_contrasts = (candidate_values @ helmert).reshape(-1)
                candidate_post = _linear_posterior(contrast_design, candidate_contrasts)
                candidate_location = float(contrast_vector @ candidate_post.mean)
                candidate_variance_scale = float(
                    contrast_vector @ candidate_post.covariance_scale @ contrast_vector
                )
                candidate_t_scale = sqrt(
                    candidate_post.scale
                    / candidate_post.shape
                    * candidate_variance_scale
                )
                candidate_log_bf = float(
                    scipy_stats.t.logpdf(0.0, 4.0, loc=0.0, scale=prior_t_scale)
                    - scipy_stats.t.logpdf(
                        0.0,
                        2.0 * candidate_post.shape,
                        loc=candidate_location,
                        scale=candidate_t_scale,
                    )
                )
                pair_sensitivity.append(
                    BayesFactorSensitivity(label, candidate_scale, candidate_log_bf)
                )
            evidence = BayesianEvidenceResult(
                null_hypothesis="selected_complete_block_condition_means_are_equal",
                alternative_hypothesis="selected_helmert_contrast_is_nonzero",
                sampling_plan="complete_block_compound_symmetry_fixed_subjects",
                log_bf10=pair_log_bf,
                display=bounded_bf10_text(pair_log_bf),
                prior_model_odds=1.0,
                sensitivity=tuple(pair_sensitivity),
            )
            pairwise.append(
                BayesianPairwiseComparisonResult(
                    levels[left],
                    levels[right],
                    _draw_summary(
                        condition_raw[:, :, left] - condition_raw[:, :, right],
                        target="population_mean_difference",
                        null_value=0.0,
                        level=level,
                    ),
                    evidence,
                )
            )
    qmc_targets = [
        _qmc_target_diagnostic(
            condition_raw[:, :, index],
            target_identity=_seed_scope("posterior_target", (("condition", identity),)),
            null_value=prior_location,
            level=level,
        )
        for index, identity in enumerate(levels)
    ]
    qmc_targets.extend(
        _qmc_target_diagnostic(
            condition_raw[:, :, left] - condition_raw[:, :, right],
            target_identity=_seed_scope(
                "posterior_target",
                (("contrast_left", levels[left]), ("contrast_right", levels[right])),
            ),
            null_value=0.0,
            level=level,
        )
        for left in range(conditions)
        for right in range(left + 1, conditions)
    )
    relative_se = max(item.median_relative_se for item in qmc_targets)
    nested = max(item.endpoint_relative_shift for item in qmc_targets)
    computation = BayesianComputationResult(
        algorithm="scrambled_sobol_conjugate_posterior",
        evaluations=8 * 4096,
        absolute_tolerance=None,
        relative_tolerance=None,
        estimated_error=None,
        calculated_work=work,
        maximum_work=maximum_work,
        hard_maximum_work=HARD_MAX_BAYESIAN_WORK,
        root_seed=seed,
        diagnostics=("eight_joint_scrambles_complete", "helmert_basis_verified"),
        qmc_dimension=conditions + 2,
        qmc_replicates=8,
        qmc_points_per_replicate=4096,
        child_seeds=tuple(repeated_seeds),
        replicate_max_relative_se=relative_se,
        nested_max_relative_shift=nested,
        qmc_targets=tuple(qmc_targets),
    )
    return (
        continuous_prior(prior_location, scale),
        level_results,
        omnibus,
        tuple(pairwise),
        computation,
    )


def dirichlet_prior(concentration: float) -> BayesianPriorResult:
    """Create the approved exchangeable per-cell Dirichlet prior record."""

    if not isfinite(concentration) or concentration <= 0.0:
        raise ValueError("prior_cell_concentration must be finite and positive")
    return BayesianPriorResult(
        family="exchangeable_dirichlet_multinomial",
        proper=True,
        parameters=(
            PriorParameter(
                "concentration_per_cell", float(concentration), "dimensionless"
            ),
        ),
    )


def _dirichlet_log_integral(counts: np.ndarray, alpha: np.ndarray) -> float:
    total_alpha = float(np.sum(alpha))
    total_counts = float(np.sum(counts))
    value = float(scipy_special.gammaln(total_alpha))
    value -= float(scipy_special.gammaln(total_alpha + total_counts))
    for count, prior in zip(counts.flat, alpha.flat, strict=True):
        value += float(scipy_special.gammaln(float(prior + count)))
        value -= float(scipy_special.gammaln(float(prior)))
    return value


def _categorical_evidence(
    observed: np.ndarray,
    *,
    concentration: float,
    ratio: np.ndarray | None,
) -> float:
    if ratio is not None:
        counts = observed.reshape(-1)
        alpha = concentration * counts.size * ratio
        alternative = _dirichlet_log_integral(counts, alpha)
        null = float(np.sum(counts * np.log(ratio)))
        return alternative - null
    rows, columns = observed.shape
    alpha = np.full(columns, concentration, dtype=np.float64)
    alternative = sum(
        _dirichlet_log_integral(observed[row], alpha) for row in range(rows)
    )
    null = _dirichlet_log_integral(np.sum(observed, axis=0), alpha)
    return float(alternative - null)


def one_way_categorical_posterior(
    observed: np.ndarray,
    ratio: np.ndarray,
    *,
    prior_cell_concentration: float,
    credible_level: float,
    maximum_work: int = DEFAULT_MAX_BAYESIAN_WORK,
) -> tuple[
    BayesianPriorResult,
    tuple[BayesianPosteriorSummary, ...],
    BayesianEvidenceResult,
    BayesianComputationResult,
]:
    """Approved fixed-total Dirichlet-multinomial analysis."""

    level = validate_credible_level(credible_level)
    concentration = float(prior_cell_concentration)
    prior = dirichlet_prior(concentration)
    counts = np.asarray(observed, dtype=np.float64).reshape(-1)
    if counts.size < 2 or float(np.sum(counts)) < 1.0:
        raise ValueError("Bayesian one-way categorical analysis requires counts")
    validate_work_limit(maximum_work, int(counts.size * 3))
    alpha = concentration * counts.size * ratio
    posterior_alpha = alpha + counts
    total = float(np.sum(posterior_alpha))
    tail = (1.0 - level) / 2.0
    summaries: list[BayesianPosteriorSummary] = []
    for index, candidate in enumerate(posterior_alpha):
        other = total - float(candidate)
        low = scipy_stats.beta.ppf(tail, float(candidate), other)
        median = scipy_stats.beta.ppf(0.5, float(candidate), other)
        high = scipy_stats.beta.ppf(1.0 - tail, float(candidate), other)
        below = scipy_stats.beta.cdf(float(ratio[index]), float(candidate), other)
        summaries.append(
            BayesianPosteriorSummary(
                target="cell_probability",
                median=float(median),
                null_value=float(ratio[index]),
                interval=IntervalResult(
                    "cell_probability",
                    "bayesian_equal_tail",
                    level,
                    float(low),
                    float(high),
                ),
                probability_above_null=1.0 - float(below),
                probability_below_null=float(below),
                probability_at_null=0.0,
            )
        )
    log_bf = _categorical_evidence(counts, concentration=concentration, ratio=ratio)
    sensitivity = tuple(
        BayesFactorSensitivity(
            label,
            candidate,
            _categorical_evidence(counts, concentration=candidate, ratio=ratio),
        )
        for label, candidate in (
            ("half", concentration * 0.5),
            ("double", concentration * 2.0),
        )
    )
    evidence = BayesianEvidenceResult(
        null_hypothesis="fixed_total_cell_probabilities_equal_declared_ratio",
        alternative_hypothesis="cell_probabilities_have_approved_dirichlet_prior",
        sampling_plan="fixed_total_multinomial",
        log_bf10=float(log_bf),
        display=bounded_bf10_text(float(log_bf)),
        prior_model_odds=1.0,
        sensitivity=sensitivity,
    )
    computation = BayesianComputationResult(
        algorithm="closed_form_dirichlet_multinomial",
        evaluations=0,
        absolute_tolerance=None,
        relative_tolerance=None,
        estimated_error=None,
        calculated_work=int(counts.size * 3),
        maximum_work=maximum_work,
        hard_maximum_work=HARD_MAX_BAYESIAN_WORK,
        root_seed=None,
        diagnostics=("closed_form_finite", "zero_cells_supported"),
    )
    return prior, tuple(summaries), evidence, computation


def independent_categorical_posterior(
    observed: np.ndarray,
    *,
    row_identities: tuple[ScalarIdentity, ...],
    column_identities: tuple[ScalarIdentity, ...],
    prior_cell_concentration: float,
    credible_level: float,
    random_seed: int | None,
    maximum_work: int = DEFAULT_MAX_BAYESIAN_WORK,
) -> tuple[
    BayesianPriorResult,
    tuple[BayesianPosteriorSummary, ...],
    tuple[tuple[int, int, int, BayesianPosteriorSummary], ...],
    BayesianEvidenceResult,
    BayesianPosteriorSummary,
    BayesianComputationResult,
]:
    """Approved fixed-row Dirichlet-multinomial analysis."""

    level = validate_credible_level(credible_level)
    concentration = float(prior_cell_concentration)
    prior = dirichlet_prior(concentration)
    seed = validate_random_seed(random_seed)
    rows, columns = observed.shape
    if len(row_identities) != rows or len(column_identities) != columns:
        raise ValueError("Bayesian categorical identities do not match the table")
    if rows < 2 or columns < 2 or bool((observed.sum(axis=1) == 0).any()):
        raise ValueError("Bayesian fixed-row analysis requires non-empty row margins")
    work = 8 * 4096 * rows * columns
    validate_work_limit(maximum_work, work)
    draws: list[np.ndarray] = []
    seeds: list[int] = []
    posterior_alpha = observed.astype(np.float64) + concentration
    identity = _seed_scope(
        "fixed_row_dirichlet",
        (
            *(("row", value) for value in row_identities),
            *(("column", value) for value in column_identities),
        ),
    )
    for replicate in range(8):
        child = _child_seed(seed, identity, replicate)
        seeds.append(child)
        engine = scipy_qmc.Sobol(rows * columns, scramble=True, seed=child)
        uniform = np.clip(  # pyright: ignore[reportUnknownMemberType]
            engine.random_base2(12), 2.0**-53, 1.0 - 2.0**-53
        ).reshape(4096, rows, columns)
        gamma = np.empty_like(uniform)
        for row in range(rows):
            for column in range(columns):
                gamma[:, row, column] = np.asarray(
                    scipy_special.gammainccinv(
                        float(posterior_alpha[row, column]),
                        1.0 - uniform[:, row, column],
                    ),
                    dtype=np.float64,
                )
        draws.append(gamma / np.sum(gamma, axis=2, keepdims=True))
    posterior_draws = np.stack(  # pyright: ignore[reportUnknownMemberType]
        draws
    )
    uniform_null = 1.0 / columns
    summaries = tuple(
        _draw_summary(
            posterior_draws[:, :, row, column],
            target="cell_probability",
            null_value=uniform_null,
            level=level,
        )
        for row in range(rows)
        for column in range(columns)
    )
    contrasts = tuple(
        (
            left,
            right,
            column,
            _draw_summary(
                posterior_draws[:, :, left, column]
                - posterior_draws[:, :, right, column],
                target="cell_probability_difference",
                null_value=0.0,
                level=level,
            ),
        )
        for left in range(rows)
        for right in range(left + 1, rows)
        for column in range(columns)
    )
    row_weights = observed.sum(axis=1) / float(observed.sum())
    pooled = np.sum(posterior_draws * row_weights[None, None, :, None], axis=2)
    deviations = posterior_draws - pooled[:, :, None, :]
    chi_component = np.sum(
        row_weights[None, None, :, None]
        * deviations**2
        / np.maximum(pooled[:, :, None, :], 1e-300),
        axis=(2, 3),
    )
    cramers = np.sqrt(chi_component / min(rows - 1, columns - 1))
    effect = _draw_summary(
        cramers,
        target="cramers_v",
        null_value=0.0,
        level=level,
    )
    log_bf = _categorical_evidence(observed, concentration=concentration, ratio=None)
    sensitivity = tuple(
        BayesFactorSensitivity(
            label,
            candidate,
            _categorical_evidence(observed, concentration=candidate, ratio=None),
        )
        for label, candidate in (
            ("half", concentration * 0.5),
            ("double", concentration * 2.0),
        )
    )
    evidence = BayesianEvidenceResult(
        null_hypothesis="all_fixed_rows_share_one_category_probability_vector",
        alternative_hypothesis="fixed_rows_have_independent_dirichlet_vectors",
        sampling_plan="fixed_row_totals_product_multinomial",
        log_bf10=float(log_bf),
        display=bounded_bf10_text(float(log_bf)),
        prior_model_odds=1.0,
        sensitivity=sensitivity,
    )
    qmc_targets = [
        _qmc_target_diagnostic(
            posterior_draws[:, :, row, column],
            target_identity=_seed_scope(
                "posterior_target",
                (
                    ("row", row_identities[row]),
                    ("column", column_identities[column]),
                ),
            ),
            null_value=uniform_null,
            level=level,
        )
        for row in range(rows)
        for column in range(columns)
    ]
    qmc_targets.extend(
        _qmc_target_diagnostic(
            posterior_draws[:, :, left, column] - posterior_draws[:, :, right, column],
            target_identity=_seed_scope(
                "posterior_target",
                (
                    ("contrast_left", row_identities[left]),
                    ("contrast_right", row_identities[right]),
                    ("column", column_identities[column]),
                ),
            ),
            null_value=0.0,
            level=level,
        )
        for left in range(rows)
        for right in range(left + 1, rows)
        for column in range(columns)
    )
    qmc_targets.append(
        _qmc_target_diagnostic(
            cramers,
            target_identity="effect:cramers_v",
            null_value=0.0,
            level=level,
        )
    )
    relative_se = max(item.median_relative_se for item in qmc_targets)
    nested = max(item.endpoint_relative_shift for item in qmc_targets)
    computation = BayesianComputationResult(
        algorithm="scrambled_sobol_conjugate_posterior",
        evaluations=8 * 4096,
        absolute_tolerance=None,
        relative_tolerance=None,
        estimated_error=None,
        calculated_work=work,
        maximum_work=maximum_work,
        hard_maximum_work=HARD_MAX_BAYESIAN_WORK,
        root_seed=seed,
        diagnostics=("eight_scrambles_complete", "zero_cells_supported"),
        qmc_dimension=rows * columns,
        qmc_replicates=8,
        qmc_points_per_replicate=4096,
        child_seeds=tuple(seeds),
        replicate_max_relative_se=relative_se,
        nested_max_relative_shift=nested,
        qmc_targets=tuple(qmc_targets),
    )
    return prior, summaries, contrasts, evidence, effect, computation
