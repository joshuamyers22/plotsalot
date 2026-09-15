# Contributing

Plotsalot is a pre-1.0 scientific Python project. Keep changes bounded, preserve
the declared statistical and ownership contracts, and add evidence for changed
behavior.

## Set up a checkout

Use Python 3.11 or newer and the locked development environment:

```sh
make setup
```

For a new clone or maintainer machine, complete
[`checklists/REPOSITORY_SETUP.md`](checklists/REPOSITORY_SETUP.md) before the
first commit or push.

## Make a change

- Work on a focused branch rather than directly on `main`.
- Keep Polars as the public tabular boundary and make numerical ownership
  explicit.
- Do not change an approved statistical method, compatibility classification,
  license, security policy, or release policy without the corresponding review.
- Add a regression test for corrected defects and deterministic seeds for random
  procedures.
- Update user documentation, method specifications, schemas, and changelog
  entries in the same change when public behavior changes.
- Keep credentials, private data, generated distributions, and raw telemetry out
  of Git.

## Verify the change

Run the local quality and packaging gates:

```sh
make check
make audit
make build
```

`make oracle` regenerates the pinned R compatibility evidence and requires
Docker. `make benchmark` refreshes retained performance evidence. Run either only
when the change affects its declared boundary, then review the resulting diff.

## Submit a pull request

Pull requests must state:

- the user-visible or risk-reducing outcome;
- compatibility, statistical, security, and data-boundary effects;
- verification evidence and any deliberately unrun gate; and
- a rollback or forward-fix path.

The accountable owner must review release, security, governance, license, and
statistical-method changes. Automated checks and agent review do not replace
that approval. Maintainers should follow the [release procedure](docs/RELEASING.md)
and complete the release-readiness checklist before creating a version tag.
