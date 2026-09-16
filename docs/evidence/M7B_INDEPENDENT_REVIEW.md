# M7B Independent Review and Owner Disposition

- Date prepared: 2026-09-15
- Independent reviewer: Joshua Myers
- Review date: 2026-09-15
- Status: independently reviewed and approved; reclassify selected
- Mapping artifact SHA-256: `fb556565ca1d1184a1780410a78aa8444a1b3b26546147088dbde6c93f7ee076`
- Confirmation artifact SHA-256: `ea1bac057f7fb4b43b030a5f8b3b13f51d165bb073d62f7bdbf0c27ade4ecf7a`

## Reviewer checklist

The independent reviewer should verify each item against the code, retained
artifacts, and tests rather than accepting the implementation-owner summary:

- [x] Generation uses Student-t with four degrees of freedom, location `mu`,
  and scale `sqrt(standard_error^2 + tau^2)`.
- [x] Each independent case uses the declared PCG64DXSM seed root plus immutable
  scenario identity and case index, without seed reuse; reversed-grid fits are
  deterministic paired permutations rather than new stochastic cases.
- [x] Coverage uses inclusive floating-point interval endpoints and retains all
  fit failures as uncovered in the declared denominator.
- [x] The two-sided 99% Wilson calculation, undercoverage flag, and conservative
  flag match an independent calculation.
- [x] The ordered 38-cell mapping and eight-cell confirmation grids match the
  approved plan, including translation, 500-study, reversed, and log-shape
  audits.
- [x] The mapping and confirmation files match their seals and the confirmation
  records the mapping digest.
- [x] Translation audit coverage differences (`-0.0085` and `+0.0070`) are
  consistent with their joint Monte Carlo standard errors (`0.00629` and
  `0.00620`); paired reversed-grid coverage counts are identical.
- [x] The independently implemented likelihood/profile calculation in
  `tests/test_m6c_meta_analysis.py` remains consistent with the production
  estimator used by the driver.

## Evidence facts requiring disposition

- Mapping: 76,000 fits, one retained `robust_meta_ambiguous_optimum` failure,
  no undercoverage flags, and five conservative flags.
- Confirmation: 40,000 fits, no failures, no undercoverage flags, and four
  conservative flags.
- Approved version-1 rule: the mapping failure blocks reaffirmation. It may not
  be dropped, silently rerun, or waived under a new threshold.

## Owner decision

Joshua Myers independently reviewed the evidence and selected **Reclassify** on
2026-09-15. Fixed-Student-t4 robust aggregate meta-analysis remains available
but is experimental for 1.0; the rest of `ggcoefstats` remains in the stable
boundary. The accepted alternatives were:

1. **Replace**: authorize a separately specified interval, schema-impact review,
   independent reference, and new locked calibration.
2. **Reclassify**: make robust aggregate meta-analysis experimental or remove it
   from the 1.0 stable boundary while retaining the rest of `ggcoefstats`.
3. **Versioned correction investigation**: authorize diagnosis of the ambiguous
   optimum and a new experiment plan/version with new seeds; the current method
   remains blocked from reaffirmation unless that complete process passes.

The accepted rationale follows the implementation-owner recommendation. One
failure in 76,000 fits is rare, but the method's own
strict ambiguity rule correctly refuses the result, and the approved plan makes
any fit failure blocking. Reclassification preserves explicit no-fallback
behavior and keeps the stable 1.0 contract from promising a method that failed
its locked evidence gate.

This review closes the M7-D2 statistical disposition. It does not accept M7C,
the final 1.0 API/schema candidate, or the 1.0 release.
