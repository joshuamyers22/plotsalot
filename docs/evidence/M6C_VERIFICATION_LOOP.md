# M6C Verification Loop

## Objective and authority

- Requirement: `docs/MILESTONE_6.md`
- Approved authority: `docs/M6C_STATISTICAL_METHODS.md`
- Scope: robust/posterior coefficient summaries, robust/Bayesian independent
  aggregate meta-analysis, common coefficient rendering/results, and `0.4`
  closeout evidence
- Invariants: explicit mode; strict Polars profiles; declared additive scale and
  independent study population; fixed robust model; proper Bayesian priors;
  bounded deterministic work; immutable typed results; no fitting, retry,
  fallback, or result-time inference
- Risk class: high-risk statistical reporting and numerical inference
- Product/statistical owner: Joshua Myers
- Implementation owner: Codex
- Independent reviewer: Joshua Myers
- Starting revision: `d8f0485520fa6b5dd883eecba9504b0f899e2447`
- Starting worktree: clean and synchronized with `origin/main`
- Entry approval: Joshua Myers, 2026-09-15
- Pass budget: three evidence-changing implementation passes after approval

## Rubric

| Dimension | Severity | Decision evidence | Pass threshold |
|---|---|---|---|
| Summary-input identity | Blocking | Approved R4-C/B5-C; profile, provenance, mutation, and round-trip tests | Every reported field, interval kind, probability partition, source, identity, and exclusion reconciles; no fabricated inference |
| Robust statistical identity | Blocking | Approved R4-M; independent likelihood/score/profile checks and contamination validation | Fixed Student-t4 likelihood, MLE, interval/test, weights, heterogeneity, warnings, and unavailable quantities match the approved record |
| Bayesian statistical identity | Blocking | Approved B5-M; high-precision/bayesmeta checks and calibration | Likelihood, proper priors, BF orientation, posterior/prediction targets, sensitivities, and small-study warnings match the approved record |
| Numerical/resource integrity | Blocking | Optimization/quadrature diagnostics, replay, work preflight, and injected faults | Tolerances and work reconcile; no ambiguity, hidden retry, work growth, seed, sampler, fallback, or partial result |
| Result/render integrity | Blocking | Mode-version schemas, constructor mutation, semantic injection, extraction/composition | Every displayed value comes from one valid immutable result and carries correct confidence/credible/prediction vocabulary |
| Compatibility/license | Blocking | Pinned upstream objects, independent reference code, audit and deliberate-difference tests | Every touched upstream behavior is dispositioned; no GPL source enters the MIT tree or package artifacts |
| Production/maintainability | Blocking | Check/audit/build/wheel/oracle/calibration/benchmark gates | Full gate passes; each new M6C analysis/result module reaches at least 90% branch coverage; accepted paths meet regression limits |

## Budget and stopping rules

- Maximum verification passes: three after R4/B5 approval.
- A pass must add a coherent implementation slice and materially new formula,
  numerical, integration, calibration, resource, or adversarial evidence.
- Stop before inferential implementation until all six entry rows in
  `M6C_SIGNOFF.md` are approved or explicitly revised.
- Stop on an ambiguous profile, source, scale, dependence assertion, robust
  likelihood, tuning, optimum, score/KKT condition, interval target, prior,
  evidence orientation, prediction target, sensitivity set, tolerance, work
  unit, or non-applicability reason.
- Stop on unexplained oracle drift, contamination/calibration failure, GPL
  source contamination, fallback, non-finite output, result/render divergence,
  or classical-result regression.
- A failed held-out simulation cell is not retuned, removed, pooled with another
  cell, or rerun under a different seed. Repeated review against unchanged
  evidence is not another pass.

## Planned iterations

| # | Planned slice | Required new evidence | Gate state |
|---:|---|---|---|
| 0 | Method-entry audit, R4/B5 proposal, sign-off ledger, and verification contract only | Published tMeta/NNHM review, GPL/MIT boundary, inherited M5/M6 constraints, exact pending decisions | Entry gate passed 2026-09-15; implementation authorized |
| 1 | R4-C/B5-C strict table profiles and schema-v2/v3 result variants | Hand calculations, invalid/mixed profiles, probability partitions, source/order/mutation/JSON tests; v1 serialization stability | Technical gate passed; accepted by Joshua Myers 2026-09-15 |
| 2 | R4-M/B5-M native engines and complete statistical results | Independent high-precision/R oracles, multistart/profile/quadrature faults, invariance, contamination, SBC, work/limit evidence | Technical gate passed 2026-09-15 with provisional owner-approved `k<20 OR tau=0` conservative rule; M7 review required |
| 3 | Shared renderer/API/extraction/composition, retained benchmark, docs, adversarial and production gates | Injection/artist identity, cross-mode composition, package audit/build/wheel/oracle/benchmark/reproducibility evidence | Technical gate passed; independently reviewed and accepted 2026-09-15 |

## Entry findings and dispositions

| ID | Finding | Consequence | Severity | Approved disposition | Acceptance check | Owner |
|---|---|---|---|---|---|---|
| M6C-E-001 | Upstream robust/Bayesian coefficient inputs do not establish a safe Python model/draw adapter | Broad dispatch could mislabel models, priors, covariance, or evidence | Blocking | Accept only strict caller-reported summary tables and mark provenance unverified | Fake-object/draw rejection; reserved-column and source mutation tests | Product/statistical owner |
| M6C-E-002 | “Robust meta-analysis” does not name one estimand or inference rule | Implementations could silently change tuning, exclude studies, or fall back | Blocking | Fix Student-t4 hierarchy, ML/profile inference, latent weights, study floor, and absent Q/I2/prediction | Formula/oracle, multistart, displacement, boundary, and no-fallback tests | Statistical owner |
| M6C-E-003 | A Bayesian heterogeneity scale is outcome-dependent and BF requires proper priors | A default/data-derived scale could dominate few-study results or make marginal likelihood undefined | Blocking | Require caller-supplied proper mean/tau scales and four sensitivity fits | Prior-predictive docs, BF/quantile oracle, small-study and scale tests | Statistical owner |
| M6C-E-004 | M6C models need no general sampler | Adding MCMC would expand dependencies, diagnostics, RNG, and failure surfaces without statistical need | Material | Use analytic conditional calculations and bounded one-dimensional quadrature in the existing core | Python 3.11+ lock, no-extra import, offline wheel, no-seed tests | Architecture owner |
| M6C-E-005 | The reviewed tMeta reference code is GPL while plotsalot is MIT | Copying implementation source could violate the accepted license posture | Blocking | Treat source only as external black-box evidence; independently derive implementation from published mathematics | License audit, provenance review, source/hash exclusion from artifacts | Product/implementation owners |

## Current state

- Status: complete and accepted by Joshua Myers, 2026-09-15
- Verification passes used: three of three implementation passes
- Pass 1 evidence: `M6C_PASS1_VERIFICATION.md`
- Pass 2 evidence: `M6C_PASS2_VERIFICATION.md` and
  `m6c-pass2-calibration.json`
- Pass 3 evidence: `M6C_VERIFICATION.md` and `M6C_ADVERSARIAL_REVIEW.md`
- Independent review and product-owner acceptance: Joshua Myers, 2026-09-15
- Preserve the boundary finding for mandatory M7 review.
- No further implementation pass is authorized absent a documented review
  finding and owner disposition.
- Next authority gate: combined M6/`0.4` review and product-owner acceptance
