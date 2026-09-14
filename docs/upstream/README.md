# Upstream Baselines

`manifest.json` pins the source repository used for behavioral discovery and
cross-language parity. The manifest records its revision, inventory counts, and
hashes of the files that define package metadata and exported APIs.

The repositories themselves are not vendored. R may be used in an isolated,
development-only oracle workflow to produce normalized fixtures. Released
Python artifacts must not depend on R, GitHub, or these repositories.

`ggstatsplot` is MIT licensed. ADR-010 records plotsalot's MIT distribution
license and upstream-notice requirements.
