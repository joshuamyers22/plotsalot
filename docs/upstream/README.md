# Upstream Baselines

`manifest.json` pins the two source repositories used for behavioral discovery
and cross-language parity. The manifest records revisions, inventory counts, and
hashes of the files that define package metadata and exported APIs.

The repositories themselves are not vendored. R may be used in an isolated,
development-only oracle workflow to produce normalized fixtures. Released
Python artifacts must not depend on R, GitHub, or these repositories.

`ggstatsplot` is MIT licensed. `qqplotr` is GPL-3. Until ADR-010 is approved,
contributors may inspect `qqplotr` only for inventory and public behavior; they
must not copy or translate its source into this repository.
