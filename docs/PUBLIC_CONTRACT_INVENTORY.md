# Public Contract Inventory

- Status: M7C API/schema hardening complete on 2026-09-15
- Manifest: [`m7/public-contract.json`](m7/public-contract.json)
- Human reference: [`PUBLIC_API_REFERENCE.md`](PUBLIC_API_REFERENCE.md)
- Golden corpus: [`m7/golden-results.json`](m7/golden-results.json)
- Update command: `make update-public-contract`
- Drift check: `make public-contract`, included in `make check`

The retained manifest records the exact candidate surface that M7 will review
and harden for 1.0. It is generated deterministically from package metadata,
`plotsalot.__all__`, runtime signatures and dataclass fields, internal CLI
parsers, checked-in JSON schemas, and literal public error codes.

The classified inventory contains:

- 144 root-package exports with their kind, defining module, signature,
  dataclass fields, and `to_dict()` capability;
- 25 public result types with a serialized `to_dict()` representation;
- four console scripts, including subcommands, arguments, defaults, choices,
  exit-status meanings, stdout format, and machine-readable artifact contracts;
- 12 checked-in schemas with SHA-256 identities and 49 discovered
  `(schema_version, analysis)` variants;
- 51 retained examples covering all 25 serialized public result types, with 50
  stable examples and one experimental robust-meta example;
- the stable `main`, `facet_{one_based_index}`, and
  `panel_{one_based_index}` semantic axes forms; and
- `M6CMetaError`, its stable `code` attribute, and all 16 currently reachable
  literal error codes.

All 144 names shipped in `0.1.1` remain in the 1.x accepted candidate; no
pre-1.0 removal or rename is proposed. M7B supersedes the all-stable M7A
candidate for seven dedicated robust-meta names: `RobustMetaAnalysis`,
`RobustMetaResult`, and the five nested `RobustMeta*Result` records are marked
`one_x_disposition="experimental"`. The other 137 names remain `stabilize`.
The generated human reference lists every classified name, disposition, and
normative documentation.

## Review meaning

Manifest drift fails the production check. An intentional change must first be
classified under the accepted 1.x stability policy, receive any required
method/schema/migration approval, and update the implementation and tests.
`make update-public-contract` is the last step after that review, not a way to
bypass it.

The `defined_in` field is retained review metadata: the stable import boundary
is the root name in `plotsalot.__all__`, so an internal module move may be
compatible even though it still requires manifest review. Exact human-readable
exception messages and CLI prose are not frozen. Console exit meanings,
machine-readable artifact schemas, documented semantic axes, exception types
and codes, public call signatures, serialized variants, and published schema
bytes are compatibility boundaries.

M7C validates every retained example against Draft 2020-12 and rejects missing
fields, wrong types, wrong versions, wrong discriminators, and unknown top-level
properties. The manifest retains the corpus hash and coverage counts so fixture
or schema drift fails the normal production check.
