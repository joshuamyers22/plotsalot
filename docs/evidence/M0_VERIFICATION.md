# M0 Verification Evidence

- Date: 2026-09-13
- Scope: repository skeleton and parametric `gghistostats` walking skeleton
- Result: Passing for implemented scope; M0 remains in progress

## Locked direct dependencies

| Package | Version |
|---|---:|
| Matplotlib | 3.11.2 |
| NumPy | 2.5.3 |
| Polars | 1.44.2 |
| SciPy | 1.18.1 |
| Statsmodels | 0.15.0 |
| Pyright | 1.1.411 |
| Ruff | 0.16.5 |

`uv.lock` is the authoritative dependency graph.

## Quality gate

Command: `make check`

- Ruff lint: passed.
- Ruff formatting check: 61 files formatted.
- Pyright strict check: 0 errors, 0 warnings, 0 information messages.
- Unit suite: 39 tests passed.

## Walking-skeleton smoke

The headless example analyzed `[1, 2, 3, 4, 5]` against a null mean of zero,
saved an SVG, and produced:

```text
t(4) = 4.24, p = 0.013, Cohen's d = 1.90
n = 5; 0 null row(s) excluded; 95% mean CI [1.04, 4.96]
```

The focused tests separately assert the full-precision analytic values, sample
reconciliation, immutable input, JSON serialization, semantic plot artists, and
invalid input behavior.

## Build and isolated artifact smoke

`uv build` produced:

| Artifact | SHA-256 |
|---|---|
| `plotsalot-0.1.0.tar.gz` | `7ff84f50773f3fe2821db6374ddc624090760e9fdf789198dae0710c59c3206c` |
| `plotsalot-0.1.0-py3-none-any.whl` | `94d71b3c92c5c0810e4e892e9075668679da2656bc0bd982193286b1902d4360` |

The wheel was installed with `uv run --isolated --with <wheel>` and its
`gghistostats` result contract passed a Python-only smoke assertion.

## Remaining M0 evidence

- Containerized R-oracle fixture generator and locked R dependency identity.
- Representative oracle fixtures beyond the analytic Python test.
- Performance and peak-memory benchmark distributions.
- Statistical-methods owner approval.
- ADR-010 qualified license review and final repository license decision.
