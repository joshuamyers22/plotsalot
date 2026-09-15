# Migrating from 0.1.1 to 1.0

- Status: M7A pass 2 baseline; update against the exact 1.0 candidate
- Source inventory: [`PUBLIC_API_REFERENCE.md`](PUBLIC_API_REFERENCE.md)
- Stability policy: [`API_STABILITY.md`](API_STABILITY.md)

The current 1.0 technical candidate preserves every root name shipped in
`plotsalot 0.1.1`. No import, function/class name, public signature, console
script, serialized schema, semantic axes key, or stable coded exception is
removed or renamed by M7A pass 2.

## Reviewed no-change boundaries

| Boundary | 0.1.1 to current 1.0 candidate | Consumer action |
|---|---|---|
| 56 upstream-workflow Python surfaces | No removal or rename | None |
| Shared analysis and seven selector functions | No removal or rename | None |
| 25 top-level serialized result types | Existing schema discriminators and `to_dict()` shapes unchanged | Continue selecting by `schema_version` and `analysis` |
| 27 nested result records | Names and constructor fields retained | Continue importing from `plotsalot` when direct construction or typing is needed |
| 12 analysis containers | Exact analysis/render handoff types retained | None |
| Nine selected-data records | Owned data boundary types retained | None |
| Five plot/theme contracts | `StatsPlot`, grouped/composed containers, annotations, and theme retained | Continue using documented semantic axes, not pixels |
| `StructuredResult` | Protocol retained | None |
| `M6CMetaError` | Exception type, `code`, and 16 codes retained | Match `code`, not message prose |
| Four console scripts | Names, command paths, arguments, exit meanings, and artifact schemas retained | None |
| 12 checked-in schemas | Existing bytes and 43 variant discriminators retained | Keep validating against the matching published schema |

## Still provisional

This is not the final 1.0 migration statement. The M7B robust-meta calibration
may reaffirm, replace, or reclassify that method, and M7C must add golden
serialized fixtures and adversarial compatibility tests. Any resulting change
must update this document with an affected-name/variant list and an explicit
consumer action before 1.0 acceptance.

Capabilities marked post-1.0 or rejected in the
[compatibility ledger](m7/compatibility-disposition.json) were never part of the
0.1.1 Python contract; their absence is not a migration from 0.1.1.
