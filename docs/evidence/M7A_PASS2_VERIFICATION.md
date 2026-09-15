# M7A Pass 2 Verification

- Date: 2026-09-15
- Scope: 1.x root-API classification, migration baseline, and compatibility
  prose reconciliation
- Starting revision: `9c910d4`
- Gate: implementation-owner technical gate passed; independent review pending

## Classification outcome

Pass 2 reviewed every name retained by the generated M7A manifest. All 144 root
exports are intentional public contracts already shipped in `0.1.1`; none is a
wildcard, leading-underscore, test, benchmark, oracle, or incidental dependency
export. The technical candidate therefore proposes no pre-1.0 removal or rename.

Every manifest symbol now has `one_x_disposition="stabilize"` and exactly one
contract category:

| Category | Count |
|---|---:|
| Approved upstream-workflow Python surfaces | 56 |
| Shared analysis function | 1 |
| Selector functions | 7 |
| Top-level serialized result types | 25 |
| Nested result components | 27 |
| Analysis containers | 12 |
| Selected-data records | 9 |
| Plot/theme contracts | 5 |
| Result protocol | 1 |
| Coded exception | 1 |

The classification is fail-closed: adding a root export without assigning a
recognized category makes manifest generation fail. The generated
`PUBLIC_API_REFERENCE.md` lists every classified name and the normative
documentation for its category.

## Reconciliation and migration evidence

The compatibility matrix now distinguishes true remaining deferrals from robust
and Bayesian modes implemented during M6. Historical M2–M5 sections explicitly
point forward to the implemented M6/M6C paths instead of presenting stale
deferrals as the current product boundary. Focused policy tests reject the
previous misleading phrases.

`MIGRATING_TO_1_0.md` records an explicit no-change result for the root API,
console scripts, serialized variants, nested records, plot contracts, semantic
axes, schemas, and coded exception boundary. It remains a baseline rather than
the final migration statement because M7B and M7C may require an evidence-backed
update.

## Automated evidence

- `make check`: passed; 276 tests, zero failures, 92% branch coverage, Ruff,
  formatting, strict Pyright, 121 Markdown documents, and generated manifest
  plus API-reference drift checks.
- Focused repository-policy tests verify the exact ten-category counts, all-144
  stabilization disposition, empty 0.1.1 breaking-change list, and current M6
  compatibility statements while rejecting stale deferral language.
- `git diff --exit-code v0.1.1 -- src/plotsalot/__init__.py pyproject.toml`
  passed. The only package-source changes since the published tag are the four
  behavior-preserving private CLI parser-builder extractions from M7A pass 1.
- `make audit`: no known runtime vulnerabilities or adverse project statuses;
  dependency license policy passed.
- `make build`: built `plotsalot-0.1.1.tar.gz` and the universal wheel from the
  source distribution.

## Gate disposition

The M7A pass-2 technical gate passes. M7-F004 is corrected in maintained prose
and awaits independent confirmation. This pass changes no statistical method,
schema, callable signature, public name, or runtime behavior. It generates no
M7B calibration evidence and does not accept the final 1.0 surface or release
candidate.
