# M7 Verification Loop

## Objective and authority

- Requirement: `docs/MILESTONE_7.md`
- User outcome: plotsalot 1.0 has an explicit compatibility boundary, stable
  public API/schema promise, resolved robust-meta calibration finding, and
  reproducible release evidence.
- Invariants: owned Polars/NumPy boundaries, exact analysis/render identity,
  atomic failure, no fallback, bounded deterministic work, no R/network runtime,
  and separate statistical and release approval.
- Non-goals: every R argument/model class, arbitrary layers, pixel identity,
  inferred subjects, partial grouped output, and generic Bayesian/model-fitting
  frameworks.
- Risk class: high-risk statistical and public-compatibility boundary.
- Implementation owner: Codex.
- Accountable approver: Joshua Myers for product/statistical and final release
  decisions; Joshua Myers is the confirmed independent reviewer.
- Starting revision: `f65629d`, the first commit containing the M7 entry
  artifacts; entry decisions were approved on 2026-09-15.

## Rubric

| Dimension | Weight or blocking severity | Decision evidence | Pass threshold |
|---|---|---|---|
| 22-export compatibility closure | Blocking | Machine ledger, pinned inventory, CI validation, reviewed gap dispositions | Exact export set; no duplicate/missing disposition; owner approves M7-D1 |
| Robust-meta calibration resolution | Blocking | Locked mapping/confirmation artifacts, independent calculation, finding ledger | No unapproved threshold/seed change; blockers closed; owner approves final disposition |
| API and schema stability | Blocking | Public manifest, golden serialization, schema/error/migration tests | Every in-scope public name and emitted variant classified and tested; owner approves M7-D3 |
| Statistical correctness and refusal behavior | Blocking | Oracles, analytic cases, simulation, fault injection, atomic/group/resource tests | No silent fallback, population drift, partial result, or unresolved material finding |
| Packaging, security, and reproducibility | Blocking | Check/audit/build, artifact inspection, isolated installs, SBOM/checksums, secret scan | All gates pass on exact candidate; no credential/private/machine path leakage |
| Documentation and operability | Major | User guide, compatibility, limitations, migration, security, release/recovery docs | All supported claims match tested behavior; recovery path is explicit |

## Budget and stopping rules

- Maximum verification iterations per delivery track: four evidence-changing
  passes, excluding a single harness smoke.
- Calibration ceiling: the cases, workers, runner-hours, and retained size in
  `docs/M7_CALIBRATION_PLAN.md`.
- Pass rule: all blocking rubric rows pass and all major findings are corrected
  or explicitly accepted by their accountable owner.
- Diminishing-return rule: stop when a pass produces no new evidence class and
  no finding disposition changes.
- Escalation trigger: any statistical-method change, 1.0 scope expansion,
  schema break, calibration undercoverage, dependency/license issue, or proposed
  weakening of atomic/no-fallback behavior.
- Abort condition: evidence identity cannot be reproduced, locked inputs or
  seeds changed after inspection, credentials/private data appear, or the exact
  candidate cannot pass clean build/install gates.

## Planned evidence-changing passes

| # | Implemented slice | New evidence/context | Required finding treatment | Focused/full gates |
|---:|---|---|---|---|
| 1 | M7A inventory and contract | 22-export machine ledger, current public names/signatures, schema and CLI inventory | Correct omissions/duplicates/stale milestone claims against approved M7-D1/D3 boundaries | Ledger policy tests, docs links, lint/type/test |
| 2 | M7B statistical boundary | Locked mapping and confirmation artifacts plus independent likelihood/coverage review | Retain every cell and failure; owner chooses reaffirm/replace/reclassify | Focused calibration verifier, M6C tests, oracle checks |
| 3 | M7C adversarial stability | Golden schema mutations, invalid/degenerate/resource/group faults, old-call compatibility, migration replay | Close silent breaks and unstable message-only contracts | Full `make check`, audit, schema/API manifest checks |
| 4 | M7D release candidate | Clean source build, sdist/wheel contents, isolated 3.11/3.12 installs, public smoke, benchmarks, docs and independent review | No blocker or unowned major risk; separate statistical and release sign-off | Full production/reproducibility and release-readiness gates |

## Finding disposition

| ID | Location and evidence | Consequence | Severity | Current disposition | Acceptance check | Owner |
|---|---|---|---|---|---|---|
| M7-F001 | `docs/evidence/M6C_PASS2_VERIFICATION.md`; M7 mapping and confirmation artifacts | Current provisional rule depends on unknowable generating `tau`; one mapping fit failed ambiguously | Blocking | Closed; Joshua Myers independently reviewed and approved experimental reclassification for 1.0 on 2026-09-15 | Machine ledger, migration guidance, and public manifest identify the experimental boundary | Joshua Myers |
| M7-F002 | `PROJECT_BRIEF.md` previously retained resolved 0.1.1/security questions | Planning state could misdirect M7 work | Major | Correct in M7 entry slice | Brief names only current decisions | Implementation owner |
| M7-F003 | Retained stability fixtures were incomplete | Downstream compatibility promise was only partly enforceable | Blocking | Closed in M7C; 51 goldens cover 25 result types and 49 discriminator triples, with schema mutation, error/refusal, migration replay, and semantic-axis checks | `docs/evidence/M7C_VERIFICATION.md` and `tests/test_m7c_stability.py` | Joshua Myers |
| M7-F004 | Deferred capability prose spanned several milestone-era sections | Older text could call an implemented M6 mode deferred | Major | Closed; M7A pass 2 independently accepted 2026-09-15 | Ledger/prose reconciliation tests and review | Product owner |

## Exit

- Stop reason: the fourth and final evidence-changing pass is complete; repeat
  only for a changed candidate or a new reviewer finding.
- Current rubric result: all technical rows pass for the 1.0.0 candidate. The
  public surface, robust-meta exception, serialized variants, schemas, error
  inventory, migration replay, semantic axes, artifact contents, and isolated
  Python 3.11/3.12 installs are retained or machine checked.
- Full quality gate: passed for the M7D candidate and remains enforced in CI and
  the stable-tag release workflow.
- Accountable review: Joshua Myers independently reviewed and accepted the exact
  `e682d9d` 1.0.0 technical candidate on 2026-09-15; M7 and the 1.0 product gate
  are complete.
- Remaining delivery work: tagging, the protected PyPI deployment approval,
  publication, and post-publication hash/install verification are separate from
  the completed implementation and acceptance evidence.
