# M7B Sign-off

- Date: 2026-09-15
- Product/statistical owner and independent reviewer: Joshua Myers
- Status: accepted; M7B complete
- Selected disposition: reclassify fixed-Student-t4 robust aggregate
  meta-analysis as experimental for 1.0

## Evidence accepted

- Locked mapping: 76,000 fits, SHA-256
  `fb556565ca1d1184a1780410a78aa8444a1b3b26546147088dbde6c93f7ee076`.
- Locked confirmation: 40,000 fits, SHA-256
  `ea1bac057f7fb4b43b030a5f8b3b13f51d165bb073d62f7bdbf0c27ade4ecf7a`.
- Mapping retained one `robust_meta_ambiguous_optimum` failure and no
  undercoverage flags. Confirmation retained no failures and no undercoverage
  flags. Reaffirmation is blocked by the approved version-1 rule.
- Joshua Myers completed the independent-review checklist and approved the
  reclassification on 2026-09-15.

## Accepted 1.0 boundary

The method selected by `meta_analytic_effect=True, type="robust"` remains
available without estimator, optimizer, interval, work, coded-failure, or
no-fallback changes. It is experimental rather than stable for 1.0.

The containing `ggcoefstats`, `analyze_ggcoefstats`, and `render_ggcoefstats`
names remain stable for supported non-experimental modes. Seven dedicated
`RobustMeta*` public types and the schema-v2 robust-meta result variant are
excluded from the stable 1.x method/serialization promise. All 144 root names
remain importable: 137 are stable candidates and seven are experimental.

## Closeout verification

The machine compatibility ledger, generated public manifest/reference,
migration guide, method and user documentation, finding ledger, and project
memory encode the accepted boundary. Policy tests fail on drift in the exact
seven-name experimental set and accepted M7-D2 approval record.

The exact closeout candidate passed 286 tests with 92% branch coverage, Ruff,
strict Pyright, 126-document link validation, generated-contract drift checks,
dependency vulnerability and license audits, clean source/wheel builds, and a
secret-content scan. No package source, estimator, result payload, schema byte,
or runtime behavior changed in the reclassification slice.

This sign-off closes M7B and M7-F001. It does not accept M7C, M7D, the final 1.0
API/schema candidate, or the 1.0 release.
