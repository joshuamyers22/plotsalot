# M3B Verification Evidence

- Date: 2026-09-14
- Scope: approved W1–W3/G4 methods, repeated/grouped rendering, pairing,
  correction, schemas, oracle, benchmark, and package surfaces
- Technical result: release-candidate gates pass
- Milestone result: passed; Joshua Myers accepted the independent review and
  final M3B release candidate on 2026-09-14

## Statistical and sample evidence

- Joshua Myers approved explicit-subject paired t/Hedges' g-z, complete-block
  repeated-measures ANOVA, always-primary Greenhouse–Geisser correction, paired
  Holm families, and grouped correction scope.
- Analytic and independent tests cover paired orientation, repeated
  sums-of-squares, covariance-projection epsilon, corrected/raw dfs and p-values,
  exact gamma correction, pairwise estimates/intervals/Holm, complete-block
  exclusion, duplicate precedence, null identities/values, permutations,
  degenerate designs, atomic grouped failure, and resource ceilings.
- The renderer draws subject paths only from the same complete matrix used by
  inference and formats all statistics from the typed result.

## R oracle and compatibility

Pinned R 4.5.1 and the approved ggstatsplot revision generated the raw repeated
object. Base R independently normalized complete-block repeated ANOVA,
Greenhouse–Geisser epsilon/dfs/probability, paired contrasts, intervals, and
Holm adjustment. `make verify-oracle` passes.

Python requires an explicit subject column and excludes incomplete subjects from
both analysis and rendering. It always makes Greenhouse–Geisser-corrected
inference primary. Its approved F-to-partial-omega conversion differs from the
upstream effect output; these are explicit adaptations.

- Oracle manifest SHA-256:
  `0e13f76a600bc6a8dac6b8473eb38c9b1b210b01c81b7e38979df27ffaa04b23`

## Performance evidence

| Workload | Selection median | Analysis median | Render median |
|---|---:|---:|---:|
| Within, 100 subjects / 5 conditions | 5.89 ms | 33.13 ms | 124.57 ms |
| Within, 1K subjects / 5 conditions | 50.32 ms | 78.75 ms | 579.03 ms |
| Within, 10K subjects / 5 conditions | 493.34 ms | 529.13 ms | 5,074.34 ms |
| Within, 1K subjects / 10 conditions / 45 contrasts | 81.35 ms | 128.73 ms | 652.96 ms |
| Within, 1,001 subjects / 5 conditions / one incomplete | 49.72 ms | 78.96 ms | 554.31 ms |

The artifact contains five warmed samples per phase and places input-frame
allocation outside the measured boundary.

- M3 benchmark SHA-256:
  `aa4509bad1c58ae1e02501c31dbae0487ca2edc36838dabda731721e7399b513`

## Production gate

- Ruff and strict Pyright pass.
- 117 tests pass with 90% repository branch coverage; every new M3B module is
  at least 94% covered.
- Vulnerability, dependency-license, build, oracle, benchmark, and isolated
  wheel smoke gates pass.

- Wheel SHA-256:
  `a7d37cd37ec08cc57f8b7222844cf850c783d235b9584e293851c8f06fd436c4`

## Closeout

Joshua Myers independently reviewed the release candidate, accepted every
recorded finding disposition, and approved M3B on 2026-09-14. All technical and
accountable M3B gates are complete.
