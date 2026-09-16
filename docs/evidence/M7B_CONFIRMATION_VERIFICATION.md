# M7B Locked Confirmation Verification

- Date: 2026-09-15
- Plan: `M7_CALIBRATION_PLAN.md`, approved version 1
- Execution revision: `f951d101d18edcf147030a4ca080b2221ce32481`
- Artifact: `m7b-robust-meta-confirmation.json`
- SHA-256: `ea1bac057f7fb4b43b030a5f8b3b13f51d165bb073d62f7bdbf0c27ade4ecf7a`
- Mapping SHA-256: `fb556565ca1d1184a1780410a78aa8444a1b3b26546147088dbde6c93f7ee076`
- Gate: locked execution complete; independently reviewed and reclassified as
  experimental by Joshua Myers on 2026-09-15

## Execution identity

The one-time confirmation started from a clean tree containing the sealed
mapping artifact. The preflight recomputed and verified the mapping digest, and
the confirmation artifact records that digest. The run used independent seed
root `2026091532`, PCG64DXSM, 16 workers, 5,000 cases in each of eight ordered
focal cells, and 40,000 total fits.

The 13,257-byte JSON artifact has a matching SHA-256 seal and records the exact
source, environment, dependency, stream, grid, denominator, and work identities.
It retains no raw simulated arrays, exception prose, machine-local path, or
credential.

## Predeclared summary outcome

All 40,000 fits succeeded. No focal cell had a two-sided 99% Wilson upper bound
below `0.95`, so no confirmation cell triggered the predeclared undercoverage
blocker.

Four focal cells were conservatively flagged because their 99% Wilson lower
bound exceeded `0.95`:

| Scenario | Coverage | 99% Wilson interval | Boundary-fit fraction |
|---|---:|---|---:|
| `k=10, tau=0` | 0.9636 | [0.9561402185833133, 0.9698310367098092] | 0.6376 |
| `k=20, tau=0` | 0.9638 | [0.9563579070708882, 0.9700128181339224] | 0.5910 |
| `k=50, tau=0` | 0.9588 | [0.9509311835791816, 0.9654527938334254] | 0.5550 |
| `k=20, tau=0.025` | 0.9586 | [0.9507147459096353, 0.9652697615912834] | 0.5814 |

The other focal results were:

| Scenario | Coverage | 99% Wilson interval | Boundary-fit fraction |
|---|---:|---|---:|
| `k=100, tau=0` | 0.9460 | [0.9371598960349508, 0.9536580070296148] | 0.5360 |
| `k=50, tau=0.025` | 0.9556 | [0.9474734736476801, 0.9625189851779167] | 0.5384 |
| `k=20, tau=0.0625` | 0.9498 | [0.9412326052449163, 0.9571752261417241] | 0.5022 |
| `k=50, tau=0.0625` | 0.9494 | [0.9408033324840216, 0.9568055590792425] | 0.4490 |

“Not flagged” means only that the 99% Wilson interval contains `0.95`; it is not
an exact-calibration claim. No result was pooled across cells, and no threshold,
scenario, seed, method, or implementation was changed after inspection.

## Overall consequence

Confirmation adds independent-seed precision but does not clear the mapping
failure. Under the approved version-1 plan, the retained
`robust_meta_ambiguous_optimum` mapping failure blocks reaffirmation of the
current interval. After independent review, Joshua Myers selected
reclassification as experimental for 1.0 on 2026-09-15. A future stable method
would require a new approved specification and evidence plan while retaining
both current artifacts.

The artifact regression test fixes the confirmation source revision and digest,
its mapping-digest chain, all eight denominators, zero failures, zero
undercoverage flags, and the four-cell conservative set. The exact evidence
candidate passed 285 tests with 92% branch coverage, Ruff, strict Pyright,
125-document link validation, and the generated-contract drift check.
