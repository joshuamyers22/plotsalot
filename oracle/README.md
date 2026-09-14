# Development R oracle

This directory is development evidence, not a Python runtime dependency.
`Dockerfile` pins Rocker R 4.5.1 by digest, `renv.lock` pins the complete R
package graph, and ggstatsplot is pinned to revision
`7a724cd0ab55668b9d0b2e84b12c711c5be68ac8`.
The renv 1.2.4 bootstrap is fetched from official immutable commit
`f98afd8becc4fc7453837ebf14a6ee0ab74faec1`; the Dockerfile frontend is pinned
by digest as well.

Run from the repository root:

```sh
make oracle
```

The command builds the Linux arm64 image, regenerates raw ggstatsplot and
normalized reference outputs, updates `fixtures/manifest.json`, and verifies
Python parity. Installed Python package behavior neither invokes nor requires
this container workflow.

Normal, null-containing, and small-sample fixtures must match the shared t-test
fields and independent base-R reference calculations at `1e-12` absolute and
relative tolerance. Non-finite and degenerate fixtures retain upstream's
acceptance behavior while requiring the safer Python contract to reject them.

Do not publish the oracle image. Its development-only dependency graph has
licenses distinct from the eventual plotsalot distribution decision.
