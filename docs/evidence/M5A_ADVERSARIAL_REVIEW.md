# M5A Adversarial Review

- Date prepared: 2026-09-14
- Review target: M5A coefficient-table and fitted-OLS technical candidate
- Preparation: implementation self-review
- Independent reviewer: Joshua Myers
- Status: Accepted, 2026-09-14

## Findings found and corrected or dispositioned

| ID | Finding | Severity | Disposition | Acceptance evidence |
|---|---|---|---|---|
| M5A-AR-001 | Repeated term text could collapse distinct responses/components/groups | Blocking, closed | Retain structured identity fields and require the full structured key to be unique | repeated-term and duplicate-key tests |
| M5A-AR-002 | Partial inference columns could be silently treated as display-only | Blocking, closed | Resolve exactly one allowlisted table-wide profile and reject every partial combination | four-profile and partial-profile tests |
| M5A-AR-003 | Reported inference could be presented as recomputed or model-validated | Blocking, closed | Retain `reported` provenance and do not reconstruct supplied tests or intervals | authoritative reported-value and subtitle tests |
| M5A-AR-004 | Duck-typed or unsupported fitted models could enter the adapter | Blocking, closed | Require exact wrapper and exact OLS model classes; reject raw results, WLS, and unsupported covariance types | adversarial adapter tests |
| M5A-AR-005 | Aliasing, zero residual df, or invalid constant metadata could misidentify coefficients | Blocking, closed | Require full rank, positive residual df, and agreeing `k_constant`/`const_idx` metadata | rank, residual-df, and intercept tests |
| M5A-AR-006 | Sorting or intercept exclusion could detach estimates from identities | Blocking, closed | Select once, retain source/display positions and excluded structured identities, and validate analysis/result pairing | sort, exclusion, mutation, and rendering tests |
| M5A-AR-007 | Significance filtering could remove coefficients or create an unstated multiplicity claim | Blocking, closed | Filter labels only with strict unadjusted `p < alpha`; retain every coefficient record | label-policy and result-count tests |
| M5A-AR-008 | Result provenance, profile, or model fields could contradict one another | Blocking, closed | Frozen constructors cross-check source, interval, statistic, df, model distribution, positions, counts, and limits | constructor mutation suite |
| M5A-AR-009 | A large model/table could create unbounded artists or labels | Blocking, closed | Default to 500 coefficients/points and 200 labels, hard-cap overrides at 1,000, and fail before partial output | resource tests and retained 500-term benchmark |
| M5A-AR-010 | Separate coefficient/meta implementations could violate the shared M5 promise | Blocking, closed | Use one public dispatch, schema family, renderer, extraction/composition path, and shared semantic layers without weakening M5B invariants | mixed M5 tests and combined production gate |

## Independent review checklist

The reviewer should verify all four table profiles, structured key identity,
authoritative reported inference, exact class allowlist, covariance/use-t
provenance, no refit, rank/residual-df/constant checks, estimate-only behavior,
intercept exclusion, stable ordering, significance-label scope, model summaries,
resource ceilings, schema contradictions, semantic layers, R/independent
fixtures, benchmark boundaries, and isolated-wheel behavior.

## Independent reviewer decision

Joshua Myers independently reviewed the M5A implementation and evidence,
accepted the technical candidate on 2026-09-14, and reported no new finding.
All prepared findings remain closed.
