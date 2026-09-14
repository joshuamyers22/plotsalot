# M1 Adversarial Code and Architecture Review

## Review metadata

- Repository: `plotsalot`
- Remote: `https://github.com/joshuamyers22/plotsalot`
- Starting revision: `4270c7536034d7096f081a4212463fa4c03c4819`
- Review date: 2026-09-14
- Product purpose: inspectable statistical plot-plus-result workflows for Python
- First-party scope: M1 result, data, histogram-analysis, rendering, public API,
  tests, schemas, and milestone documentation
- North star: one reconciled sample and one typed result flow from Polars input
  through independent analysis to caller-owned Matplotlib output
- Blocking threshold: any critical/high finding or failed M1 invariant
- Review ceiling: three evidence-changing passes

## Executive verdict

- Technical verdict: approve.
- Milestone verdict: approve; M0 entry approvals were recorded on 2026-09-14.
- Highest remaining risk: future statistical families require method-specific
  specifications and validation before implementation.
- Strongest property: data selection, statistical computation, result records,
  and rendering now have enforceable dependency and test boundaries.

## Verification evidence

| Check | Result |
|---|---|
| Formatting and lint | Passed via `make check` |
| Static typing | Pyright strict: 0 errors, 0 warnings |
| Unit/contract/artifact/license tests | 54 passed |
| Coverage | 79% branch coverage; enforced floor 75%; M1 modules 97–100% |
| Build/package | Wheel and sdist passed |
| Architecture contracts | Analysis modules reject pandas/Matplotlib imports in tests |
| Dependency/security audit | No known vulnerability; license policy passed |
| Isolated artifact smoke | Passed with headless Matplotlib and no R/network runtime |

## Architecture map

```text
Polars input
    -> data boundary (owned finite float64 sample + audit)
    -> histogram analysis (SciPy/NumPy + typed result)
    -> histogram renderer (Matplotlib)
    -> StatsPlot (figure + named axes + typed result + annotations)
```

The compatibility `core` module re-exports prior names, but new internal code
uses `result` and `plot` directly. Statistical modules do not depend on the
renderer. No database, network, filesystem, global random state, or process
boundary participates in the M1 path.

## Findings and dispositions

### M1-001 — analysis and rendering shared a concrete module

- Severity: high.
- Evidence: the first implementation pass kept SciPy analysis and Matplotlib
  construction in `histogram.py` and mixed result records with plot objects in
  `core.py`.
- Consequence: later analyses could inherit renderer coupling and analysis-only
  use would load presentation concerns.
- Correction: split `result.py`, `data.py`, `histogram_analysis.py`, `plot.py`,
  and the Matplotlib `histogram.py` adapter; retain `core.py` only as a
  compatibility export.
- Acceptance: import-boundary tests and the full gate pass.
- Status: closed.

### M1-002 — repository quality gate did not enforce coverage

- Severity: medium.
- Evidence: the baseline `make test` ran unittest without coverage measurement.
- Consequence: future untested contract branches could merge while the nominal
  quality gate stayed green.
- Correction: pin Coverage.py, enable branch measurement, and enforce the
  measured 75% repository baseline in `make check`.
- Acceptance: full gate reports 79%, with the new M1 modules at 97–100%.
- Status: closed.

### M1-003 — a NumPy read-only flag could be reversed by a consumer

- Severity: medium.
- Evidence: the first data contract owned an array and disabled writes, but an
  owning NumPy array can normally have writes re-enabled.
- Consequence: a retained analysis could be rendered from values mutated after
  its statistical result was computed.
- Correction: back the public array with immutable bytes and test both ordinary
  assignment and attempts to re-enable the write flag.
- Acceptance: focused mutation tests pass.
- Status: closed.

## Remaining limitations

- The 75% repository floor is an initial enforced baseline, not the final target;
  CLI entry points inherited from the archetype currently dominate uncovered
  lines.
- M1 validates structural sample/result identity. The M0 oracle and statistical
  approval now pass.
- ADR-010 separately records Joshua Myers's upstream-scope and MIT-license
  decision.
