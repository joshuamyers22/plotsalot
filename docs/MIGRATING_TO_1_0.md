# Migrating from 0.1.1 to 1.0

- Status: 1.0 migration contract
- Source inventory: [`PUBLIC_API_REFERENCE.md`](PUBLIC_API_REFERENCE.md)
- Stability policy: [`API_STABILITY.md`](API_STABILITY.md)

Plotsalot 1.0 preserves every root name shipped in
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

| Boundary | 0.1.1 to 1.0 | Consumer action |
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
| 12 checked-in schemas | No schema identifier or emitted discriminator/version pair was removed; 49 distinct triples are retained | Validate against the corrected candidate schemas and select variants by both `schema_version` and `analysis` |

## Pre-1.0 schema-document corrections

M7C found three declaration gaps without changing runtime serialization:

- `grouped-result.schema.json` now declares the six already-emitted grouped
  robust identities, their robust nested results, and resampling work record;
- `composition-result.schema.json` no longer requires two resource-limit fields
  that `CompositionResult.to_dict()` has never emitted; and
- `bayesian-result.schema.json` declares all emitted top-level and computation
  fields and rejects unknown top-level properties.

These corrected documents, 51 retained golden examples, and the mutation suite
form the 1.0 baseline. A consumer that copied a `0.1.1` schema should replace it
with the matching 1.0 schema before validating 1.0 output.
Valid `0.1.1` runtime payloads do not need a data migration.

## Release boundary

M7A–M7D retain the public inventory, robust-meta experimental reclassification,
adversarial compatibility suite, and exact-candidate package evidence. Version
`1.0.0` was tagged and published through the protected trusted-publishing
workflow after independent owner acceptance.

Capabilities marked post-1.0 or rejected in the
[compatibility ledger](m7/compatibility-disposition.json) were never part of the
0.1.1 Python contract; their absence is not a migration from 0.1.1.
