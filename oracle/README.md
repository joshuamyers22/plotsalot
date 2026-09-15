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

M2 adds raw pinned-ggstatsplot objects plus normalized base-R fixtures for the
labeled-dot overall/per-label means and intervals, Pearson coefficients and
Fisher intervals, pairwise sample counts, and Holm-adjusted matrix p-values.
`tools/verify_oracle.py` compares those retained values to the Python result
contracts and checks every oracle artifact hash.

M3 adds independent and complete-block repeated comparison objects plus
normalized Welch, Greenhouse–Geisser, paired-contrast, interval, and Holm
references. M4 adds one-way, independent, paired, raw-row, aggregate-count,
bar, pie, and grouped categorical objects. Base R independently inverts the M4
noncentral chi-square intervals and computes exact binomial intervals; the
verifier explicitly asserts upstream Fisher, McNemar, Pearson's-C, and stratum
adjustment differences as adaptations.

M5A adds raw pinned-ggstatsplot coefficient-table and fitted-`lm` objects plus
normalized base-R OLS coefficient and model-dimension results. M5B adds a raw
pinned-ggstatsplot meta-analysis object and normalized study and summary results.
The oracle independently solves the approved intercept-only
REML score in base R and derives modified Hartung–Knapp inference, prediction,
and heterogeneity values. Pinned metafor 5.0-1 supplies separate normal and
`adhoc` references; its iterative tau estimate is checked at `1e-6` relative
and `1e-8` absolute tolerance, while the independently solved values use
`1e-10` relative and `1e-12` absolute tolerance.

M6A adds raw robust ggstatsplot objects for one-sample, association,
between-group, and repeated-group workflows. Because the approved M6A methods
deliberately adapt upstream intervals, association reference df, effects, and
two-condition repeated targets, base R separately implements the approved
fixed-trim, Winsorized, Yuen/Welch–Yuen, and repeated-omnibus formulas. The
Python verifier compares those normalized fields at `1e-10` relative and
`1e-12` absolute tolerance and treats the raw upstream objects as explicit
compatibility evidence rather than the acceptance target.

Do not publish the oracle image. Its development-only dependency graph has
licenses distinct from the eventual plotsalot distribution decision.
