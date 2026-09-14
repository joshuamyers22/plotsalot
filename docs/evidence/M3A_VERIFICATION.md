# M3A Verification Evidence

- Date: 2026-09-14
- Scope: approved B1–B3/G3 methods, independent/grouped rendering,
  composition, theme, schemas, oracle, benchmark, and package surfaces
- Technical result: release-candidate gates pass
- Milestone result: passed; Joshua Myers accepted the independent review and
  final M3A release candidate on 2026-09-14

## Statistical and sample evidence

- Joshua Myers approved the Welch t, Welch ANOVA, Hedges' g, partial omega
  squared, pairwise Welch/Holm, and grouped correction-scope specification.
- Analytic and independent tests cover balanced/unbalanced unequal-variance
  samples, two and multi-level formulas, exact gamma bias correction, complete
  pairwise families, Holm/no adjustment, display filtering, null handling,
  non-finite/constant/sparse failure, deterministic scalar/categorical order,
  row permutations, typed identity, and resource ceilings.
- Renderer injection tests establish that subtitles, intervals, brackets, and
  semantic layers use the supplied typed result without reanalysis.

## R oracle and compatibility

Pinned R 4.5.1 and
`ggstatsplot@7a724cd0ab55668b9d0b2e84b12c711c5be68ac8` generated the raw
between-group object. Base R independently normalized Welch ANOVA, Welch
pairwise t tests, intervals, and Holm adjustment. `make verify-oracle` passes.

The raw upstream object identifies Games–Howell pairwise tests; Python's
approved Welch-plus-Holm family is therefore adapted, not equivalent. The
Python partial omega-squared effect is the pre-approved F conversion and its
missing effect interval is explicit.

- Oracle manifest SHA-256:
  `0e13f76a600bc6a8dac6b8473eb38c9b1b210b01c81b7e38979df27ffaa04b23`

## Performance evidence

The M3 artifact retains five warmed measurements per phase with input-frame
allocation outside the measured boundary. Selection measures the data boundary;
analysis is end-to-end selection plus inference; rendering consumes a retained
analysis.

| Workload | Selection median | Analysis median | Render/compose median |
|---|---:|---:|---:|
| Between, 10K rows / 5 levels | 2.12 ms | 31.95 ms | 93.64 ms |
| Between, 100K rows / 5 levels | 2.77 ms | 36.45 ms | 137.33 ms |
| Between, 1M rows / 5 levels | 11.33 ms | 49.98 ms | 926.25 ms |
| Between, 10K rows / 20 levels / 190 contrasts | 4.62 ms | 115.56 ms | 377.98 ms |
| Composition, 1 panel | — | — | 127.44 ms |
| Composition, 20 panels | — | — | 2,628.31 ms |

- M3 benchmark SHA-256:
  `aa4509bad1c58ae1e02501c31dbae0487ca2edc36838dabda731721e7399b513`

## Production gate

- Ruff and strict Pyright pass.
- 117 tests pass with 90% repository branch coverage; every new M3A module is
  at least 94% covered.
- The OSV audit found no known vulnerabilities or adverse project statuses;
  dependency-license policy passes.
- Wheel and sdist build, oracle verification and benchmark verification pass.
- An isolated environment installed the wheel and passed between, grouped,
  composition, extraction, JSON, local-theme, and headless SVG smoke checks.

- Wheel SHA-256:
  `a7d37cd37ec08cc57f8b7222844cf850c783d235b9584e293851c8f06fd436c4`

## Closeout

Joshua Myers independently reviewed the release candidate, accepted every
recorded finding disposition, and approved M3A on 2026-09-14. All technical and
accountable M3A gates are complete.
