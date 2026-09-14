# Agentic Verification Loop: M1 shared contracts

## Objective and authority

- Requirement: `docs/MILESTONE_1.md`
- User journey: analyze a supported Polars column, inspect a portable typed
  result, render it, then customize the returned Matplotlib objects.
- Invariants and non-goals: recorded in `docs/MILESTONE_1.md`.
- Risk class: material; statistical sample identity and public contracts.
- Implementation owner: technical lead.
- Accountable statistical/product/legal approver: Joshua Myers; decisions were
  recorded after the technical loop in M0 sign-off and ADR-010.
- Starting revision: `4270c7536034d7096f081a4212463fa4c03c4819`, clean `main`.

## Rubric

| Dimension | Blocking severity | Decision evidence | Pass threshold |
|---|---|---|---|
| Shared-contract behavior | Blocking | Focused contract and boundary tests | All declared M1 behaviors pass |
| Statistical/sample correctness | Blocking | Existing analytic fixture plus separation and reconciliation tests | No regression or sample divergence |
| Data integrity | Blocking | Immutability, null, non-finite, dtype, and caller-mutation tests | All pass |
| Maintainability | High | Import-boundary and adversarial architecture review | No open high finding |
| Artifact/repository quality | Blocking | Full check, audit, build, and isolated wheel smoke | All applicable gates pass |

## Budget and stopping rules

- Maximum iterations: three evidence-changing passes.
- Pass rule: every blocking check passes and no critical/high finding remains.
- Diminishing-return rule: stop after a full unchanged pass adds no finding.
- Escalation trigger: statistical-method ambiguity, license selection, or owner
  approval is required.
- Rollback condition: public walking-skeleton behavior or analytic values regress.

## Iterations

| # | Implemented slice | New evidence/context | Findings | Decision and correction | Gates |
|---:|---|---|---|---|---|
| 0 | Baseline only | Existing M0 implementation | M1 contracts not yet separated | Proceed with bounded M1 implementation | `make check`: 39 tests passed |
| 1 | Initial shared contracts | Focused result/data/plot tests | Analysis and Matplotlib still shared modules; read-only array flag reversible | Split dependency boundaries and use immutable backing storage | 49 tests passed |
| 2 | Separated modules and validated states | Import-boundary, mutation, schema, and invalid-state tests | Repository gate lacked a coverage floor | Pin coverage and enforce measured baseline | 51 tests passed; new modules 97–100% |
| 3 | Production gate | Audit, build, isolated wheel smoke, adversarial review | No open technical blocker | Stop for diminishing returns and M0 domain escalation | Full gate passed |

## Exit

- Stop reason: technical rubric passed; milestone closeout escalated at the M0
  entry gate.
- Rubric result: no open technical blocking finding.
- Full quality gate: 51 tests, 79% branch coverage, strict typing and lint pass.
- Artifact evidence: wheel/sdist build and isolated headless wheel smoke pass.
- Post-loop closeout: M0 oracle/benchmark evidence passes and Joshua Myers
  supplied the statistical and product/legal approvals on 2026-09-14.
- Durable facts promoted to `docs/CONTRACTS.md`, contract tests,
  `docs/evidence/M1_VERIFICATION.md`, and `PROJECT_MEMORY.md`.
