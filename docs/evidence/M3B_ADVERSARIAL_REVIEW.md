# M3B Adversarial Review

- Date prepared: 2026-09-14
- Review target: M3B release candidate
- Preparation: implementation self-review
- Independent reviewer: Joshua Myers
- Status: Approved

## Findings found and corrected or dispositioned

| ID | Finding | Severity | Disposition | Acceptance evidence |
|---|---|---|---|---|
| M3B-AR-001 | An omitted subject identity can create silent row-index pairing upstream | Blocking | Require explicit `subject_id`; reject duplicate subject-condition cells; never infer pairing | repeated data-contract and public failure tests |
| M3B-AR-002 | Removing null values before duplicate detection could hide an ambiguous subject-condition cell | Blocking | Detect duplicates after identity validation but before numeric null removal | identified duplicate/null-order test |
| M3B-AR-003 | Pair-specific deletion could make omnibus, pairwise, and plotted paths use different subjects | Blocking | Build one complete subject block and use it for every test, summary, and path; audit incomplete rows/subjects | incomplete-block and injected-render tests |
| M3B-AR-004 | A data-dependent sphericity switch would make the primary result unstable | Blocking | Always retain raw and Greenhouse–Geisser values and make corrected p/dfs primary for 3+ conditions | independent GG and result-invariant tests |
| M3B-AR-005 | Upstream repeated effect output does not match the approved F-to-partial-omega conversion | Required | Retain the pre-approved conversion, name it, omit unsupported uncertainty, and classify it adapted | method spec, compatibility matrix, oracle disposition |
| M3B-AR-006 | Subject-path rendering can dominate memory/time at large n | Required | Default to a serialized 10,000-path ceiling with explicit override; never silently sample | resource and benchmark tests |

## Independent review checklist

The reviewer should verify subject/condition identity, duplicate precedence,
complete-block auditing, condition orientation, paired t and g-z calculations,
repeated sums of squares, Greenhouse–Geisser projection, complete paired family,
Holm scope, grouped subject scoping, renderer/result traceability, resource
ceilings, compatibility wording, and package isolation.

## Independent reviewer decision

Joshua Myers reviewed the M3B release candidate, accepted every finding
disposition above, and approved M3B on 2026-09-14. No additional findings were
recorded.
