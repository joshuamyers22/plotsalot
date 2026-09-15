# Project Brief

- Status: M0–M6 and public 0.1.1 complete; M7 active
- Last updated: 2026-09-15

## Outcome

- Problem and affected users: Python analysts, researchers, educators, and
  report authors must currently coordinate plotting, statistical tests, effect
  sizes, uncertainty, corrections, and distribution diagnostics across multiple
  libraries. `plotsalot` will provide cohesive, inspectable plot-plus-result
  workflows derived from the public behavior of `ggstatsplot`.
- Measurable success criteria: Every one of the 22 upstream exports is
  classified as equivalent, adapted, experimental, or deferred; each supported
  statistic maps to a versioned result field and specification; deterministic
  methods pass R-oracle and independent-reference fixtures at method-specific
  tolerances; released wheels and sdists install and run without R or network
  access.
- Explicit non-goals: line-by-line R translation; R tidy evaluation; arbitrary
  `ggplot2` layer compatibility; pixel identity; automatic interpretation of
  results; support for every R model class in 1.0; an initial Shiny-equivalent
  application; any claim of upstream endorsement.
- Critical user journeys: create one statistical plot from a Polars dataframe;
  extract structured results and annotations; create grouped panels; modify and
  save the Matplotlib result; pass supported Statsmodels/tidy coefficients.

## Constraints and risk

- Runtime/deployment environment: Python 3.11+ library for Linux and macOS,
  notebooks, scripts, and headless CI; wheels and sdist; no service or database.
- Expected load and growth: benchmark 10K, 100K, and 1M-row univariate and
  scatter workloads plus 10-, 25-, and 50-variable correlation matrices. M0
  establishes the implemented univariate baseline; each remaining
  family joins the retained grid at its implementation milestone.
- Data classification and retention: caller-owned in-process data; no implicit
  persistence, logging of rows, or remote telemetry; figures and evidence are
  saved only by explicit user action.
- Availability objectives: not applicable to a local library. Import and core
  deterministic workflows must remain independent of network and R runtimes.
- Latency distribution, jitter, throughput, and measurement boundary: M0 will
  measure analysis separately from rendering. Subsequent releases may not
  regress median time or peak memory by more than 20% on the stable benchmark
  host without an approved performance record.
- Queue/capacity limits and overload behavior: no queues. Resampling, Bayesian
  work, group counts, labels, correlation dimensions, and artist counts require
  finite defaults and explicit override/budget behavior.
- Recovery point/time objectives: not applicable. Published package artifacts
  must be reproducible and traceable; defective releases are yanked and patched.
- Legal/compliance constraints: preserve applicable MIT notices for
  `ggstatsplot`-derived material; credit upstream projects and publications; do
  not imply official status.
- Budget and delivery deadline: initial estimate 42–58 engineer-weeks and 6–8
  calendar months with two engineers plus a part-time statistical reviewer;
  recalibrate after M0. No committed deadline or financial budget is assigned.
- Owners and on-call expectations: Joshua Myers is the product, M0 statistical,
  and license approver. Technical, visualization, and release/security roles
  remain unassigned. No on-call duty is required before a supported release.
- Top failure or abuse scenarios: mislabeled estimator or interval; lost pairing;
  inconsistent plotted/tested samples; invalid stochastic output presented as
  precise; R/SciPy parameterization drift; resource exhaustion; license
  contamination; implied upstream endorsement.

## System outline

- Sources of truth: approved statistical method files, public API contracts,
  tests, frozen oracle manifests, ADRs, and the compatibility matrix. Upstream
  repositories are behavioral references pinned in `docs/upstream/manifest.json`.
- External dependencies: Polars, NumPy, SciPy, Statsmodels, and Matplotlib.
  PyMC/ArviZ and higher-level renderers remain candidates, not baseline
  dependencies.
- Trust boundaries: untrusted caller data, labels, model objects, paths, style
  options, distribution objects, and serialized result input; development-only
  R oracle environment; package build and publication pipeline.
- Core domain invariants: the displayed and tested samples reconcile; pairing is
  explicit; every rendered number comes from a typed result field; correction,
  interval, distribution, and randomness metadata are retained; imports have no
  I/O or global plotting/random-state side effects.
- Consistency and concurrency needs: result objects are immutable value records;
  random generators are caller-owned or locally constructed; no shared mutable
  analysis state.
- Deployment and migration strategy: incremental 0.x releases with a
  machine-readable compatibility matrix; 1.0 only after every upstream symbol is
  dispositioned and release evidence is approved.
- Observability signals: typed warnings/errors, result provenance, optional
  progress callbacks, reproducibility artifacts, and retained benchmarks; no
  remote telemetry.
- Replay and performance-regression evidence: frozen input/output oracle
  fixtures, environment manifests, analytic cases, semantic visual tests, and
  stable-host benchmark distributions.

## Acceptance evidence

| Requirement | Verification | Owner | Status |
|---|---|---|---|
| Repository is generated and reproducible | `uv.lock`, `make check`, `uv build` | Technical lead | Passing for published 0.1.1 |
| Upstream is pinned | `docs/upstream/manifest.json` and hashes | Technical lead | Passing |
| Public API inventory is complete | `docs/compatibility.md`, M7 machine ledger, and namespaces | Product owner | 22-export 1.0 scope approved; detailed API/schema inventory active |
| No R runtime dependency | Python-only isolated wheel smoke test | Technical lead | Passing for published 0.1.1 |
| Statistical correctness | Method specs, analytic cases, R oracle, independent review | Joshua Myers | M0–M6 approved; M6C boundary disposition provisional until M7 |
| MIT license posture | ADR-010 and qualified review | Joshua Myers | Approved |
| Trusted package publication | OIDC release workflow, hashes, metadata, and clean-index smoke | Joshua Myers | 0.1.1 published and verified |

## Open decisions

| Question | Decision deadline | Owner | ADR |
|---|---|---|---|
| Select the final M6C robust-meta disposition from the locked experiment evidence | M7B close | Joshua Myers | M7-D2 / ADR-005 |
| Accept the exact hardened candidate as plotsalot 1.0 | M7 exit | Joshua Myers | M7 contract |
