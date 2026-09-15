"""Generate locked M6C robust-coverage, contamination, and Bayesian SBC evidence."""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from math import exp, log, pi, sqrt
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
from scipy.integrate import quad
from scipy.optimize import brentq, minimize_scalar
from scipy.special import ndtr
from scipy.stats import norm

from plotsalot import analyze_ggcoefstats

ROOT = Path(__file__).resolve().parents[1]
FIRST_OUTPUT = ROOT / "docs" / "evidence" / "m6c-pass2-calibration.json"
DEFAULT_OUTPUT = ROOT / "docs" / "evidence" / "m6c-pass2-calibration-confirmation.json"
CASES = 2_000
CONF_LEVEL = 0.95
WILSON_LEVEL = 0.99
FIRST_ROBUST_SEED = 2026091511
FIRST_CONTAMINATION_SEED = 2026091512
FIRST_BAYESIAN_SEED = 2026091513
CONFIRMATION_ROBUST_SEED = 2026091520
CONFIRMATION_CONTAMINATION_SEED = 2026091521
CONFIRMATION_BAYESIAN_SEED = 2026091522
BAYESIAN_K = 5
PRIOR_MEAN_SCALE = 1.0
PRIOR_TAU_SCALE = 0.5
ROBUST_SCENARIOS = (
    (10, 0.0, 0.0),
    (20, 0.0, 0.2),
    (50, 0.3, 0.0),
    (500, 0.3, 0.2),
)
COMMON = {
    "meta_analytic_effect": True,
    "estimand": "simulation population effect",
    "effect_scale": "mean difference",
    "effect_direction": "positive favors treatment",
    "effect_units": "simulation units",
    "stats_labels": False,
}


def _standard_errors(k: int) -> np.ndarray[Any, np.dtype[np.float64]]:
    return np.linspace(0.15, 0.35, k, dtype=np.float64)


def _data_seed(root: int, scenario: int, case: int) -> np.random.SeedSequence:
    return np.random.SeedSequence((root, scenario, case))


def _independent_m5_reml_mean(
    estimates: np.ndarray[Any, np.dtype[np.float64]],
    errors: np.ndarray[Any, np.dtype[np.float64]],
    null: float,
) -> float:
    scale = max(float(np.max(np.abs(estimates - null))), float(np.max(errors)))
    y = (estimates - null) / scale
    variances = (errors / scale) ** 2

    def score(tau_squared: float) -> float:
        weights = 1.0 / (variances + tau_squared)
        mean = float(np.sum(weights * y) / np.sum(weights))
        residuals = y - mean
        return float(
            0.5
            * (
                np.sum(weights * weights * residuals * residuals)
                - np.sum(weights)
                + np.sum(weights * weights) / np.sum(weights)
            )
        )

    if score(0.0) <= 0.0:
        tau_squared = 0.0
    else:
        upper = max(1.0, float(np.var(y, ddof=1)), float(np.max(variances)))
        while score(upper) >= 0.0:
            upper *= 2.0
        root = brentq(
            score,
            0.0,
            upper,
            xtol=np.finfo(np.float64).tiny,
            rtol=4.0 * np.finfo(np.float64).eps,
            maxiter=100,
        )
        tau_squared = float(root) * scale * scale
    weights = 1.0 / (errors * errors + tau_squared)
    return float(np.sum(weights * estimates) / np.sum(weights))


def _robust_case(
    task: tuple[int, int, int, float, float, bool, int, int],
) -> tuple[bool, float, float]:
    scenario, case, k, mu, tau, contaminate, robust_seed, contamination_seed = task
    root = contamination_seed if contaminate else robust_seed
    rng = np.random.Generator(np.random.PCG64DXSM(_data_seed(root, scenario, case)))
    errors = _standard_errors(k)
    estimates = mu + np.sqrt(errors * errors + tau * tau) * rng.standard_t(4, k)
    if contaminate:
        contaminated = max(1, int(round(0.10 * k)))
        estimates[:contaminated] += 10.0 * float(np.median(errors))
    data = pl.DataFrame(
        {
            "term": [f"study-{index + 1}" for index in range(k)],
            "estimate": estimates,
            "standard_error": errors,
        }
    )
    robust = analyze_ggcoefstats(data, type="robust", **COMMON).result
    pooled = robust.meta_analysis.pooled
    if not contaminate:
        return pooled.interval.low <= mu <= pooled.interval.high, 0.0, 0.0
    classical_estimate = _independent_m5_reml_mean(estimates, errors, mu)
    return (
        False,
        abs(pooled.estimate - mu),
        abs(classical_estimate - mu),
    )


def _wilson(successes: int, total: int) -> tuple[float, float]:
    probability = successes / total
    critical = float(norm.ppf(0.5 + WILSON_LEVEL / 2.0))
    denominator = 1.0 + critical * critical / total
    center = (probability + critical * critical / (2.0 * total)) / denominator
    half = (
        critical
        / denominator
        * sqrt(
            probability * (1.0 - probability) / total
            + critical * critical / (4.0 * total * total)
        )
    )
    return center - half, center + half


def _robust_calibration(
    cases: int,
    workers: int,
    *,
    robust_seed: int,
    contamination_seed: int,
    conservative_small_k: bool,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=workers) as executor:
        for scenario, (k, mu, tau) in enumerate(ROBUST_SCENARIOS):
            clean_tasks = (
                (
                    scenario,
                    case,
                    k,
                    mu,
                    tau,
                    False,
                    robust_seed,
                    contamination_seed,
                )
                for case in range(cases)
            )
            clean = list(executor.map(_robust_case, clean_tasks, chunksize=10))
            covered = sum(int(item[0]) for item in clean)
            wilson_low, wilson_high = _wilson(covered, cases)
            contaminated_tasks = (
                (
                    scenario,
                    case,
                    k,
                    mu,
                    tau,
                    True,
                    robust_seed,
                    contamination_seed,
                )
                for case in range(cases)
            )
            contaminated = list(
                executor.map(_robust_case, contaminated_tasks, chunksize=10)
            )
            robust_errors = np.asarray([item[1] for item in contaminated])
            classical_errors = np.asarray([item[2] for item in contaminated])
            robust_median = float(np.median(robust_errors))
            classical_median = float(np.median(classical_errors))
            conservative_rule = conservative_small_k and k < 20
            coverage_passes = (
                wilson_high >= CONF_LEVEL
                if conservative_rule
                else wilson_low <= CONF_LEVEL <= wilson_high
            )
            results.append(
                {
                    "k": k,
                    "mu": mu,
                    "tau": tau,
                    "cases": cases,
                    "covered": covered,
                    "coverage": covered / cases,
                    "wilson_99_low": wilson_low,
                    "wilson_99_high": wilson_high,
                    "wilson_contains_0_95": wilson_low <= 0.95 <= wilson_high,
                    "coverage_acceptance_rule": (
                        "wilson_99_upper_at_least_0.95_conservative_allowed"
                        if conservative_rule
                        else "wilson_99_contains_0.95"
                    ),
                    "passes_approved_coverage_rule": coverage_passes,
                    "contamination_fraction": 0.10,
                    "contamination_displacement_in_median_se": 10.0,
                    "robust_median_absolute_error": robust_median,
                    "m5_reml_median_absolute_error": classical_median,
                    "robust_not_worse_under_contamination": (
                        robust_median <= classical_median
                    ),
                }
            )
    return results


def _bayesian_rank(task: tuple[int, int]) -> tuple[float, float]:
    case, bayesian_seed = task
    rng = np.random.Generator(np.random.PCG64DXSM(_data_seed(bayesian_seed, 0, case)))
    mu = float(rng.normal(0.0, PRIOR_MEAN_SCALE))
    tau = abs(float(rng.normal(0.0, PRIOR_TAU_SCALE)))
    errors = _standard_errors(BAYESIAN_K)
    theta = rng.normal(mu, tau, BAYESIAN_K)
    y = rng.normal(theta, errors)
    variances = errors * errors

    def log_kernel(x: float) -> float:
        if x < 0.0 or x >= 1.0:
            return -float("inf")
        candidate_tau = PRIOR_TAU_SCALE * x / (1.0 - x)
        d = variances + candidate_tau * candidate_tau
        precision = 1.0 / (PRIOR_MEAN_SCALE**2) + float(np.sum(1.0 / d))
        b = float(np.sum(y / d))
        c = float(np.sum(y * y / d))
        base = -0.5 * (BAYESIAN_K * log(2.0 * pi) + float(np.sum(np.log(d))))
        log_likelihood = (
            base
            - log(PRIOR_MEAN_SCALE)
            - 0.5 * log(precision)
            - 0.5 * (c - b * b / precision)
        )
        log_prior_jacobian = (
            0.5 * log(2.0 / pi)
            - 0.5 * (candidate_tau / PRIOR_TAU_SCALE) ** 2
            - 2.0 * log(1.0 - x)
        )
        return log_likelihood + log_prior_jacobian

    optimized = minimize_scalar(
        lambda x: -log_kernel(float(x)),
        bounds=(0.0, 1.0 - 1e-12),
        method="bounded",
        options={"xatol": 1e-11, "maxiter": 500},
    )
    peak = max(-float(optimized.fun), log_kernel(0.0))

    def weight(x: float) -> float:
        return exp(log_kernel(x) - peak)

    normalizer = quad(weight, 0.0, 1.0, epsabs=1e-10, epsrel=1e-8, limit=200)[0]
    tau_x = tau / (PRIOR_TAU_SCALE + tau)
    tau_rank = (
        quad(weight, 0.0, tau_x, epsabs=1e-10, epsrel=1e-8, limit=200)[0] / normalizer
    )

    def mu_integrand(x: float) -> float:
        candidate_tau = PRIOR_TAU_SCALE * x / (1.0 - x)
        d = variances + candidate_tau * candidate_tau
        precision = 1.0 / (PRIOR_MEAN_SCALE**2) + float(np.sum(1.0 / d))
        conditional_variance = 1.0 / precision
        conditional_mean = conditional_variance * float(np.sum(y / d))
        probability = float(ndtr((mu - conditional_mean) / sqrt(conditional_variance)))
        return weight(x) * probability

    mu_rank = (
        quad(mu_integrand, 0.0, 1.0, epsabs=1e-10, epsrel=1e-8, limit=200)[0]
        / normalizer
    )
    return min(1.0, max(0.0, mu_rank)), min(1.0, max(0.0, tau_rank))


def _ks_uniform(values: np.ndarray[Any, np.dtype[np.float64]]) -> float:
    ordered = np.sort(values)
    total = ordered.size
    upper = np.arange(1, total + 1, dtype=np.float64) / total
    lower = np.arange(0, total, dtype=np.float64) / total
    return max(float(np.max(upper - ordered)), float(np.max(ordered - lower)))


def _bayesian_calibration(
    cases: int, workers: int, *, bayesian_seed: int
) -> dict[str, Any]:
    with ProcessPoolExecutor(max_workers=workers) as executor:
        tasks = ((case, bayesian_seed) for case in range(cases))
        ranks = list(executor.map(_bayesian_rank, tasks, chunksize=10))
    mu_ranks = np.asarray([item[0] for item in ranks])
    tau_ranks = np.asarray([item[1] for item in ranks])
    bound = sqrt(log(2.0 / 0.01) / (2.0 * cases))
    mu_distance = _ks_uniform(mu_ranks)
    tau_distance = _ks_uniform(tau_ranks)
    return {
        "k": BAYESIAN_K,
        "cases": cases,
        "prior_mean_scale": PRIOR_MEAN_SCALE,
        "prior_tau_scale": PRIOR_TAU_SCALE,
        "dkw_99_bound": bound,
        "mu_ks_distance": mu_distance,
        "tau_ks_distance": tau_distance,
        "mu_passes_dkw_bound": mu_distance <= bound,
        "tau_passes_dkw_bound": tau_distance <= bound,
    }


def run(cases: int, workers: int, *, confirmation: bool) -> dict[str, Any]:
    robust_seed = CONFIRMATION_ROBUST_SEED if confirmation else FIRST_ROBUST_SEED
    contamination_seed = (
        CONFIRMATION_CONTAMINATION_SEED if confirmation else FIRST_CONTAMINATION_SEED
    )
    bayesian_seed = CONFIRMATION_BAYESIAN_SEED if confirmation else FIRST_BAYESIAN_SEED
    robust = _robust_calibration(
        cases,
        workers,
        robust_seed=robust_seed,
        contamination_seed=contamination_seed,
        conservative_small_k=confirmation,
    )
    bayesian = _bayesian_calibration(cases, workers, bayesian_seed=bayesian_seed)
    return {
        "schema_version": 1,
        "status": "locked_validation",
        "cases_per_cell": cases,
        "bit_generator": "PCG64DXSM",
        "validation_run": "confirmation" if confirmation else "first_held_out",
        "robust_seed": robust_seed,
        "contamination_seed": contamination_seed,
        "bayesian_seed": bayesian_seed,
        "robust": robust,
        "bayesian": bayesian,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=int, default=CASES)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument(
        "--run", choices=("first-held-out", "confirmation"), default="confirmation"
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.cases < 1 or args.workers < 1:
        raise ValueError("cases and workers must be positive")
    payload = run(args.cases, args.workers, confirmation=args.run == "confirmation")
    passed = all(
        item["passes_approved_coverage_rule"]
        and item["robust_not_worse_under_contamination"]
        for item in payload["robust"]
    ) and all(
        payload["bayesian"][field]
        for field in ("mu_passes_dkw_bound", "tau_passes_dkw_bound")
    )
    payload["status"] = "locked_validation" if passed else "held_out_finding"
    output = args.output or (
        DEFAULT_OUTPUT if args.run == "confirmation" else FIRST_OUTPUT
    )
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    if not passed:
        raise RuntimeError("M6C pass-2 calibration failed")
    print(output)


if __name__ == "__main__":
    main()
