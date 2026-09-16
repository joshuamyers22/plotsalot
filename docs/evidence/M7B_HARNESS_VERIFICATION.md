# M7B Calibration Harness Verification

- Date: 2026-09-15
- Scope: locked robust-meta boundary-calibration driver and disposable smoke
- Starting revision: `3e4c509`
- Gate: implementation-owner harness gate passed; locked evidence and independent
  review not started

## Accepted predecessor

Joshua Myers independently accepted M7A pass 2 on 2026-09-15. The accepted
candidate retains all 144 root exports without a removal or rename and closes
M7-F004. This acceptance permits M7B to proceed; it does not accept any M7B
result or the final 1.0 contract.

## Locked experiment identity

`tools/calibrate_m7b.py` implements version 1 of `M7_CALIBRATION_PLAN.md` without
changing the production estimator, optimizer, interval, cutoff, tolerance,
warning, or fallback behavior. Its fixed run identities are:

| Run | Seed root | Cells | Cases per cell | Total fits | Evidence status |
|---|---:|---:|---:|---:|---|
| Disposable smoke | `2026091530` | 38 | 20 | 760 | Never acceptance evidence |
| Locked mapping | `2026091531` | 38 | 2,000 | 76,000 | Retained; reaffirmation blocker |
| Locked confirmation | `2026091532` | 8 | 5,000 | 40,000 | Retained; independent review pending |

The mapping grid has 30 primary cells, two translation cells, two 500-study
cells, two paired reversed-grid fits, and two piecewise-log standard-error
shape cells. The piecewise-log grids retain endpoints `0.15` and `0.35` and
median `0.25`. A reversed-grid fit is a deterministic permutation of its
matched primary case and consumes no second random stream.

Each independent stochastic case uses PCG64DXSM with a `SeedSequence` formed
from the locked seed root, four little-endian 32-bit words from the SHA-256
scenario identity, and the case index. The artifact records that identity and
the deterministic standard-error-grid digest for every cell.

## Failure and artifact controls

- Every fit failure remains uncovered in the declared cell denominator and is
  counted by a stable production or harness failure code.
- Inclusive interval endpoints determine coverage. Summaries include the 99%
  Wilson interval, undercoverage and conservative flags, interval-width
  quantiles, error summaries, boundary fraction, and work/profile evaluations.
- Locked runs require a clean source tree, exact predeclared output paths, and
  one through 16 workers. Existing artifacts or seals cannot be overwritten;
  disposable smoke output is confined to ignored `.work/`.
- Mapping output receives a SHA-256 seal. Confirmation refuses to start without
  a matching mapping artifact and records its digest.
- Each summarized JSON artifact is capped at 5 MiB. Raw simulated study arrays,
  exception prose, and machine-local paths are not retained.

## Disposable smoke evidence

The approved smoke ran once with eight workers and produced 760 fits across all
38 mapping cells. All fits succeeded; no non-finite output, interval-order
violation, missing work record, or production numerical failure occurred. The
58,187-byte output is retained only under ignored `.work/` and identifies its
source tree as dirty because the driver had not yet been committed.

The smoke's small Wilson intervals are not inspected or cited as statistical
acceptance evidence. Its only purpose is to establish that every scenario,
stream, fit, summary, and artifact path executes within the approved harness.

## Automated verification

Focused tests verify exact scenario and fit counts, immutable confirmation-cell
ordering, retained standard-error endpoints and medians, distinct
identity-derived streams, paired permutation behavior, failure-inclusive
coverage, smoke-output confinement, and seal-tamper rejection. The full gate
passed with 283 tests, 92% branch coverage, Ruff, strict Pyright, 122-document
link validation, and current generated contracts. The dependency vulnerability
and license audit passed, and clean source/wheel artifacts built successfully.

## Gate disposition

The M7B harness slice passes its technical smoke gate. The locked mapping was
then retained unchanged and is documented separately in
`M7B_MAPPING_VERIFICATION.md`. Its single fit failure blocks reaffirmation under
the approved rule. The confirmation was then retained unchanged and is
documented in `M7B_CONFIRMATION_VERIFICATION.md`. No observed coverage informed
a threshold or implementation change. Independent review and the owner's
replace, reclassify, or versioned-correction disposition remain open.
