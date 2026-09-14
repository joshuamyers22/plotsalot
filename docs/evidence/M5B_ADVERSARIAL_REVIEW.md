# M5B Adversarial Review

- Date prepared: 2026-09-14
- Review target: M5B frequentist meta-analysis technical core
- Preparation: implementation self-review
- Independent reviewer: Joshua Myers
- Status: Independently reviewed and accepted, 2026-09-14

## Findings found and corrected or dispositioned

| ID | Finding | Severity | Disposition | Acceptance evidence |
|---|---|---|---|---|
| M5B-AR-001 | Ordinary coefficients could be pooled merely because standard errors are present | Blocking | Require the exact `meta_analytic_effect=True` selector plus four explicit scale/estimand declarations and independent dependence | explicit-mode and invalid-option tests |
| M5B-AR-002 | Null or invalid studies could be silently dropped and change the pooled population | Blocking | Reject any null, duplicate, non-finite, nonpositive, or unrepresentable participating value; retain source order and exact count | owned-boundary and adversarial input tests |
| M5B-AR-003 | REML could drift under very small or large effect units | Blocking | Normalize around the declared null before solving and transform tau, pooled values, and intervals back to the supplied scale | scale-equivariance, independent likelihood, and 300-case development fuzz evidence |
| M5B-AR-004 | Numerical difficulty could silently select fixed-effect or another tau estimator | Blocking | Use bounded deterministic bracketing/Brent solving, retain convergence metadata, and raise on failure with no fallback | boundary, positive-root, and bracket-expansion tests |
| M5B-AR-005 | A pooled confidence interval could be presented as prediction | Blocking | Use distinct typed targets/methods/layers; require five studies; retain an explicit absence reason below that threshold | 3/5-study and result-construction tests |
| M5B-AR-006 | Serialized weights or pooled values could contradict one another | Blocking | Frozen result constructors reproduce variances, weights, normalization, contributions, pooled mean/variance/test, df, and boundary relationships | cross-field mutation suite and JSON-safe schema checks |
| M5B-AR-007 | `only_significant` could alter study membership or pooling | Blocking | Compute and retain every study before applying label visibility; renderer consults the display policy only for text | renderer label and result-count tests |
| M5B-AR-008 | Large label/point requests could create unbounded work or silent sampling | Blocking | Default to 500 studies/points and 200 labels, cap explicit overrides at 1,000, and fail before figure creation | ceiling and invalid-resource tests; retained 500-study grid |
| M5B-AR-009 | Upstream parametric wording could imply inferential equivalence | Blocking, closed | Classify Python M5B as adapted because pooled inference uses modified Hartung–Knapp rather than upstream normal inference | raw pinned-ggstatsplot object plus base-R and metafor normal/`adhoc` oracle comparisons |
| M5B-AR-010 | A meta-only implementation cannot yet prove the shared M5A/M5B result/renderer promise | Blocking, closed | Implement both modes through the shared schema-v1 result family, public dispatch, semantic renderer, extraction, and composition contracts | combined M5 tests, oracle, and production gate |

## Independent review checklist

The reviewer should verify study identity and row preservation, estimand/scale/
direction/units/null declarations, normal study inference, REML score and
restricted-likelihood behavior, numerical normalization, convergence limits,
random weights/contributions, modified Hartung–Knapp inference, prediction
threshold/target, Q/I-squared/tau records, zero heterogeneity, dominant studies,
schema contradictions, renderer traceability, label-only filtering, resource
ceilings, compatibility wording, independent fixtures, the retained benchmark,
and isolated-wheel behavior.

## Independent reviewer decision

Joshua Myers independently reviewed the M5B implementation and evidence and
accepted the technical candidate on 2026-09-14. No new M5B finding was reported.
M5B-AR-010 closed when M5A proved the shared result and renderer contract. Joshua
Myers accepted the final combined M5/`0.3` candidate on 2026-09-14.
