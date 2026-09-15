# M7 Robust Meta-analysis Calibration Plan

- Status: approved version 1; locked mapping retained with a reaffirmation
  blocker, confirmation pending
- Date: 2026-09-15
- Applies to: fixed-Student-t4 aggregate robust meta-analysis only
- Prior evidence: `evidence/M6C_PASS2_VERIFICATION.md` and retained JSON artifacts

## Decision objective

Determine whether the M6C 95% profile-likelihood interval has an acceptable,
operationally describable coverage boundary for 1.0. The retained M6C evidence
shows conservative coverage at exact generating `tau=0` for `k=10` and `k=50`.
The provisional rule permits conservative overcoverage when `k<20` or generating
`tau=0`, but true generating heterogeneity is not observable by a caller.

M7 must map the neighborhood around zero, quantify interval width and failure
behavior, and support exactly one owner disposition:

1. **Reaffirm** the current interval as a supported sensitivity method with a
   runtime-observable warning/qualification and documented conservative region.
2. **Replace** the interval construction with a separately specified and
   validated finite-sample or boundary-calibrated method.
3. **Reclassify** robust aggregate meta-analysis as experimental or remove it
   from the 1.0 stable boundary while retaining the rest of `ggcoefstats`.

The experiment cannot by itself approve option 1, design option 2, or choose
option 3. That is a product/statistical-owner decision over retained evidence.

## Fixed estimand and data-generating model

The primary estimand is the location `mu` in the exact fixed-Student-t4 marginal
model implemented by M6C:

```text
y_i ~ StudentT(df=4,
               location=mu,
               scale=sqrt(standard_error_i^2 + tau^2))
```

The primary interval is the existing two-sided 95% profile-likelihood interval
for `mu`. No implementation tolerance, optimizer, start, likelihood, interval
cutoff, warning, or fallback may change during evidence generation.

Primary simulations use `mu=0` because the implementation is translation
invariant. A locked audit subset repeats `mu=0.3` to detect an accidental loss
of that invariance. Standard errors use the retained deterministic grid
`linspace(0.15, 0.35, k)`, whose median is `0.25`.

## Predeclared scenario grid

### Primary boundary grid

Cross the following factors for 30 cells:

- study count `k`: `10`, `15`, `20`, `30`, `50`, and `100`;
- heterogeneity ratio `tau / median(standard_error)`: `0`, `0.10`, `0.25`,
  `0.50`, and `1.00`; and
- `mu=0`.

The resulting `tau` values are `0`, `0.025`, `0.0625`, `0.125`, and `0.25`.
This grid distinguishes the exact boundary from near-boundary positive
heterogeneity instead of treating `tau=0` as a runtime selector.

### Locked audit cells

Run these additional cells without pooling them into the primary grid:

- translation: `(k=10, tau=0, mu=0.3)` and
  `(k=50, tau=0.0625, mu=0.3)`;
- large-study boundary: `(k=500, tau=0, mu=0)` and
  `(k=500, tau=0.25, mu=0)`; and
- standard-error shape: `(k=20, tau=0)` and `(k=50, tau=0.0625)` using the
  reversed retained grid and a precomputed log-spaced grid with the same median
  and endpoints.

Reversing the deterministic grid tests permutation invariance; it is not an
independent statistical cell. The log-spaced cells test whether the finding is
an artifact of the retained linear standard-error design.

## Cases, streams, and artifacts

- Harness smoke: 20 cases per cell using seed root `2026091530`. Smoke output is
  disposable and never acceptance evidence.
- Locked mapping run: 2,000 cases per primary/audit cell using PCG64DXSM seed
  root `2026091531` and identity-derived `(scenario, case)` child streams.
- Locked confirmation: 5,000 cases for the predeclared focal cells below using
  independent PCG64DXSM seed root `2026091532`:
  `(10,0)`, `(20,0)`, `(50,0)`, `(100,0)`, `(20,0.025)`, `(50,0.025)`,
  `(20,0.0625)`, and `(50,0.0625)`, all at `mu=0`.

The mapping artifact is retained even if it fails. Confirmation is run once
after the mapping artifact is sealed, regardless of the mapping outcome. Seeds
may not be reused for threshold selection, implementation tuning, or a second
“confirmation.” Every fit failure and non-finite result remains in its cell's
denominator and receives a stable failure code.

Artifacts must record the exact commit, Python and dependency versions, platform,
worker count, bit generator, seed roots, ordered scenario definitions, case
counts, successes, failures by code, interval widths, coverage counts, and
Wilson intervals. Raw simulated study arrays are not retained.

## Predeclared summaries

For each cell report:

- empirical 95% interval coverage and a two-sided 99% Wilson interval;
- undercoverage flag: Wilson 99% upper bound is below `0.95`;
- conservative flag: Wilson 99% lower bound is above `0.95`;
- median, 10th, and 90th percentile interval width;
- median absolute pooled-estimate error, mean signed error, and its Monte Carlo
  standard error;
- boundary-fit fraction (`tau_squared` estimate equals zero under the existing
  recorded boundary rule);
- convergence/failure count and exact stable codes; and
- median and 99th-percentile work/evaluation count.

The experiment characterizes evidence rather than converting a failed symmetric
criterion into a pass. “Neither undercoverage nor conservative” means only that
the 99% Wilson interval contains `0.95`; it is not proof of exact calibration.

## Blocking and decision rules

The following are fixed before execution:

- Any primary or confirmation cell whose 99% Wilson upper bound is below `0.95`
  blocks reaffirmation under option 1.
- Any fit failure, non-finite output, interval-order violation, or missing work
  record blocks reaffirmation unless its cause is corrected and the entire
  locked run is replaced under a new, owner-approved experiment version. The
  original artifact remains retained.
- A conservative cell is not silently accepted. Option 1 requires the owner to
  approve the measured overcoverage and a warning/qualification based only on
  observable result state, not the unknowable generating `tau`.
- Translation and reversed-grid audit cells must agree with their matched
  primary cells within their joint Monte Carlo uncertainty. A material mismatch
  is an implementation blocker rather than a new acceptance threshold.
- Option 2 requires a new method specification, implementation identity, schema
  impact review, independent reference, and a separate locked calibration. M7
  evidence for the existing interval cannot be reused as validation of the new
  interval.
- Option 3 requires migration and compatibility updates but no threshold
  weakening.

## Independent evidence

Before final disposition, a reviewer who did not write the simulation driver
must verify:

- the Student-t scale parameterization and generation formula;
- deterministic identity-derived streams and absence of seed reuse;
- Wilson calculation and denominator/failure accounting;
- interval inclusion at exact floating-point boundaries;
- scenario-to-artifact identity and immutable ordering; and
- at least one analytic or separately implemented likelihood/profile case.

The pinned R/metaplus comparison may remain contextual evidence, but it cannot
validate coverage of this different fixed-Student-t4 model.

## Resource ceiling and stopping rules

- Maximum planned fits: 80,000 mapping fits plus 40,000 confirmation fits and
  no more than 2,000 smoke/audit-development fits.
- Maximum parallel workers: 16.
- Maximum wall-clock allocation: 36 aggregate runner-hours.
- Maximum retained artifact size: 5 MiB per summarized JSON file.
- Abort the run on evidence of stream collision, scenario mislabeling, mutable
  shared RNG state, denominator loss, output overwrite, or implementation drift.
- Do not add cases after inspecting results. More precision requires a versioned,
  owner-approved follow-up plan with new seeds and an explicit rationale.

## Approval record

Joshua Myers approved M7-D2 without revision on 2026-09-15. The accepted plan
is version 1: the exact primary and audit grids above; seed roots `2026091530`,
`2026091531`, and `2026091532`; 20-case smoke, 2,000-case mapping, and
5,000-case confirmation counts; the predeclared summaries and blockers; a
ceiling of 80,000 mapping fits, 40,000 confirmation fits, 2,000 development
fits, 16 workers, 36 aggregate runner-hours, and 5 MiB per retained summary;
and Joshua Myers as independent reviewer of the Codex-authored driver and
evidence. Final owner disposition is recorded only after both locked artifacts
and the independent review exist.
