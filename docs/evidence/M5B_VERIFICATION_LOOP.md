# M5B Verification Loop

## Objective and authority

- Requirement: `docs/MILESTONE_5.md`
- Scope: independent aggregate study effects, frequentist random-effects meta-
  analysis, and shared coefficient rendering
- Risk class: high-risk statistical reporting
- Product/statistical owner: Joshua Myers
- Implementation owner: Codex
- Independent reviewer: Joshua Myers
- Starting revision: `58f9f2f`
- Pass budget: three evidence-changing passes after method approval

## Iterations

| # | Implemented slice | New evidence/context | Finding and disposition | Gate state |
|---:|---|---|---|---|
| 0 | Method-entry audit only | Pinned upstream REML/normal behavior, official metafor REML and Knapp–Hartung guidance, Statsmodels meta-analysis implementation, Cochrane prediction-interval guidance | MA1–MA4 introduced scale/independence, tau-squared, pooled/prediction, heterogeneity, convergence, and boundary choices; Joshua Myers approved them without revision on 2026-09-14 | Entry gate complete |
| 1 | Owned study boundary, REML/Hartung–Knapp analysis, typed result/schema, semantic forest renderer, extraction/composition, tests, and retained benchmark | Closed-form equal-variance case; independent restricted-likelihood optimizer; boundary, scale, bracket, contradiction, rendering, and failure tests; 300-case development fuzz audit; 3/10/100/500-study five-sample grid; check/audit/build/offline-wheel smoke | Corrected ambiguous participating fields, representability guards, strict significance threshold, hard override ceilings, and result cross-field reconciliation. M5-specific R evidence and shared M5A proof remain open | Python technical core passes; track incomplete |
| 2 | Pinned-R meta oracle and adaptation check | Raw pinned-ggstatsplot object; independently solved base-R REML and modified-Hartung–Knapp fields; pinned metafor 5.0-1 normal and `adhoc` references; hashed manifest | Separated the strict base-R score-root comparison from metafor's lower-precision iterative tau estimate and explicitly proved that approved pooled inference differs from upstream normal inference. Shared M5A proof and independent review remain open | M5B technical evidence passes; track incomplete |

## Current state

- Status: M5B technical candidate independently reviewed and accepted; shared
  M5A integration passes
- Technical implementation: M5B core accepted, 2026-09-14
- Milestone outcome: combined gate and final M5/`0.3` acceptance complete
