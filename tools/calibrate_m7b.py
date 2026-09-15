"""Run the locked M7B robust-meta boundary calibration experiment."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
from importlib.metadata import version
from math import isclose, isfinite, sqrt
from pathlib import Path
from statistics import NormalDist
from typing import Any, Literal, cast

import numpy as np
import polars as pl

from plotsalot import M6CMetaError, RobustMetaAnalysis, analyze_ggcoefstats

ROOT = Path(__file__).resolve().parents[1]
SMOKE_OUTPUT = ROOT / ".work" / "m7b-smoke.json"
MAPPING_OUTPUT = ROOT / "docs" / "evidence" / "m7b-robust-meta-mapping.json"
CONFIRMATION_OUTPUT = ROOT / "docs" / "evidence" / "m7b-robust-meta-confirmation.json"

PLAN_VERSION = 1
SCHEMA_VERSION = 1
CONFIDENCE_LEVEL = 0.95
WILSON_LEVEL = 0.99
SMOKE_CASES = 20
MAPPING_CASES = 2_000
CONFIRMATION_CASES = 5_000
SMOKE_SEED = 2026091530
MAPPING_SEED = 2026091531
CONFIRMATION_SEED = 2026091532
MAXIMUM_WORKERS = 16
MAXIMUM_ARTIFACT_BYTES = 5 * 1024 * 1024
DEPENDENCIES = ("matplotlib", "numpy", "polars", "scipy", "statsmodels")
TAU_VALUES = (0.0, 0.025, 0.0625, 0.125, 0.25)
PRIMARY_K = (10, 15, 20, 30, 50, 100)
COMMON: dict[str, Any] = {
    "meta_analytic_effect": True,
    "estimand": "simulation population effect",
    "effect_scale": "mean difference",
    "effect_direction": "positive favors treatment",
    "effect_units": "simulation units",
    "stats_labels": False,
}

RunKind = Literal["smoke", "mapping", "confirmation"]
GridKind = Literal["linear", "reversed_linear", "piecewise_log"]


@dataclass(frozen=True, slots=True)
class Scenario:
    """One immutable scenario in the approved M7B experiment."""

    scenario_id: str
    family: Literal["primary", "translation", "large_study", "se_shape"]
    k: int
    mu: float
    tau: float
    standard_error_grid: GridKind
    matched_primary_id: str | None


@dataclass(frozen=True, slots=True)
class CaseResult:
    """Minimal per-case state retained only until a cell is summarized."""

    covered: bool
    interval_width: float | None
    absolute_error: float | None
    signed_error: float | None
    boundary_fit: bool | None
    work_evaluations: int | None
    profile_evaluations: int | None
    failure_code: str | None


def _number_tag(value: float) -> str:
    return f"{value:.4f}".replace("-", "m").replace(".", "p")


def _primary_id(k: int, tau: float) -> str:
    return f"primary-k{k:03d}-tau-{_number_tag(tau)}-mu-0p0000-linear"


def mapping_scenarios() -> tuple[Scenario, ...]:
    """Return the immutable 30-cell primary and 8-cell audit grid."""

    primary = tuple(
        Scenario(
            _primary_id(k, tau),
            "primary",
            k,
            0.0,
            tau,
            "linear",
            None,
        )
        for k in PRIMARY_K
        for tau in TAU_VALUES
    )
    audits = (
        Scenario(
            "translation-k010-tau-0p0000-mu-0p3000-linear",
            "translation",
            10,
            0.3,
            0.0,
            "linear",
            _primary_id(10, 0.0),
        ),
        Scenario(
            "translation-k050-tau-0p0625-mu-0p3000-linear",
            "translation",
            50,
            0.3,
            0.0625,
            "linear",
            _primary_id(50, 0.0625),
        ),
        Scenario(
            "large-study-k500-tau-0p0000-mu-0p0000-linear",
            "large_study",
            500,
            0.0,
            0.0,
            "linear",
            None,
        ),
        Scenario(
            "large-study-k500-tau-0p2500-mu-0p0000-linear",
            "large_study",
            500,
            0.0,
            0.25,
            "linear",
            None,
        ),
        Scenario(
            "se-shape-k020-tau-0p0000-mu-0p0000-reversed-linear",
            "se_shape",
            20,
            0.0,
            0.0,
            "reversed_linear",
            _primary_id(20, 0.0),
        ),
        Scenario(
            "se-shape-k050-tau-0p0625-mu-0p0000-reversed-linear",
            "se_shape",
            50,
            0.0,
            0.0625,
            "reversed_linear",
            _primary_id(50, 0.0625),
        ),
        Scenario(
            "se-shape-k020-tau-0p0000-mu-0p0000-piecewise-log",
            "se_shape",
            20,
            0.0,
            0.0,
            "piecewise_log",
            _primary_id(20, 0.0),
        ),
        Scenario(
            "se-shape-k050-tau-0p0625-mu-0p0000-piecewise-log",
            "se_shape",
            50,
            0.0,
            0.0625,
            "piecewise_log",
            _primary_id(50, 0.0625),
        ),
    )
    scenarios = primary + audits
    if len(scenarios) != 38 or len({item.scenario_id for item in scenarios}) != 38:
        raise AssertionError("M7B mapping scenario identity is inconsistent")
    return scenarios


def confirmation_scenarios() -> tuple[Scenario, ...]:
    """Return the immutable eight-cell independent confirmation grid."""

    focal_cells = (
        (10, 0.0),
        (20, 0.0),
        (50, 0.0),
        (100, 0.0),
        (20, 0.025),
        (50, 0.025),
        (20, 0.0625),
        (50, 0.0625),
    )
    return tuple(
        Scenario(
            _primary_id(k, tau),
            "primary",
            k,
            0.0,
            tau,
            "linear",
            None,
        )
        for k, tau in focal_cells
    )


def _standard_errors(scenario: Scenario) -> np.ndarray[Any, np.dtype[np.float64]]:
    if scenario.standard_error_grid == "linear":
        values = np.linspace(0.15, 0.35, scenario.k, dtype=np.float64)
    elif scenario.standard_error_grid == "reversed_linear":
        values = np.linspace(0.35, 0.15, scenario.k, dtype=np.float64)
    else:
        lower_count = scenario.k // 2
        upper_count = scenario.k - lower_count
        values = cast(
            np.ndarray[Any, np.dtype[np.float64]],
            np.concatenate(  # pyright: ignore[reportUnknownMemberType]
                (
                    np.geomspace(0.15, 0.25, lower_count, dtype=np.float64),
                    np.geomspace(0.25, 0.35, upper_count, dtype=np.float64),
                )
            ),
        )
    if (
        values.size != scenario.k
        or not isclose(float(np.min(values)), 0.15)
        or not isclose(float(np.max(values)), 0.35)
        or not isclose(float(np.median(values)), 0.25)
    ):
        raise AssertionError("M7B standard-error grid identity is inconsistent")
    return values


def _scenario_seed_words(scenario_id: str) -> tuple[int, ...]:
    digest = hashlib.sha256(scenario_id.encode("ascii")).digest()
    return tuple(
        int.from_bytes(digest[offset : offset + 4], "little")
        for offset in range(0, 16, 4)
    )


def _rng(seed_root: int, scenario_id: str, case: int) -> np.random.Generator:
    entropy = (seed_root, *_scenario_seed_words(scenario_id), case)
    return np.random.Generator(np.random.PCG64DXSM(np.random.SeedSequence(entropy)))


def _stream_id(scenario: Scenario) -> str:
    if scenario.standard_error_grid == "reversed_linear":
        if scenario.matched_primary_id is None:
            raise AssertionError("reversed M7B audit must identify its primary cell")
        return scenario.matched_primary_id
    return scenario.scenario_id


def _failure(code: str) -> CaseResult:
    return CaseResult(False, None, None, None, None, None, None, code)


def _run_case(task: tuple[Scenario, int, int]) -> CaseResult:
    scenario, case, seed_root = task
    errors = _standard_errors(scenario)
    generator = _rng(seed_root, _stream_id(scenario), case)
    draws = generator.standard_t(4, scenario.k)
    if scenario.standard_error_grid == "reversed_linear":
        draws = draws[::-1]
    estimates = scenario.mu + np.sqrt(errors * errors + scenario.tau**2) * draws
    data = pl.DataFrame(
        {
            "term": [f"study-{index + 1}" for index in range(scenario.k)],
            "estimate": estimates,
            "standard_error": errors,
        }
    )
    try:
        analysis = cast(
            RobustMetaAnalysis,
            analyze_ggcoefstats(data, type="robust", **COMMON),
        )
        result = analysis.result
        pooled = result.meta_analysis.pooled
        interval = pooled.interval
        values = (
            pooled.estimate,
            pooled.tau_squared,
            interval.low,
            interval.high,
        )
        if not all(isfinite(value) for value in values):
            return _failure("m7b_non_finite_output")
        if interval.low > interval.high or not (
            interval.low <= pooled.estimate <= interval.high
        ):
            return _failure("m7b_interval_order_violation")
        if result.work.actual_work < 0 or result.convergence.profile_evaluations < 0:
            return _failure("m7b_work_record_invalid")
        signed_error = pooled.estimate - scenario.mu
        return CaseResult(
            interval.low <= scenario.mu <= interval.high,
            interval.high - interval.low,
            abs(signed_error),
            signed_error,
            pooled.tau_squared == 0.0,
            result.work.actual_work,
            result.convergence.profile_evaluations,
            None,
        )
    except M6CMetaError as error:
        return _failure(error.code)
    except (ArithmeticError, RuntimeError, TypeError, ValueError):
        return _failure("m7b_unexpected_fit_exception")


def _wilson(successes: int, total: int) -> tuple[float, float]:
    probability = successes / total
    critical = NormalDist().inv_cdf(0.5 + WILSON_LEVEL / 2.0)
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


def _quantile(values: list[float], probability: float) -> float | None:
    if not values:
        return None
    return float(
        np.quantile(  # pyright: ignore[reportUnknownMemberType]
            np.asarray(values, dtype=np.float64), probability
        )
    )


def _mean_and_mcse(values: list[float]) -> tuple[float | None, float | None]:
    if not values:
        return None, None
    array = np.asarray(values, dtype=np.float64)
    mean = float(np.mean(array))
    mcse = 0.0 if array.size == 1 else float(np.std(array, ddof=1) / sqrt(array.size))
    return mean, mcse


def summarize_cell(
    scenario: Scenario, cases: int, results: list[CaseResult]
) -> dict[str, Any]:
    """Summarize a cell without dropping failures from the coverage denominator."""

    if len(results) != cases:
        raise ValueError("M7B cell result count does not match its locked denominator")
    completed = [item for item in results if item.failure_code is None]
    covered = sum(item.covered for item in results)
    wilson_low, wilson_high = _wilson(covered, cases)
    widths = [cast(float, item.interval_width) for item in completed]
    absolute_errors = [cast(float, item.absolute_error) for item in completed]
    signed_errors = [cast(float, item.signed_error) for item in completed]
    work = [float(cast(int, item.work_evaluations)) for item in completed]
    profile = [float(cast(int, item.profile_evaluations)) for item in completed]
    mean_signed_error, signed_error_mcse = _mean_and_mcse(signed_errors)
    failures = Counter(
        item.failure_code for item in results if item.failure_code is not None
    )
    scenario_record = asdict(scenario)
    scenario_record["standard_error_sha256"] = hashlib.sha256(
        _standard_errors(scenario).tobytes()
    ).hexdigest()
    stream_id = _stream_id(scenario)
    scenario_record["random_stream_id"] = stream_id
    scenario_record["stream_seed_words"] = list(_scenario_seed_words(stream_id))
    scenario_record["paired_permutation_audit"] = (
        scenario.standard_error_grid == "reversed_linear"
    )
    return {
        "scenario": scenario_record,
        "cases": cases,
        "successes": len(completed),
        "failures": cases - len(completed),
        "failure_counts": dict(sorted(failures.items())),
        "coverage_denominator_includes_failures": True,
        "covered": covered,
        "coverage": covered / cases,
        "wilson_99_low": wilson_low,
        "wilson_99_high": wilson_high,
        "undercoverage": wilson_high < CONFIDENCE_LEVEL,
        "conservative": wilson_low > CONFIDENCE_LEVEL,
        "interval_width_p10": _quantile(widths, 0.10),
        "interval_width_median": _quantile(widths, 0.50),
        "interval_width_p90": _quantile(widths, 0.90),
        "median_absolute_pooled_error": _quantile(absolute_errors, 0.50),
        "mean_signed_error": mean_signed_error,
        "mean_signed_error_mcse": signed_error_mcse,
        "boundary_fits": sum(item.boundary_fit is True for item in completed),
        "boundary_fit_fraction": (
            sum(item.boundary_fit is True for item in completed) / len(completed)
            if completed
            else None
        ),
        "work_evaluations_median": _quantile(work, 0.50),
        "work_evaluations_p99": _quantile(work, 0.99),
        "profile_evaluations_median": _quantile(profile, 0.50),
        "profile_evaluations_p99": _quantile(profile, 0.99),
    }


def _git(*args: str) -> str:
    completed = subprocess.run(
        ("git", *args),
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _source_identity() -> tuple[str, bool]:
    return _git("rev-parse", "HEAD"), not bool(_git("status", "--porcelain"))


def _sealed_digest(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    seal = path.with_suffix(path.suffix + ".sha256")
    expected = seal.read_text().strip().split(maxsplit=1)
    if len(expected) != 2 or expected[0] != digest or expected[1] != path.name:
        raise RuntimeError(f"M7B artifact seal does not match {path.name}")
    return digest


def _run_configuration(kind: RunKind) -> tuple[int, int, tuple[Scenario, ...]]:
    if kind == "smoke":
        return SMOKE_CASES, SMOKE_SEED, mapping_scenarios()
    if kind == "mapping":
        return MAPPING_CASES, MAPPING_SEED, mapping_scenarios()
    return CONFIRMATION_CASES, CONFIRMATION_SEED, confirmation_scenarios()


def _preflight(kind: RunKind, workers: int, output: Path) -> str | None:
    if not 1 <= workers <= MAXIMUM_WORKERS:
        raise ValueError(f"workers must be from 1 through {MAXIMUM_WORKERS}")
    if kind == "smoke":
        work_root = (ROOT / ".work").resolve()
        if not output.resolve().is_relative_to(work_root):
            raise ValueError("disposable M7B smoke output must stay under .work")
    else:
        expected = MAPPING_OUTPUT if kind == "mapping" else CONFIRMATION_OUTPUT
        if output.resolve() != expected.resolve():
            raise ValueError("locked M7B runs must use the predeclared artifact path")
        _, clean = _source_identity()
        if not clean:
            raise RuntimeError("locked M7B runs require a clean source tree")
        if output.exists() or output.with_suffix(output.suffix + ".sha256").exists():
            raise FileExistsError("locked M7B artifacts cannot be overwritten")
    if kind == "confirmation":
        if not MAPPING_OUTPUT.exists():
            raise FileNotFoundError("sealed M7B mapping evidence is required first")
        return _sealed_digest(MAPPING_OUTPUT)
    return None


def run(kind: RunKind, workers: int, output: Path) -> dict[str, Any]:
    """Execute one fixed M7B run and write its summarized artifact."""

    mapping_digest = _preflight(kind, workers, output)
    cases, seed_root, scenarios = _run_configuration(kind)
    commit, clean = _source_identity()
    summaries: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=workers) as executor:
        for scenario in scenarios:
            tasks = ((scenario, case, seed_root) for case in range(cases))
            results = list(executor.map(_run_case, tasks, chunksize=10))
            summaries.append(summarize_cell(scenario, cases, results))
    blockers = any(item["undercoverage"] or item["failures"] for item in summaries)
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "plan_version": PLAN_VERSION,
        "run": kind,
        "status": (
            "disposable_smoke"
            if kind == "smoke"
            else "completed_with_reaffirmation_blocker"
            if blockers
            else "completed_pending_independent_review"
        ),
        "decision_disposition": "not_decided",
        "source_commit": commit,
        "source_tree_clean": clean,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "dependency_versions": {name: version(name) for name in DEPENDENCIES},
        "workers": workers,
        "cases_per_cell": cases,
        "scenario_count": len(scenarios),
        "total_fits": cases * len(scenarios),
        "bit_generator": "PCG64DXSM",
        "seed_root": seed_root,
        "stream_derivation": (
            "SeedSequence(seed_root, sha256(scenario_id)[0:16] as four "
            "little-endian uint32 words, case_index)"
        ),
        "paired_stream_policy": (
            "reversed-linear audit fits deterministically reverse the matched "
            "primary case and consume no independent random stream"
        ),
        "confidence_level": CONFIDENCE_LEVEL,
        "wilson_level": WILSON_LEVEL,
        "quantile_method": "numpy_linear",
        "failure_policy": "all failures remain uncovered in the cell denominator",
        "mapping_artifact_sha256": mapping_digest,
        "cells": summaries,
    }
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    if len(encoded) > MAXIMUM_ARTIFACT_BYTES:
        raise RuntimeError("M7B artifact exceeds the approved 5 MiB ceiling")
    output.parent.mkdir(parents=True, exist_ok=True)
    mode = "wb" if kind == "smoke" else "xb"
    with output.open(mode) as artifact:
        artifact.write(encoded)
    if kind != "smoke":
        digest = hashlib.sha256(encoded).hexdigest()
        seal = output.with_suffix(output.suffix + ".sha256")
        with seal.open("x") as seal_file:
            seal_file.write(f"{digest}  {output.name}\n")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--run", choices=("smoke", "mapping", "confirmation"), required=True
    )
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    kind = cast(RunKind, args.run)
    default_output = {
        "smoke": SMOKE_OUTPUT,
        "mapping": MAPPING_OUTPUT,
        "confirmation": CONFIRMATION_OUTPUT,
    }[kind]
    output = args.output or default_output
    payload = run(kind, args.workers, output)
    print(
        json.dumps(
            {
                "output": str(output.relative_to(ROOT)),
                "run": kind,
                "status": payload["status"],
                "total_fits": payload["total_fits"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
