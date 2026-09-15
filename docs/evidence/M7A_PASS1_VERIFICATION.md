# M7A Pass 1 Verification

- Date: 2026-09-15
- Scope: generated public API, CLI, schema, axes, and coded-error inventory
- Starting revision: `306e80a`
- Gate: implementation-owner technical gate passed; independent review pending

## Implemented slice

Pass 1 adds a deterministic retained manifest for the accepted M7-D1 and M7-D3
boundaries. `tools/public_contract.py` derives the root export inventory from
`plotsalot.__all__`, captures runtime signatures and dataclass fields, inspects
the four installed console-script parsers, hashes every checked-in JSON schema,
discovers schema-version/analysis pairs, and inventories the public coded
exception. Reviewed semantic axes and CLI artifact meanings are retained beside
those generated facts.

Each console module now exposes a private `_build_parser()` hook so the installed
argument contract and the runtime parser have one source. `main()` behavior and
the root public namespace are unchanged. `make public-contract` compares a fresh
render with `docs/m7/public-contract.json`, and `make check` now fails on drift.

## Retained inventory

- 144 unique root exports with names, kinds, defining modules, signatures,
  dataclass fields, and `to_dict()` capability;
- 25 public serialized result types;
- four console scripts and six command paths, including arguments, required
  state, defaults, choices, exit meanings, stdout format, and artifact schemas;
- 12 JSON schemas, exact SHA-256 identities, and 43 discovered
  `(schema_version, analysis)` variants;
- `main`, `facet_{one_based_index}`, and `panel_{one_based_index}` semantic axes
  forms plus grouped-member delegation; and
- `M6CMetaError`, its stable `code` attribute, and 16 literal codes.

## Automated evidence

- `make check`: passed; 275 tests, zero failures, 92% branch coverage, Ruff,
  formatting, strict Pyright, 117 Markdown documents, and manifest drift check.
- `make audit`: no known runtime vulnerabilities or adverse project statuses;
  dependency license policy passed.
- `make build`: built `plotsalot-0.1.1.tar.gz` and the universal wheel from the
  source distribution.
- CLI smoke: `--help` passed for all four entry points and both
  `plotsalot-dataset` subcommands.
- Focused repository-policy tests reconcile the manifest with `plotsalot.__all__`
  and require the approved CLI, schema, axes, and exception boundaries.

## Gate disposition

Pass 1 satisfies the implementation-owner M7A inventory gate. It does not yet
freeze the exact 1.0 candidate, accept a release, or close M7-F003: golden
serialized examples, schema mutations, error/refusal fixtures, and fuller
semantic plot-contract tests remain M7C work. It generates no M7B calibration
evidence and does not change the approved calibration plan or provisional M6C
statistical disposition.
