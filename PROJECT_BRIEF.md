# Project Brief

- Status: Draft; M0 decisions requiring accountable owners remain open
- Last updated: 2026-09-13

## Outcome

- Problem and affected users: Python analysts, researchers, educators, and
  report authors must currently coordinate plotting, statistical tests, effect
  sizes, uncertainty, corrections, and distribution diagnostics across multiple
  libraries. `plotsalot` will provide cohesive, inspectable plot-plus-result
  workflows derived from the public behavior of `ggstatsplot` and `qqplotr`.
- Measurable success criteria: Every one of the 37 combined upstream exports is
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
  save the Matplotlib result; pass supported Statsmodels/tidy coefficients;
  compose Q–Q/P–P points, reference lines, detrending, and approved bands.

## Constraints and risk

- Runtime/deployment environment: Python 3.11+ library for Linux and macOS,
  notebooks, scripts, and headless CI; wheels and sdist; no service or database.
- Expected load and growth: benchmark 10K, 100K, and 1M-row univariate,
  scatter, and Q–Q workloads plus 10-, 25-, and 50-variable correlation
  matrices during M0.
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
- Legal/compliance constraints: preserve MIT notices for `ggstatsplot`-derived
  material; `qqplotr` is GPL-3 and creates a blocking license decision before
  source copying or translation; credit both upstream projects and publications;
  do not imply official status without approval.
- Budget and delivery deadline: initial estimate 46–64 engineer-weeks and 6–9
  calendar months with two engineers plus a part-time statistical reviewer;
  recalibrate after M0. No committed deadline or financial budget is assigned.
- Owners and on-call expectations: product, technical, statistical,
  visualization, and release/security owners are unassigned. No on-call duty is
  required before a supported public release.
- Top failure or abuse scenarios: mislabeled estimator or interval; lost pairing;
  inconsistent plotted/tested samples; invalid stochastic output presented as
  precise; wrong Q–Q/P–P band coverage semantics; R/SciPy parameterization drift;
  resource exhaustion; license contamination; implied upstream endorsement.

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
  interval, distribution, quantile, detrending, and randomness metadata are
  retained; imports have no I/O or global plotting/random-state side effects.
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
| Repository is generated and reproducible | `uv.lock`, `make check`, `uv build` | Technical lead | Passing for M0 |
| Both upstreams are pinned | `docs/upstream/manifest.json` and hashes | Technical lead | Passing |
| Public API inventory is complete | `docs/compatibility.md` versus namespaces | Product owner | Baseline complete |
| No R runtime dependency | Python-only isolated wheel smoke test | Technical lead | Passing for prototype |
| Statistical correctness | Method specs, analytic cases, R oracle, independent review | Statistical owner | Blocked on owner |
| GPL/MIT posture | ADR-010 and qualified review | Product/release owners | Blocking |
| Initial walking skeleton | Focused tests and saved headless figure | Technical lead | Passing |

## Open decisions

| Question | Decision deadline | Owner | ADR |
|---|---|---|---|
| Is `plotsalot` an official port and what license will it use? | End of M0 | Product owner | ADR-001, ADR-010 |
| Which renderer and dataframe contracts are stable? | End of M0 | Technical/visualization owners | ADR-002, ADR-003 |
| Which behaviors define compatibility? | End of M0 | Product/statistical owners | ADR-004 |
| Which Bayesian, robust, and diagnostic-band methods ship? | Before their implementation | Statistical owner | ADR-005, ADR-006, ADR-011 |
| How are distributions and R quantile types mapped? | Before Q–Q/P–P code | Statistical owner | ADR-012 |
