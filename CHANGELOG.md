# Changelog

## Unreleased

- Created the `plotsalot` production repository and M0 planning/evidence records.
- Added the initial parametric `gghistostats` walking skeleton with structured,
  extractable results and a Matplotlib renderer.
- Added M1 shared contracts: a reusable Polars-to-NumPy numeric boundary,
  renderer-independent histogram analysis, reusable rendering, generic typed
  plot/result extraction, validated named axes, and immutable annotations.
- Added the lockfile-driven R 4.5.1 oracle for pinned ggstatsplot fixtures,
  SHA-256 integrity checks, and explicit upstream/adapted behavior records.
- Added retained 10K/100K/1M-row analysis/render timing and incremental
  peak-allocation distributions, with artifact checks in the unit gate.
- Adopted the MIT license and limited the upstream compatibility scope to
  ggstatsplot in ADR-010.
