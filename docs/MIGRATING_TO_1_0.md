# Migrating from 0.1.1 to 1.0

- Status: M7B-updated 1.0 migration candidate
- Source inventory: [`PUBLIC_API_REFERENCE.md`](PUBLIC_API_REFERENCE.md)
- Stability policy: [`API_STABILITY.md`](API_STABILITY.md)

The current 1.0 technical candidate preserves every root name shipped in
`plotsalot 0.1.1`. No import, function/class name, public signature, console
script, serialized schema, semantic axes key, or stable coded exception is
removed or renamed by M7A pass 2.

## Robust aggregate meta-analysis

The `0.1.1` call selected by `meta_analytic_effect=True, type="robust"` remains
available with the same fixed-Student-t4 estimator, strict coded failures, and
no-fallback behavior. It is reclassified as **experimental** for 1.0 after the
locked M7B mapping retained one `robust_meta_ambiguous_optimum` failure.

The seven dedicated `RobustMeta*` public types and the schema-v2 robust-meta
result variant are therefore excluded from the 1.x stable-method and stable-
serialization promise. Consumers should not build a long-lived 1.x interchange
contract on that variant. Pin the plotsalot version, retain serialized
provenance, handle `M6CMetaError.code`, and plan to revalidate or reanalyze if a
later release replaces or removes the experimental method. Classical and
Bayesian aggregate modes are separate methods, not automatic substitutes.

## Reviewed no-change boundaries

| Boundary | 0.1.1 to current 1.0 candidate | Consumer action |
|---|---|---|
| 56 upstream-workflow Python surfaces | No removal or rename | None |
| Shared analysis and seven selector functions | No removal or rename | None |
| 24 stable top-level serialized result types plus experimental `RobustMetaResult` | Existing bytes unchanged; robust-meta schema v2 is excluded from the stable promise | Continue selecting stable variants by discriminator; pin and revalidate experimental robust-meta output |
| 22 stable nested result records plus five experimental `RobustMeta*` components | Names and constructor fields retained | Do not treat experimental robust-meta fields as a durable 1.x interchange contract |
| 11 stable analysis containers plus experimental `RobustMetaAnalysis` | Exact stable analysis/render handoff types retained | Pin and revalidate the experimental robust-meta container |
| Nine selected-data records | Owned data boundary types retained | None |
| Five plot/theme contracts | `StatsPlot`, grouped/composed containers, annotations, and theme retained | Continue using documented semantic axes, not pixels |
| `StructuredResult` | Protocol retained | None |
| `M6CMetaError` | Exception type, `code`, and 16 codes retained | Match `code`, not message prose |
| Four console scripts | Names, command paths, arguments, exit meanings, and artifact schemas retained | None |
| 12 checked-in schemas | Existing bytes and 43 variant discriminators retained | Keep validating against the matching published schema |

## Still provisional

This is not the final 1.0 migration statement. M7B is closed with the robust-meta
experimental reclassification above. M7C must add golden serialized fixtures
and adversarial compatibility tests; any resulting change must update this
document with an affected-name/variant list and an explicit consumer action
before 1.0 acceptance.

Capabilities marked post-1.0 or rejected in the
[compatibility ledger](m7/compatibility-disposition.json) were never part of the
0.1.1 Python contract; their absence is not a migration from 0.1.1.
