# M2 Verification Loop

## Objective and authority

- Requirement: `docs/MILESTONE_2.md`
- User journey: create inspectable univariate, scatter, correlation-matrix, and
  grouped plot-plus-result objects from Polars data.
- Risk class: high-risk statistical reporting
- Product/statistical owner: Joshua Myers
- Implementation, visualization, and independent-review owners: Unassigned
- Starting revision: `f6a8adb`; clean local `main`, one commit ahead of origin

## Rubric

The blocking and required thresholds are defined in the M2 contract. Statistical
identity, sample integrity, result/render separation, failure behavior,
compatibility disposition, and the production gate are blocking.

## Budget and stopping rules

- Maximum three evidence-changing milestone verification passes.
- A pass must add implementation/tests, independent numerical evidence,
  retained oracle/benchmark evidence, or a meaningfully different review.
- Stop a method before implementation when its statistical specification lacks
  accountable approval.
- Abort or roll back on sample/result divergence, unexplained oracle drift,
  unbounded workloads, or a failing release gate.

## Iterations

| # | Implemented slice | New evidence/context | Findings | Decision and correction | Gates |
|---:|---|---|---|---|---|
| 0 | Contract and method-entry audit | Pinned ggstatsplot public functions, statsExpressions 2.1.1 backend, SciPy/Statsmodels contracts | U1 is already approved; U2/G1/C1/C2/G2 introduce unapproved interval, missingness, and correction choices | Record one concrete method proposal and stop statistical implementation pending Joshua Myers's approval | `make check` passes: 55 tests, 79% branch coverage, Ruff, strict Pyright |
| 1 | Approved U2/G1/C1/C2/G2 analysis, result, renderer, and grouped surfaces | Analytic Pearson case, independent Fisher/Holm calculations, sample/atomicity/schema/failure tests, serialized resource limits | Initial grouped identity stringification was ambiguous and dot-label artist growth was unbounded | Preserve scalar JSON identities, reject unsupported identity types, cap labels at 200 by default, and retain configured ceilings in results | 79 tests pass; 86% project branch coverage; new result contracts 100%; Ruff and strict Pyright pass |
| 2 | Oracle, semantic-render, and performance evidence | Pinned R 4.5.1 raw ggstatsplot outputs, base-R normalized fixtures, result-injection render tests, M2 workload grid, fresh M0 comparison | Perfect-correlation Python results intentionally omit the finite approximation R emits; initial oracle verifier incorrectly required a statistic | Treat the declared perfect boundary as an adaptation while retaining coefficient, p-value, interval, count, and Holm checks | Oracle and benchmark verification pass; 82 tests pass; fresh M0 median time changes range from -3.9% to +6.7%, below the 20% investigation threshold |
| 3 | Production and accountable closeout | Full check, audit, build, isolated-wheel smoke, adversarial finding record, Joshua Myers review | No remaining technical or statistical blocker | Accept the release candidate and stop at the three-pass budget | 83 tests pass; 86% project coverage; all new M2 domain modules exceed 90%; all production gates and accountable approvals pass |

## Current finding disposition

| ID | Evidence | Consequence | Severity | Disposition | Acceptance check | Owner |
|---|---|---|---|---|---|---|
| M2-001 | `M2_SIGNOFF.md` | New statistical code would violate the M2 entry gate | Blocking | Closed: Joshua Myers approved U2/G1/C1/C2/G2 without revision on 2026-09-14 | All sign-off rows name Joshua Myers, date, and Approved status | Joshua Myers |

## Exit state

- Status: Complete
- Technical implementation started: 2026-09-14
- Technical and accountable closeout: 2026-09-14
- Remaining uncertainty: none within the approved M2 scope
