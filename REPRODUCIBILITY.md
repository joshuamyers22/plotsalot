# Reproducibility

Plotsalot separates runtime behavior, development-time compatibility evidence,
and retained performance evidence. A released wheel or sdist requires only
Python and its declared Python dependencies; it never invokes R, Docker, or the
network.

## Runtime and dependency environment

- Supported Python versions begin at 3.11 and are declared in `pyproject.toml`.
- `uv.lock` is the authoritative resolver-generated development lockfile.
- Local and CI environments use `uv sync --frozen --dev`.
- Runtime versions and method provenance are retained in structured evidence
  where the result contract requires them.
- Dependency changes update `pyproject.toml` and the regenerated lockfile
  together and rerun numerical regression evidence.

## Tests and builds

From a clean checkout:

```sh
make setup
make check
make audit
make build
```

`make check` runs formatting, lint, strict type checking, the unit and contract
tests, branch-aware coverage enforcement, and documentation-link validation. `make
audit` queries OSV for locked runtime dependencies and checks the dependency
license allowlist. `make build` creates the sdist and universal wheel from the
declared build backend.

Release tags must exactly match package metadata. Release artifacts are built in
CI from the tagged commit; local `dist/` files are ignored and are not release
inputs.

## Statistical and stochastic evidence

Each analysis contract defines sample construction, missing/non-finite handling,
estimand, interval or posterior convention, correction family, and failure
behavior. Consequential changes require an updated method specification and
review evidence.

Random procedures require an explicit seed or a documented identity-derived
stream. Robust bootstrap and Bayesian randomized quasi-Monte Carlo paths use
owned generators, bounded work, and retained generator/provenance metadata. A
request that exceeds its ceiling fails before drawing rather than silently
reducing work.

## R oracle

The development-only oracle is pinned by `oracle/renv.lock` and the upstream
revision recorded in `docs/upstream/manifest.json`. Checked-in fixtures include
input and output hashes and are verified without R during the default test suite.

To regenerate reviewed oracle fixtures:

```sh
make oracle
```

This command requires Docker and the declared R platform. Differences caused by
intentional Python adaptations are documented in the method specifications and
compatibility matrix rather than hidden by loose tolerances.

## Performance evidence

Retained benchmark artifacts record workload shape, phase-separated samples,
environment identity, and allocation or work measurements. Regenerate them only
on a controlled host appropriate for comparison:

```sh
make benchmark
```

Shared CI verifies artifact shape and invariants but does not treat noisy timing
on a generic runner as a release threshold.

## Data and downstream results

Callers own their source data and saved figures. Plotsalot performs no implicit
persistence or remote telemetry. For reproducible downstream work, retain the
package version, Git revision when applicable, structured result, analysis
parameters, input identity/hash, units, random seed, and evaluation time.

The included dataset and regression-evidence utilities retain stricter source,
schema, availability, and output hashes for their documented workflows. See
`docs/PARQUET_DATASETS.md` and `docs/REGRESSION_EVIDENCE.md`.
