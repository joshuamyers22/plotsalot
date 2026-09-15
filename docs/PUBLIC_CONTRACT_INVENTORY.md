# Public Contract Inventory

- Status: M7A baseline implemented
- Manifest: [`m7/public-contract.json`](m7/public-contract.json)
- Update command: `make update-public-contract`
- Drift check: `make public-contract`, included in `make check`

The retained manifest records the exact candidate surface that M7 will review
and harden for 1.0. It is generated deterministically from package metadata,
`plotsalot.__all__`, runtime signatures and dataclass fields, internal CLI
parsers, checked-in JSON schemas, and literal public error codes.

The initial inventory contains:

- 144 root-package exports with their kind, defining module, signature,
  dataclass fields, and `to_dict()` capability;
- 25 public result types with a serialized `to_dict()` representation;
- four console scripts, including subcommands, arguments, defaults, choices,
  exit-status meanings, stdout format, and machine-readable artifact contracts;
- 12 checked-in schemas with SHA-256 identities and 43 discovered
  `(schema_version, analysis)` variants;
- the stable `main`, `facet_{one_based_index}`, and
  `panel_{one_based_index}` semantic axes forms; and
- `M6CMetaError`, its stable `code` attribute, and all 16 currently reachable
  literal error codes.

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

This slice inventories schemas and serializable result types; it does not claim
that every emitted variant already has a retained golden instance. M7C must add
and mutation-test those golden fixtures before the 1.0 candidate can pass.
