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
- At adoption, exact engine/version selection remained blocked until M6B method
  design. The later approved M6B and M6C clarifications select the locked core
  for their bounded methods; this ADR still does not approve PyMC, ArviZ, or a
  general sampler.
- General Bayesian regression/model execution remains outside plotsalot.

## Approved M6B clarification

The B6 proposal in `../M6B_STATISTICAL_METHODS.md` selects existing locked
NumPy/SciPy primitives for M6B closed-form marginal likelihoods, adaptive
one-dimensional quadrature, and bounded randomized quasi-Monte Carlo of exact
conjugate posteriors. It proposes no PyMC/ArviZ extra or MCMC path for M6B.

For this proposal, randomized quasi-Monte Carlo is treated as a core numerical
integration algorithm, not as the optional fitted-model sampling engine covered
by the second decision bullet above. It still receives owned seeds, independent
replicates, approximation diagnostics, work ceilings, and no-retry/no-fallback
behavior. Joshua Myers approved this clarification with B6 on 2026-09-15. A
future M6C MCMC or general posterior-sampling path would still require the
isolated optional extra.

## Approved M6C clarification

The B5 record in `../M6C_STATISTICAL_METHODS.md` requires no sampler. Reported
posterior coefficient summaries accept neither fitted models nor draws, and the
Bayesian aggregate normal-normal hierarchy integrates its Gaussian mean
analytically and its single heterogeneity coordinate by bounded adaptive
Gauss-Kronrod quadrature. M6C therefore uses the locked NumPy/SciPy core, adds
no optional Bayesian dependency or RNG, and retains the accepted diagnostic,
work, atomic-failure, and no-fallback boundaries. Joshua Myers approved this
clarification with B5 on 2026-09-15.

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
