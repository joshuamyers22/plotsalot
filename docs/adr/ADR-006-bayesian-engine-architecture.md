# ADR-006: Isolated Bayesian engine and artifact boundary

- Status: Accepted
- Date: 2026-09-14
- Owner/approver: Joshua Myers

## Context and options

M6B/M6C will require Bayesian estimation, evidence measures, diagnostics, and
possibly posterior simulation. The core plotsalot package currently has a small
offline NumPy/SciPy/Statsmodels/Matplotlib/Polars runtime and no import-time I/O
or random-state side effects. The project brief names PyMC/ArviZ as candidates,
not baseline dependencies.

The architecture options are:

1. make a full probabilistic-programming stack mandatory for all users;
2. implement only analytic methods in the core and permanently exclude sampled
   models;
3. keep analytic approved methods in core and place sampled methods behind one
   locked optional `bayes` extra and a narrow internal engine port; or
4. keep all Bayesian methods deferred.

An engine choice cannot itself define likelihoods, priors, evidence semantics,
or diagnostic thresholds. Those remain B1–B6 statistical decisions.

## Decision

Adopt option 3 as the M6 architecture, while deferring the exact engine/version
and all Bayesian statistical methods to B1–B6 approval.

- Core analytic methods may use existing NumPy/SciPy primitives only when their
  likelihood, prior, evidence, and numerical algorithm are separately approved.
- Any sampling-based path is exposed through `plotsalot[bayes]`, imported lazily
  behind a narrow internal engine protocol. PyMC/ArviZ is the initial candidate,
  not an approved dependency until B6 records exact locked versions, platform
  support, licenses, diagnostics, and smoke evidence.
- Core import and every classical/robust path work without the extra. Invoking a
  sampled Bayesian mode without it raises one stable actionable error.
- The engine port accepts only plotsalot-owned immutable numerical inputs and an
  approved model specification. It does not execute caller model code, formulas,
  callbacks, custom likelihoods, arbitrary priors, or remote artifacts.
- RNG state is locally owned. Results retain root seed, child-stream derivation,
  chains, warmup, retained draws, parallelism, algorithm/settings, engine and
  package versions, work limits, and diagnostic summaries.
- Full draws are not embedded in default JSON results or persisted by plotsalot.
  A future caller-managed draw artifact may be referenced only by an explicit
  fingerprint and separate storage contract.
- Imports and analysis perform no network access, package download, telemetry,
  global warning/filter/backend mutation, or hidden unbounded parallelism.
- A diagnostic or convergence failure cannot fall back to another engine,
  approximation, prior, or classical result. Retry behavior, if any, must be a
  separately approved B6 algorithm and remain visible in the result.
- Minimal-core and `bayes`-extra dependency locks, license audits, builds, and
  offline wheel smoke tests are separate release gates.

## Consequences

- M6A can proceed without adding Bayesian dependencies after this architecture
  and ADR-005 are approved.
- Bayesian users may install a heavier optional environment, while classical
  and robust users retain the current core footprint.
- Supporting both analytic and sampled paths increases schema and testing work;
  their result variants must share semantics without implying identical
  algorithms or evidence.
- Exact engine/version selection remains intentionally blocked until M6B method
  design. This decision does not approve PyMC, ArviZ, a sampler, a prior, or a
  Bayes factor.
- General Bayesian regression/model execution remains outside plotsalot.

## Verification

Approval of this architecture requires dependency-resolution and platform
feasibility evidence before M6B implementation. Final verification must include
minimal/extra lock integrity, lazy-import tests, no-network/offline execution,
seed-stream replay, diagnostics and failure injection, draw non-retention,
resource/cancellation behavior, license/security audit, and isolated wheel
smokes on every supported platform.

Reconsider this decision if the optional stack cannot satisfy supported Python
and platform policy, materially destabilizes dependency resolution, cannot run
offline, exposes uncontrolled global state/parallelism, or cannot provide the
diagnostics required by B6.
