# ADR-005: Native bounded robust-method architecture

- Status: Accepted
- Date: 2026-09-14
- Owner/approver: Joshua Myers

## Context and options

M6A adds robust modes to plotsalot's existing univariate, correlation,
independent-comparison, repeated-comparison, matrix, and grouped workflows. The
pinned upstream implementation delegates these paths across
`statsExpressions==2.1.1`, `WRS2==1.1-7`, and `correlation`, sometimes using R's
global RNG, hidden resample counts, hard-coded confidence behavior, or different
inferential approximations for the same displayed estimator.

The realistic production options are:

1. invoke R/WRS2 at runtime, which violates the accepted no-R-runtime contract;
2. add a broad Python robust-statistics dependency and inherit its object,
   fallback, and release behavior;
3. implement the narrowly approved trimmed/Winsorized formulas with NumPy/SciPy
   and use pinned WRS2 only as a development oracle; or
4. keep robust modes deferred.

Robust methods also introduce estimator-specific effective samples and, for the
proposed correlation interval, stochastic resampling. Those require explicit
RNG ownership, work accounting, deterministic grouped streams, and atomic
failure semantics.

## Decision

Adopt option 3 for M6A under the approved R1–R3 and G6 decisions in
`../M6_STATISTICAL_METHODS.md`.

- Production robust calculations use owned NumPy arrays, SciPy distributions,
  and small plotsalot-native formula modules. R/WRS2 remains a pinned
  development oracle and is never imported or invoked at runtime.
- Only methods explicitly approved in R1–R3 are implemented. A shared internal
  trimmed/Winsorized kernel owns sorting, tail counts, Winsorized variance and
  covariance, effective count, and finite/degenerate checks.
- Robust mode is caller-selected. Diagnostics, contamination, outliers, failed
  classical assumptions, or numerical problems never switch methods.
- No observation is silently classified or removed as an outlier. Trimming and
  Winsorization are estimator operations over the retained audited sample, not
  sample-selection operations.
- Deterministic analytic inference is preferred where the approved method
  supports it. Stochastic work is limited to an explicitly approved interval or
  effect procedure and uses a locally constructed `numpy.random.Generator` from
  a caller-supplied integer seed.
- Resampling uses an immutable plan retained in the result: algorithm, seed,
  requested/successful/failed replicate counts, quantile method, work limit,
  and software identity. Python's global RNG and Python's randomized `hash()`
  are forbidden.
- Group and matrix child seeds are derived from the root seed plus canonical
  typed identities using SHA-256 and NumPy `SeedSequence`. Worker or iteration
  order cannot affect the mapping.
- M6A executes synchronously and serially. No worker-count or progress API is
  added in the first robust release. Later parallel execution requires an ADR
  amendment and replay evidence.
- Default and hard work ceilings are checked before allocation or resampling.
  Exhaustion raises a stable error; draws, rows, variables, groups, hypotheses,
  or labels are never silently reduced.
- Nonconvergence, non-finite output, degenerate Winsorized scale, insufficient
  effective sample, or inadequate valid bootstrap replicates fails atomically.
  There is no classical, nonparametric, or alternate-robust fallback.
- Robust results are distinct typed schema variants. They retain estimator,
  trimming, effective-sample, test/interval, resampling, software, audit,
  warning, and resource records. Rendering performs no robust calculation.

## Consequences

- The production dependency set need not grow for M6A.
- Formula ownership increases implementation and evidence burden; each kernel
  needs direct equations, independent calculations, pinned-R fixtures,
  metamorphic tests, and mutation-resistant results.
- Some Python outputs will be classified as adapted rather than equivalent.
  In particular, the proposed M6A path does not inherit upstream's hidden/global
  RNG, 100–500-resample defaults, hard-coded 95% branches, or ordinary Pearson
  inference applied after Winsorization.
- A caller must provide a seed when requesting a robust path that uses
  bootstrap inference. This is intentionally stricter than upstream.
- Large correlation matrices may hit the resampling-work ceiling even though
  the same shape is allowed for classical Pearson analysis. The call fails
  before work rather than sampling rows or reducing pair counts.
- The design is reversible: an independently reviewed Python dependency can
  replace a native kernel through a later ADR while preserving public result
  semantics and evidence fixtures.

## Approved M6C clarification

The R4 record in `../M6C_STATISTICAL_METHODS.md` extends the same native,
bounded, no-fallback architecture to M6C. Caller-reported robust coefficient
intervals perform no fitting. Robust aggregate meta-analysis uses the approved
fixed-Student-t4 hierarchy, deterministic multistart maximum likelihood,
profile-likelihood inference, retained latent weights, and explicit work and
convergence records. It adds no robust-statistics runtime dependency, RNG, or
automatic study deletion. Joshua Myers approved this clarification with R4 on
2026-09-15.

## Verification

Acceptance requires:

- Joshua Myers's approval of this ADR and applicable R1–R4/G6 decisions;
- direct unit tests for every trimmed/Winsorized formula and boundary;
- analytic or separately implemented reference calculations;
- raw and normalized pinned WRS2/statsExpressions fixtures;
- clean-data, contamination, location/scale, ordering, tie, small-sample,
  perfect-association, and degenerate-scale tests;
- same-seed replay and different-seed distributional checks without claiming
  cross-language bit identity;
- seed derivation invariant to execution order and process hash randomization;
- preflight resource, invalid-replicate, fault-injection, and no-fallback tests;
- semantic render/extraction/grouping/composition tests; and
- `make check`, audit, build, oracle, benchmark, and isolated-wheel smoke gates.

Reconsider this decision if calibration cannot meet its approved bounds, the
native formulas cannot be independently maintained, a required platform cannot
reproduce seeded execution within its declared contract, or robust work causes
an unresolved regression in classical paths.
