# M6C Pass 1 Verification

- Date: 2026-09-15
- Scope: R4-C/B5-C reported coefficient-summary boundaries and result variants
- Starting revision: `921ea52`
- Gate: implementation-owner technical gate passed; independent review pending

## Implemented slice

Pass 1 adds the explicit `type="robust"` and `type="bayes"` coefficient-analysis
dispatch, strict Polars `robust_interval` and `posterior_summary` profiles,
owned immutable arrays, caller-reported-unverified provenance records, and
schema-v2/v3 result variants. Structured identity, intercept exclusion, stable
sorting, source/display positions, declarations, nulls, interval semantics,
warnings, and resource limits reconcile in immutable constructors.

The robust and Bayesian aggregate meta-analysis engines still fail before work
with a pass-2 message. Rendering a reported-summary analysis still fails before
figure construction with a pass-3 message. No fitted model, posterior object,
draw, chain, artifact, Bayes factor, standard error, test statistic, degrees of
freedom, p-value, or reconstructed significance enters either summary profile.

## Independent hand fixtures

The retained three-row robust fixture reports points `(2.0, 0.8, -0.2)` inside
confidence intervals `(1.5, 2.5)`, `(0.4, 1.2)`, and `(-0.6, 0.1)`. Excluding
the marked intercept retains original source positions `(1, 2)`; descending
point order is `dose, age`. The implementation copies these reported values and
performs no test reconstruction.

The retained posterior fixture reports medians `(2.0, 0.75, -0.15)` inside its
three credible intervals. Its directional partitions are `(1,0,0)`,
`(0.98,0.02,0)`, and `(0.25,0.75,0)`, each summing exactly to one. The boundary
fixture accepts an absolute partition deviation of `5e-13` and rejects `2e-12`,
matching the approved `1e-12` tolerance. Ascending order after intercept
exclusion is `age, dose`, while source order remains `dose, age`.

## Automated evidence

- `make check`: passed; 243 tests, zero failures; strict Ruff and Pyright clean.
- Full suite coverage: 91% with branch measurement.
- New `coefficient_summary_analysis.py`: 97% branch coverage, exceeding the 90%
  M6C module threshold.
- M6C pass-1 tests: 20, covering incomplete/mixed/reserved profiles, numeric and
  null failures, interval containment, the probability tolerance, Unicode and
  control-character provenance, identity/intercept audits, order/permutation,
  resource preflight, immutable source arrays, constructor mutations, atomic
  pass-2/pass-3 deferrals, and JSON round trips.
- Schema-v1 stability: the canonical estimate-only payload retains SHA-256
  `8b2766c45d306baaa27a8fed55155af3b17760c140ea294d31cf56ba6c954170`.
- `schemas/coefficient-result.schema.json` remains a strict union and adds exact
  robust-v2 and posterior-v3 discriminators without changing the v1 branches.

## Gate disposition

Pass 1 satisfies its implementation-owner technical criteria. This record does
not constitute independent review, M6C acceptance, M6/`0.4` acceptance, or
authorization to skip the approved engine and integration passes. Pass 2 is the
next gate.
