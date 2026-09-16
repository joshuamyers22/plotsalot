# M7B Locked Mapping Verification

- Date: 2026-09-15
- Plan: `M7_CALIBRATION_PLAN.md`, approved version 1
- Driver revision: `d272aea402b77144d2ce2ef9cdaf52743e53916f`
- Artifact: `m7b-robust-meta-mapping.json`
- SHA-256: `fb556565ca1d1184a1780410a78aa8444a1b3b26546147088dbde6c93f7ee076`
- Gate: retained with a predeclared reaffirmation blocker; confirmation and
  independent review complete, experimental reclassification approved

## Execution identity

The one-time mapping run started from a clean tree after local and hosted gates
passed on the exact driver revision. It used seed root `2026091531`, PCG64DXSM,
16 workers, 2,000 cases in each of 38 ordered cells, and 76,000 total fits. The
58,612-byte JSON artifact records Python, platform, dependency, stream, grid,
work, and source identities and is accompanied by a matching SHA-256 seal.

No raw simulated arrays, exception prose, machine-local path, or credential is
retained. The artifact was inspected only after it had been fully written and
sealed.

## Predeclared summary outcome

All 38 cells retained their full 2,000-case coverage denominator. There were no
cells whose two-sided 99% Wilson upper bound was below `0.95`, so the mapping
showed no predeclared undercoverage flag.

One of 76,000 fits failed in
`primary-k010-tau-0p0250-mu-0p0000-linear`. Its stable production code is
`robust_meta_ambiguous_optimum`. The cell retained 1,999 successful fits and one
uncovered failure in its denominator; its coverage was `0.9695` with 99% Wilson
interval `[0.9579385278743707, 0.9779566881318337]`.

Five cells met the predeclared conservative flag because their 99% Wilson lower
bound exceeded `0.95`:

| Scenario | Coverage | 99% Wilson interval |
|---|---:|---|
| `k=10, tau=0`, primary | 0.9630 | [0.9505074936768568, 0.9724307065592935] |
| `k=10, tau=0.025`, primary | 0.9695 | [0.9579385278743707, 0.9779566881318337] |
| `k=30, tau=0`, primary | 0.9655 | [0.9533539008740859, 0.9745677669659314] |
| `k=30, tau=0.025`, primary | 0.9660 | [0.953924849762166, 0.9749935115986246] |
| `k=50, tau=0.0625, mu=0.3`, translation audit | 0.9635 | [0.9510756998242796, 0.9728591939326442] |

The paired reversed-grid audit summaries agree with their matched primary cells
apart from floating-point-order differences below `3e-11` in the reported error
and interval-width summaries. No threshold, scenario, seed, optimizer, or method
was changed after inspection.

The retained-artifact regression test fixes the source revision, digest, plan
identity, full denominators, failure location/code, conservative-cell set, and
absence of undercoverage flags. The exact evidence commit passed 284 tests with
92% branch coverage, Ruff, strict Pyright, 123-document link validation, and the
generated-contract drift check.

## Fixed disposition consequence

The approved plan states that any fit failure blocks reaffirmation unless its
cause is corrected and the entire locked run is replaced under a new,
owner-approved experiment version, while preserving this artifact. Therefore
option 1, reaffirmation of the current interval, is blocked by this mapping
result. Joshua Myers later reviewed both locked artifacts and selected
experimental reclassification for 1.0; no rerun is authorized.

The independently seeded confirmation subsequently ran once from the committed,
sealed mapping artifact and verified this mapping digest.
