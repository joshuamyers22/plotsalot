# M2 Verification Evidence

- Date: 2026-09-14
- Scope: approved frequentist univariate, Pearson correlation, matrix, grouped,
  extraction, schema, oracle, benchmark, and package surfaces
- Technical result: release-candidate gates pass
- Milestone result: passed; Joshua Myers approved the independent review and
  final milestone acceptance on 2026-09-14

## Statistical and sample evidence

- `M2_STATISTICAL_METHODS.md` records Joshua Myers's approval of U1, U2, G1,
  C1, C2, and G2.
- Analytic and independent tests cover one-sample means, per-label Student
  intervals, Pearson coefficients and Student statistics, Fisher intervals,
  pairwise missingness, Holm adjustment, perfect correlation, and rejected
  constant/near-constant/non-finite samples.
- Group tests cover first-observed order, preserved scalar identity, null-group
  audits, atomic named failures, correction scope, and group/row limits.
- Result-injection tests demonstrate that dot, scatter, and matrix annotations
  and cells are rendered from the supplied typed result without reanalysis.

## R oracle

`make oracle` regenerated raw objects from pinned
`ggstatsplot@7a724cd0ab55668b9d0b2e84b12c711c5be68ac8` under R 4.5.1 and normalized
base-R results for labeled means, Pearson/Fisher statistics, pairwise counts,
and Holm adjustment. `make verify-oracle` passes without invoking R or Docker.

- Oracle manifest SHA-256:
  `e1da67740f17c7a149ffa084c8ceb9c072bd897cb97668d6d7a23cd3ce44b136`
- Declared adaptation: exact-perfect Python correlations retain no finite
  Student statistic; base R can emit a very large finite approximation.

## Performance evidence

The M2 artifact retains five warmed measurements per phase. Input dataframe
allocation is outside the measured boundary; memory is incremental Python
allocation peak from `tracemalloc`.

| Workload | Analysis median | Analysis peak | Render median | Render peak |
|---|---:|---:|---:|---:|
| Scatter, 10K rows | 10.39 ms | 0.49 MB | 10.19 ms | 0.88 MB |
| Scatter, 100K rows | 87.28 ms | 4.81 MB | 12.17 ms | 6.10 MB |
| Scatter, 1M rows | 863.70 ms | 48.01 MB | 33.60 ms | 58.30 MB |
| Matrix, 10 variables/10K rows | 508.87 ms | 0.56 MB | 55.68 ms | 1.87 MB |
| Matrix, 25 variables/10K rows | 3187.71 ms | 0.84 MB | 165.29 ms | 7.24 MB |
| Matrix, 50 variables/10K rows | 12581.95 ms | 2.11 MB | 553.34 ms | 25.09 MB |

- M2 benchmark SHA-256:
  `9a512fe22c279fd8d86c1721819b608edaaf39b9039f4c44400fc6e571c4c3fe`
- A fresh M0 comparison on the retained host changed median time by -3.9% to
  +6.7% and median peak allocation by -0.1% to 0.0%, below the 20%
  investigation threshold.

## Quality, dependency, and artifact gates

`make check`:

- Ruff lint and formatting passed.
- Strict Pyright passed with 0 errors and 0 warnings.
- 83 tests passed.
- Repository branch coverage is 86% against the 75% floor.
- New/extended M2 domain coverage: correlation renderer 97%, correlation
  analysis 98%, dot renderer 100%, dot analysis 96%, grouped analysis 93%, plot
  contract 93%, and result contracts 99%.

`make audit` found no known vulnerabilities or adverse project statuses and the
dependency-license policy passed. `make build` produced:

| Artifact | SHA-256 |
|---|---|
| `plotsalot-0.1.0-py3-none-any.whl` | `c252bb8da9761a832cd7b390abbbaf236022db1c7ccc537c4702aba5571c4610` |

The sdist also built successfully. Its hash is not embedded in an evidence file
that the sdist itself contains, avoiding a self-referential artifact record.

An isolated Python environment installed the wheel and passed dot, scatter,
matrix, grouped extraction, JSON serialization, public export, and headless SVG
smoke assertions. The wheel contains Python package and distribution metadata,
with no R or oracle payload.

## Closeout

Joshua Myers independently reviewed the release candidate, accepted every
recorded finding disposition, and approved M2 on 2026-09-14. All technical and
accountable gates are complete.
