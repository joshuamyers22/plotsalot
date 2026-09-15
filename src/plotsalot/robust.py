"""Approved fixed-20% trimmed and Winsorized numerical kernels for M6A."""

from __future__ import annotations

from hashlib import sha256
from importlib import import_module
from math import ceil, floor, sqrt
from typing import Protocol, cast

import numpy as np

from plotsalot.data import FloatArray
from plotsalot.robust_result import (
    ResamplingResult,
    RobustMethodResult,
    TrimmedKernelResult,
)

TRIM_FRACTION = 0.20
DEFAULT_BOOTSTRAP_RESAMPLES = 1_999
DEFAULT_MAX_RESAMPLE_WORK = 100_000_000
HARD_MAX_RESAMPLE_WORK = 500_000_000
BATCH_INDEX_LIMIT = 1_000_000


class _VersionedModule(Protocol):
    __version__: str


scipy = cast(_VersionedModule, import_module("scipy"))


def method_result(name: str) -> RobustMethodResult:
    return RobustMethodResult(
        name=name,
        version="m6a-1",
        compatibility="adapted",
        numpy_version=np.__version__,
        scipy_version=scipy.__version__,
    )


def validate_trim_fraction(trim_fraction: float) -> None:
    if not np.isfinite(trim_fraction) or trim_fraction != TRIM_FRACTION:
        raise ValueError("trim_fraction must equal 0.20 for M6A robust methods")


def trimmed_kernel(
    values: FloatArray, *, trim_fraction: float = TRIM_FRACTION
) -> tuple[TrimmedKernelResult, FloatArray]:
    """Return the approved kernel record and ephemeral Winsorized values."""

    validate_trim_fraction(trim_fraction)
    array: FloatArray = np.asarray(values, dtype=np.float64)
    if array.ndim != 1 or array.size < 5:
        raise ValueError("robust samples require at least five observations")
    if not bool(np.isfinite(array).all()):
        raise ValueError("robust samples must contain only finite values")
    ordered = array.copy()
    ordered.sort()
    n = int(array.size)
    g = floor(trim_fraction * n)
    h = n - (2 * g)
    if g < 1 or h < 3:
        raise ValueError("robust sample has an invalid effective count")
    lower = float(ordered[g])
    upper = float(ordered[n - g - 1])
    trimmed_mean = float(np.mean(ordered[g : n - g]))
    winsorized = array.copy()
    winsorized[winsorized < lower] = lower
    winsorized[winsorized > upper] = upper
    variance = float(np.var(winsorized, ddof=1))
    if not np.isfinite(variance) or variance <= 0.0:
        raise ValueError("robust sample requires positive Winsorized variance")
    q = ((n - 1) * variance) / (h * (h - 1))
    if not np.isfinite(q) or q <= 0.0:
        raise ValueError("robust trimmed-mean variance is invalid")
    record = TrimmedKernelResult(
        trim_fraction=trim_fraction,
        n=n,
        g=g,
        h=h,
        lower_bound=lower,
        upper_bound=upper,
        trimmed_mean=trimmed_mean,
        winsorized_variance=variance,
        q=q,
    )
    return record, winsorized


def validate_resampling(
    *,
    bootstrap_resamples: int,
    random_seed: int | None,
    maximum_resample_work: int,
    calculated_work: int,
) -> int:
    if (
        type(bootstrap_resamples) is not int
        or not 999 <= bootstrap_resamples <= 9_999
        or bootstrap_resamples % 2 != 1
    ):
        raise ValueError("bootstrap_resamples must be an odd integer from 999 to 9999")
    if type(random_seed) is not int or not 0 <= random_seed <= (2**64) - 1:
        raise ValueError(
            "random_seed is required and must be an unsigned 64-bit integer"
        )
    if (
        type(maximum_resample_work) is not int
        or maximum_resample_work < 1
        or maximum_resample_work > HARD_MAX_RESAMPLE_WORK
    ):
        raise ValueError("maximum_resample_work must be an integer from 1 to 500000000")
    if calculated_work > maximum_resample_work:
        raise ValueError(
            f"resample work {calculated_work} exceeds maximum_resample_work="
            f"{maximum_resample_work}"
        )
    return random_seed


def typed_identity(value: object) -> str:
    if isinstance(value, bool):
        return f"bool:{str(value).lower()}"
    if isinstance(value, int):
        return f"int:{value}"
    if isinstance(value, float) and np.isfinite(value):
        return f"float:{value.hex()}"
    if isinstance(value, str) and value:
        return f"str:{value}"
    raise TypeError("seed identities must be finite scalar identities")


def child_seed(
    root_seed: int, analysis: str, identities: tuple[object, ...]
) -> tuple[int, str]:
    encoded = "|".join(
        (typed_identity(analysis), *(typed_identity(value) for value in identities))
    )
    digest = sha256(encoded.encode("utf-8")).digest()
    digest_words = [
        int.from_bytes(digest[index : index + 4], "little")
        for index in range(0, len(digest), 4)
    ]
    entropy = [root_seed, *digest_words]
    sequence = np.random.SeedSequence(entropy)
    generated = int(sequence.generate_state(1, dtype=np.uint64)[0])
    return generated, encoded


def winsorized_correlation(
    x: FloatArray, y: FloatArray
) -> tuple[float, float, TrimmedKernelResult, TrimmedKernelResult]:
    x_kernel, x_winsorized = trimmed_kernel(x)
    y_kernel, y_winsorized = trimmed_kernel(y)
    covariance = float(np.cov(x_winsorized, y_winsorized, ddof=1)[0, 1])
    denominator = sqrt(x_kernel.winsorized_variance * y_kernel.winsorized_variance)
    estimate = covariance / denominator
    tolerance = 1e-12
    if (
        not np.isfinite(estimate)
        or estimate < -1.0 - tolerance
        or estimate > 1.0 + tolerance
    ):
        raise ValueError("Winsorized correlation is outside its numerical bounds")
    return max(-1.0, min(1.0, estimate)), covariance, x_kernel, y_kernel


def bootstrap_winsorized_correlation(
    x: FloatArray,
    y: FloatArray,
    *,
    conf_level: float,
    bootstrap_resamples: int,
    root_seed: int,
    derived_seed: int,
    child_identity: str,
    maximum_resample_work: int,
) -> tuple[float, float, ResamplingResult]:
    n = int(x.size)
    work = n * bootstrap_resamples
    validate_resampling(
        bootstrap_resamples=bootstrap_resamples,
        random_seed=root_seed,
        maximum_resample_work=maximum_resample_work,
        calculated_work=work,
    )
    generator = np.random.Generator(np.random.PCG64DXSM(derived_seed))
    batch_replicates = max(1, BATCH_INDEX_LIMIT // n)
    estimates: list[float] = []
    failed = 0
    for start in range(0, bootstrap_resamples, batch_replicates):
        count = min(batch_replicates, bootstrap_resamples - start)
        indices = generator.integers(0, n, size=(count, n), dtype=np.int64)
        for row in indices:
            try:
                estimate, _, _, _ = winsorized_correlation(x[row], y[row])
            except ValueError:
                failed += 1
            else:
                estimates.append(estimate)
    required = max(950, ceil(0.99 * bootstrap_resamples))
    if len(estimates) < required:
        raise ValueError(
            f"valid bootstrap replicates {len(estimates)} are below required {required}"
        )
    alpha = (1.0 - conf_level) / 2.0
    ordered_estimates = sorted(estimates)

    def type7(probability: float) -> float:
        position = (len(ordered_estimates) - 1) * probability
        lower_index = floor(position)
        upper_index = ceil(position)
        if lower_index == upper_index:
            return ordered_estimates[lower_index]
        fraction = position - lower_index
        return (
            ordered_estimates[lower_index] * (1.0 - fraction)
            + ordered_estimates[upper_index] * fraction
        )

    low = type7(alpha)
    high = type7(1.0 - alpha)
    return (
        low,
        high,
        ResamplingResult(
            algorithm="paired_percentile_bootstrap",
            bit_generator="PCG64DXSM",
            root_seed=root_seed,
            child_seed=derived_seed,
            child_identity=child_identity,
            requested_replicates=bootstrap_resamples,
            valid_replicates=len(estimates),
            failed_replicates=failed,
            quantile_method="linear_type7",
            calculated_work=work,
            maximum_resample_work=maximum_resample_work,
            hard_maximum_resample_work=HARD_MAX_RESAMPLE_WORK,
            batch_index_limit=BATCH_INDEX_LIMIT,
        ),
    )
