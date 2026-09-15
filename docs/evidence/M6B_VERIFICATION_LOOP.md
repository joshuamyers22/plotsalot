# M6B Verification Loop

## Objective and authority

- Requirement: `docs/MILESTONE_6.md`
- Scope: Bayesian univariate, association/matrix, independent/repeated
  comparison, categorical, and existing grouped surfaces
- Invariants: explicit mode and priors; reconciled immutable samples; numeric
  BF10 orientation; typed posterior summaries; bounded native computation;
  owned identity-keyed randomness; no retry or fallback; result-only rendering
- Non-goals: general Bayesian modeling, MCMC, custom priors, partial correlation,
  non-normal continuous likelihoods, paired categorical analysis, coefficients,
  and meta-analysis
- Risk class: high-risk statistical reporting with numerical approximation
- Product/statistical owner: Joshua Myers
- Implementation owner: Codex
- Independent reviewer: Joshua Myers
- Starting revision: `d4e6ccd`
- Starting worktree: clean and synchronized with `origin/main`
- Entry approval: Joshua Myers, 2026-09-15
- Pass budget: three evidence-changing passes after entry approval

## Rubric

| Dimension | Severity | Decision evidence | Pass threshold |
|---|---|---|---|
| Bayesian statistical identity | Blocking | Approved B1–B4; analytic/high-precision/oracle/calibration artifacts | Every likelihood, prior, posterior target, hypothesis, BF orientation, and interval matches the approved record |
| Numerical and RNG integrity | Blocking | Approved B6; quadrature/RQMC replay, tolerance, work, and fault tests | All diagnostics pass; exact locked replay; no hidden retry, work growth, or fallback |
| Sample/family integrity | Blocking | Existing audits plus grouped/matrix/comparison/categorical tests | Samples, subjects, groups, pairs, categories, margins, hypotheses, and directions reconcile exactly |
| Result/render integrity | Blocking | Schema mutation and semantic injection tests | Every displayed value comes from a valid typed result; rendering performs no inference or RNG work |
| Compatibility/failure behavior | Blocking | Pinned source audit, deliberate-difference and negative tests | Every touched upstream behavior is dispositioned and every invalid/failed computation is atomic |
| Production/maintainability | Blocking | Check, audit, build, wheel, oracle, calibration, benchmark gates | Full gate passes and every new Bayesian domain module reaches 90% branch coverage |

## Budget and stopping rules

- Maximum verification passes: three after B1–B6 approval.
- A pass must add a coherent implementation slice plus materially new analytic,
  numerical, integration, calibration, performance, or adversarial evidence.
- Stop before inferential implementation until every B1–B6 sign-off row is
  approved or explicitly revised.
- Stop on an ambiguous prior, hypothesis, BF direction, sampling plan, repeated
  covariance, contrast direction, interval target, numerical tolerance, seed
  identity, work unit, or diagnostic rule.
- Stop on unexplained oracle drift, sensitivity/orientation failure, calibration
  failure, silent data/hypothesis loss, fallback, non-finite output, result/render
  divergence, or resource bypass.
- Repeated review against unchanged evidence is not another pass.

## Iterations

| # | Implemented slice | New evidence/context | Finding and disposition | Gate state |
|---:|---|---|---|---|
| 0 | Method-entry audit and proposal only | Pinned ggstatsplot/statsExpressions/BayesFactor paths; accepted ADR-006; supported Python/locked NumPy-SciPy boundary; current sampling-stack compatibility review | Upstream JZS/sampling behavior does not define plotsalot's priors, bounded work, result diagnostics, or supported-Python contract. B1–B6 define explicit adapted models and a native exact/quadrature/RQMC engine; Joshua Myers approved them without revision | Entry gate passed 2026-09-15; implementation authorized |
| 1 | B1/B2 shared schema-v3 results, exact NIG one-sample/dot, and exact correlation/scalar-matrix quadrature | Analytic location/scale and sign symmetries; constant-sample, perfect-correlation, sensitivity, mutation, render-injection, and matrix-family tests | A direct left-tail quadrature over a remote negative mode initially lost posterior mass; mode-aware left/right integration resolved the defect and the sign-reversal invariant now passes | Core exact/quadrature gate passed |
| 2 | B3/B4 independent and complete-block comparisons plus fixed-total/fixed-row categorical inference | Common-mean versus cell-mean exact marginal likelihoods; Helmert reconstruction and Savage–Dickey pair evidence; deterministic eight-scramble replay; affine invariance; zero-cell and paired-deferral tests | Broad union annotations leaked Bayesian fields into legacy callers, and an off-diagonal matrix cell initially allowed a partial posterior/evidence pair. Base-contract containment and a strict both-or-neither invariant resolved both findings | Comparison/categorical/result gate passed |
| 3 | Existing grouped surfaces, schema/export/docs integration, adversarial mutation coverage, retained performance/work grid, and full production gate | Collision-safe typed group/target seed identities; target-level RQMC diagnostics; conservative aggregate preflight before quadrature or grouped QMC generation; atomic grouped smoke; 223-test full suite; 91% total coverage; Bayesian engine/result modules at 92%/90%; benchmark verifier; audit/build/wheel smoke | No unresolved implementation-owner finding remains. Independent statistical/adversarial review is still required and is not self-approved | Technical candidate complete; independent gate open |

## Finding disposition

| ID | Location/evidence | Consequence | Severity | Proposed disposition | Acceptance check | Owner |
|---|---|---|---|---|---|---|
| M6B-E-001 | Pinned upstream delegates across BayesFactor/correlation helpers with family-specific defaults | A generic `type="bayes"` would hide different priors, hypotheses, and sampling plans | Blocking | Approve explicit B1–B4 models and retain full method identity | Schema, oracle-difference, prior mutation, and orientation tests | Statistical owner |
| M6B-E-002 | Latest PyMC/ArviZ releases reviewed for the entry proposal require Python 3.12 while plotsalot supports 3.11 | Making that stack mandatory would silently narrow supported Python or fragment M6B behavior | Blocking | B6 proposes the locked NumPy/SciPy core for M6B; reserve optional sampling engine for a later approved M6C need | 3.11+ lock matrix and minimal-wheel smoke | Architecture owner |
| M6B-E-003 | Posterior derived effects lack one common closed form | Naive Monte Carlo can hide error, change with order, or grow work without bound | Blocking | B6 specifies fixed RQMC replicates, nested diagnostics, identity seeds, preflight work, and no retry | Replay, alternate-seed, tolerance, ceiling, and fault tests | Architecture/statistical owner |
| M6B-E-004 | Upstream captions apply qualitative BF categories | Threshold language can imply a decision rule that was not approved | Material | B1 retains log BF10 and renders only a bounded numeric value | Renderer injection and extreme-BF tests | Product/statistical owner |

## Current state

- Status: independently reviewed and accepted; M6B complete
- Verification passes used: three of three implementation passes
- Acceptance: Joshua Myers, 2026-09-15
- Still not authorized: R4/M6C, final M6, or `0.4`
