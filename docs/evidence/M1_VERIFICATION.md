# M1 Verification Evidence

- Date: 2026-09-14
- Scope: shared result, data, analysis, and Matplotlib plot contracts
- Result: passed; M0 entry gate and M1 technical scope complete

## Contract evidence

- Result records are frozen, validate schema invariants, serialize without
  non-finite JSON values, and match the checked-in schema shape.
- `select_numeric_sample` owns a read-only float64 buffer, reconciles null rows,
  and rejects unsupported dataframe, dtype, size, variation, and finite-value
  states.
- `histogram_analysis` depends on result/data/NumPy/SciPy/Polars boundaries and
  does not import Matplotlib.
- `render_gghistostats` can render the same analysis repeatedly without
  recomputation and formats annotations from typed result fields.
- `StatsPlot` owns an immutable named-axes mapping and rejects empty or foreign
  figure axes while leaving Matplotlib objects caller-customizable.

## Quality and coverage gate

Command: `make check`

- Ruff lint and formatting: passed.
- Pyright strict: 0 errors and 0 warnings.
- Unit, retained-artifact, and license suite: 54 tests passed.
- Branch coverage: 79% repository-wide against a 75% enforced floor.
- New M1 modules: 100% for result, analysis, plot, and histogram rendering;
  97% for the data boundary (the unexecuted branch is a defensive dimensionality
  check after a Polars Series conversion).

## Dependency and artifact gate

- `make audit`: no known vulnerabilities in locked runtime packages; dependency
  license policy passed.
- `make build`: sdist and wheel built from the locked project. The current wheel
  SHA-256 is `47d3cebd7b3dc18996d24f3a2e009c175be022cafb0baf8355e88757b947f633`.
- Isolated Python-only wheel smoke: analysis, null reconciliation, immutable
  sample, JSON serialization, named axes, and headless rendering passed.

## Entry-gate closeout

M0's oracle and benchmark evidence pass. Joshua Myers approved its statistical
specification, ADR-010's approved upstream scope, and the MIT distribution
license on 2026-09-14, closing M1's remaining entry gate.
