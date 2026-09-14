# M2 Adversarial Review

- Date prepared: 2026-09-14
- Review target: M2 release candidate
- Preparation: implementation self-review followed by accountable review
- Independent reviewer: Joshua Myers
- Status: Approved

## Review checklist

The independent reviewer should verify method identity, missing-data policy,
typed-result invariants, renderer/result traceability, grouped atomicity,
multiplicity scope, workload ceilings, unsupported-input failure, oracle
interpretation, package isolation, and compatibility wording.

## Findings already found and corrected

| ID | Finding | Severity | Correction | Acceptance evidence |
|---|---|---|---|---|
| M2-AR-001 | Group identities were initially stringified, making integer `1` ambiguous with string `"1"` | Blocking | Preserve finite JSON scalar type and reject unsupported identity types | `test_numeric_group_identity_keeps_its_json_scalar_type`; grouped record guards |
| M2-AR-002 | Dot labels and their rendered artists had no explicit bound | Blocking | Preserve scalar label identity, cap labels at 200 by default, expose an explicit positive override, and serialize the ceiling | dot boundary/resource tests and result schema |
| M2-AR-003 | The first oracle verifier required a Student statistic for exact-perfect correlation even though the approved contract omits it | Blocking | Treat the R finite approximation as a declared adaptation while retaining coefficient, p, interval, count, and adjustment checks | `tools/verify_oracle.py`; perfect-correlation test |
| M2-AR-004 | A bare string could be interpreted as a sequence of matrix column names | Required | Require a list or tuple of non-empty column-name strings | correlation invalid-input tests |
| M2-AR-005 | Matrix captions always called p-values adjusted, including `p_adjust="none"` | Required | Label raw p-values as `p` and Holm values as `Holm-adjusted p` | matrix renderer caption tests |
| M2-AR-006 | Merely near-perfect values could be collapsed to the exact-perfect boundary | Blocking | Require an exact clipped coefficient of `+/-1`; retain finite inference otherwise | correlation implementation and near/perfect fixtures |

## Open review item

| ID | Finding | Severity | Disposition | Acceptance check | Owner |
|---|---|---|---|---|---|
| M2-AR-007 | No independent reviewer was initially assigned | Blocking for milestone closeout | Closed: Joshua Myers reviewed and approved the release candidate on 2026-09-14 | Reviewer name, review date, decision, and finding dispositions are recorded here | Joshua Myers |

## Independent reviewer decision

Joshua Myers reviewed the M2 release candidate and approved all implementation,
verification, compatibility, oracle, benchmark, and finding dispositions on
2026-09-14. No additional findings were recorded. The reviewed candidate is the
working tree atop `f6a8adb`, identified by the wheel, oracle-manifest, and
benchmark hashes in `M2_VERIFICATION.md`.
