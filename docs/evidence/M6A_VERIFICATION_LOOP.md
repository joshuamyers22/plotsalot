# M6A Verification Loop

## Objective and authority

- Requirement: `docs/MILESTONE_6.md`
- Scope: robust univariate, association, independent/repeated comparison,
  matrix, and existing grouped surfaces
- Invariants: caller-selected methods; reconciled immutable samples; explicit
  20% trimmed/Winsorized estimands; owned RNG; bounded work; no fallback;
  typed-result-only rendering
- Non-goals: nonparametric methods, robust categorical/coefficient/meta paths,
  arbitrary trim values, automatic outlier removal, and general resampling
- Risk class: high-risk statistical reporting with bounded stochastic work
- Product/statistical owner: Joshua Myers
- Implementation owner: Codex
- Independent reviewer: Joshua Myers
- Starting revision: `fd9456c`
- Starting worktree: M6 contract changes uncommitted
- Entry approval: Joshua Myers, 2026-09-14
- Pass budget: three evidence-changing passes after entry approval

## Rubric

| Dimension | Severity | Decision evidence | Pass threshold |
|---|---|---|---|
| Robust statistical identity | Blocking | Approved R1–R3; analytic/reference/oracle/calibration artifacts | Every estimate/test/interval/effective count matches its approved target and tolerance |
| RNG and resource integrity | Blocking | Approved ADR-005/G6; replay/work/fault tests | Exact locked-environment replay; preflight ceilings; no hidden RNG, work reduction, or fallback |
| Sample/family integrity | Blocking | Existing audits plus robust grouped/matrix/comparison tests | Samples, subjects, groups, pairs, hypotheses, directions, and adjustments reconcile exactly |
| Result/render integrity | Blocking | Schema mutation and semantic injection tests | Every displayed number/classification originates in a valid typed result; rendering is deterministic and analysis-free |
| Compatibility and failure behavior | Blocking | Pinned source, negative tests, compatibility matrix | Every touched upstream behavior is dispositioned; invalid/degenerate/underpowered computation fails atomically |
| Production and maintainability | Blocking | Check/audit/build/wheel/oracle/benchmark gates | Full gate passes; each new M6A domain module has at least 90% branch coverage |

## Budget and stopping rules

- Maximum verification passes: three after method/architecture approval.
- A pass must add a coherent implementation slice and new evidence, an
  independent/oracle/calibration artifact, performance/resource evidence, a
  production gate, fault injection, or a genuinely different adversarial view.
- Stop before implementation until ADR-005, ADR-006, R1–R3, and G6 are approved.
- Stop on ambiguous formulas, estimands, pair directions, interval targets,
  effective samples, seed mappings, invalid replicate policy, or work units.
- Stop on calibration failure, unexplained oracle drift, silent observation or
  hypothesis loss, fallback, non-finite output, result/render divergence,
  resource bypass, or unresolved blocking finding.
- Repeated review against unchanged evidence is not a new pass and cannot
  establish independence.

## Iterations

| # | Implemented slice | New evidence/context | Finding and disposition | Gate state |
|---:|---|---|---|---|
| 0 | Method-entry audit only | Pinned ggstatsplot/statsExpressions/WRS2 signatures and bodies; existing M2/M3 data/result/render boundaries; robust-method primary references | Upstream uses hidden/global RNG, low resample defaults, hard-coded interval behavior, ordinary Pearson inference after Winsorization, and stochastic/ambiguous effects. ADR-005 plus R1–R3/G6 define explicit adapted behavior | Entry gate passed; implementation authorized 2026-09-14 |
| 1 | Shared fixed-trim kernel, R1/R2/R3 analyses, schema-v2 immutable results | Direct analytic equations, replay, scale/contamination, small/degenerate input, complete-family, and constructor mutation tests | M6A-E-001/002/003 resolved by explicit analytic/seeded methods and typed provenance; no fallback path found | Core statistical/result gate passed |
| 2 | Semantic renderers, matrix and all existing grouped surfaces, aggregate work preflight | Renderer injection/identity checks, reordered streams, atomic grouped fault, hash-seed replay, retained resource benchmark | M6A-E-004 resolved; complete work is known before draws and grouped failures return no partial result | Integration/resource gate passed |
| 3 | Pinned-R/base-R oracle, 300-case interval calibration, public compatibility/docs, full package gate | Exact oracle regeneration, byte-identical calibration replay, 199 tests/92% coverage, audit, build, offline wheel smoke, benchmark verification | No unresolved implementation-owner finding; Joshua Myers independently reviewed and reported no new finding | Technical candidate independently accepted 2026-09-14 |

## Finding disposition

| ID | Location/evidence | Consequence | Severity | Proposed disposition | Acceptance check | Owner |
|---|---|---|---|---|---|---|
| M6A-E-001 | Pinned `trimcibt` uses R global RNG and 200 bootstrap draws | Same call is not replayable and Monte Carlo resolution is weak | Blocking | Replace with deterministic analytic trimmed-location inference under R1 | Analytic/oracle distinction and replay tests | Statistical owner |
| M6A-E-002 | Pinned robust correlation applies ordinary Pearson reference inference after Winsorization | Test/interval target and effective df are inconsistent with WRS2 output | Blocking | R2 uses WRS2-style df and explicit paired percentile bootstrap interval | Independent formula plus calibration | Statistical owner |
| M6A-E-003 | Pinned comparison helpers hard-code 95% branches and mix stochastic effect estimates | Caller confidence level and effect reproducibility can diverge | Blocking | R3 uses configurable analytic tests/raw effects; standardized effect deferred | Confidence-level and repeated-seed tests | Statistical owner |
| M6A-E-004 | Upstream stochastic work has no plotsalot work/seed contract | Matrix/group calls can become unbounded or order-dependent | Blocking | ADR-005/G6 preflight total work and derive identity-keyed streams | Ceiling, order, and hash-randomization tests | Architecture owner |

## Current state

- Status: M6A complete and accepted
- Technical implementation: Complete for approved R1–R3/G6 scope
- Verification passes used: three of three
- Independent/product decision: Joshua Myers accepted, 2026-09-14
- Still not authorized by this state: R4, B1–B6, M6B, M6C, M6 closeout, or
  `0.4`
