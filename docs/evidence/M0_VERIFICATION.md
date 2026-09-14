# M0 Verification Evidence

- Date: 2026-09-14
- Scope: discovery, parametric `gghistostats` walking skeleton, R oracle,
  retained fixtures, benchmark baseline, and package boundary
- Result: passed; technical evidence and accountable approvals complete

## Locked Python environment

| Package | Version |
|---|---:|
| Matplotlib | 3.11.2 |
| NumPy | 2.5.3 |
| Polars | 1.44.2 |
| SciPy | 1.18.1 |
| Statsmodels | 0.15.0 |
| Coverage.py | 7.16.1 |
| Pyright | 1.1.411 |
| Ruff | 0.16.5 |

`uv.lock` is the authoritative Python dependency graph.

## R oracle and retained fixtures

- Base: `rocker/r-ver:4.5.1` at multi-platform digest
  `sha256:03b023fbf7b1b24ac1bb8b2ac5fd7e15a767e67b40ff50c155e328110981c2aa`.
- Tested platform: Linux arm64.
- Upstream: `ggstatsplot@7a724cd0ab55668b9d0b2e84b12c711c5be68ac8`.
- Dependency graph: 107 packages restored from `oracle/renv.lock`; lockfile
  SHA-256 `79ee4cadc12458298ed7d8213ec4a9678907f88574655f42c696c4f7ecee76f9`.
- Bootstrap: renv 1.2.4 from official commit
  `f98afd8becc4fc7453837ebf14a6ee0ab74faec1`; Dockerfile frontend is also
  pinned by digest.
- Verified local image identity:
  `sha256:c5122aeab7ff25d698770167c85b22d253e1447e6c5eac6b5cc62bb4a6ade4c8`.
- Fixture manifest SHA-256:
  `759f90ad1cc8acc9fc5b5f29f818d70cb988d4b345fc19c3202542cd3542a71d`.

Normal, null-containing, and two-observation fixtures match direct upstream
t-statistic, degrees of freedom, p-value, and sample count plus independent
base-R mean, sample standard deviation, two-sided Student-t interval, and
Cohen's d at `1e-12` relative and absolute tolerance.

The non-finite and degenerate fixtures record an intentional incompatibility:
the pinned upstream call accepts both, while Python rejects them before analysis.
Upstream also reports Hedges' g with an ncp interval; the M0 prototype reports
Cohen's d without effect-size uncertainty. These are classified adaptations,
not parity claims.

Commands: `make oracle` regenerates the evidence; `make verify-oracle` verifies
checked-in evidence without invoking R or Docker.

## Benchmark baseline

The retained artifact contains five warmed samples per phase and size on
macOS 15.1 arm64 with Python 3.12.14. Times are medians; memory is incremental
peak Python allocation measured with tracemalloc.

| Rows | Analysis median | Analysis peak median | Render median | Render peak median |
|---:|---:|---:|---:|---:|
| 10,000 | 1.96 ms | 242 KiB | 61.21 ms | 913 KiB |
| 100,000 | 2.65 ms | 2.30 MiB | 137.61 ms | 2.39 MiB |
| 1,000,000 | 11.85 ms | 22.90 MiB | 323.87 ms | 8.85 MiB |

Artifact SHA-256:
`b805de90258c3d2161aad0e69d05ed1a0a0d6fa2e1b3a9a6c59fe2a9f1088820`.
The input dataframe is created before each phase's measurement boundary.

## Quality gate

Command: `make check`

- Ruff lint and formatting: passed.
- Pyright strict: 0 errors, 0 warnings.
- Unit, artifact, and license suite: 54 tests passed.
- Branch coverage: 79% repository-wide against the enforced 75% floor.

## Walking-skeleton smoke

The headless example analyzed `[1, 2, 3, 4, 5]` against a null mean of zero,
saved an SVG, and produced:

```text
t(4) = 4.24, p = 0.013, Cohen's d = 1.90
n = 5; 0 null row(s) excluded; 95% mean CI [1.04, 4.96]
```

Focused tests assert full-precision values, sample reconciliation, immutable
input, JSON serialization, semantic plot artists, and invalid-input behavior.

## Build and isolated artifact smoke

`uv build` produced the source distribution and wheel. The installable wheel is
hashed here (the sdist contains this evidence file, so recording its own current
hash inside it would be self-referential):

| Artifact | SHA-256 |
|---|---|
| `plotsalot-0.1.0-py3-none-any.whl` | `47d3cebd7b3dc18996d24f3a2e009c175be022cafb0baf8355e88757b947f633` |

The wheel contains only Python package and distribution metadata. An isolated
install outside the repository passed analysis, null reconciliation, immutable
sample, JSON, named-axis, and headless-render assertions without R or Docker.
The locked dependency audit found no known vulnerabilities and the dependency
license-policy check passed.

## Accountable approvals

Joshua Myers approved the M0 one-sample statistical specification, ADR-010's
upstream scope, and the MIT distribution license on 2026-09-14.
See `M0_SIGNOFF.md`.
