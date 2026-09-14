# Statistical Analysis Plan: Cross-Language Parity Program

- Status: M0, M2, M3, and M4 classical specifications approved
- Version: 0.1.0
- Date: 2026-09-13
- Statistical owner/reviewer: Joshua Myers; M0 approval recorded 2026-09-14

## Decision and estimand

- Decision this analysis informs: whether a Python method can be labeled
  equivalent to, adapted from, experimental relative to, or deferred from a
  pinned R behavior.
- Population and estimand: varies by plot family. Every method file must identify
  its population, sampling unit, estimand, null/alternative, and effect-size
  target before implementation.
- Primary hypothesis or prediction target: no shared hypothesis or predictive
  target exists; this is a verification program, not one scientific analysis.
- Model objective, utility, guardrails, and proxy gaps: maximize correct,
  inspectable statistical reporting. Guardrails are sample reconciliation,
  method/label identity, uncertainty metadata, deterministic provenance, and no
  false compatibility claim. Agreement with R alone cannot detect a shared
  methodological defect.
- Practical significance threshold: exact semantics are mandatory. Numerical
  tolerances are method-specific and based on conditioning, algorithm, and
  independent references—not displayed rounding.
- Pre-specified versus exploratory analyses: compatibility fixtures and pass
  thresholds are pre-specified before implementation. Feasibility spikes are
  exploratory and cannot establish parity by themselves.

## Data and sample

- Dataset owners, versions, licenses, hashes, and as-of time: synthetic and
  redistributable reference fixtures only. Each oracle manifest records input
  hash, upstream revisions, R session/lock identity, and generation time.
- Dataset contract: versioned JSON metadata with Parquet or JSON values;
  deterministic column order, explicit dtypes/category order, units,
  nullability, row identity, and expected exclusions.
- Inclusion/exclusion rules: specified per method. Plot and analysis samples are
  reconciled explicitly; visual-only omissions are named separately.
- Observation unit and sample size: fixture-specific. Include normal, null,
  non-finite, degenerate, tied, small-sample, unbalanced, paired, repeated, and
  discrete-support cases as applicable.
- Missing/outlier policy: no imputation. Null-dropping is allowed only when the
  method spec says so and the result records counts. Non-finite values fail by
  default. No automatic outlier deletion.
- Leakage/look-ahead controls: not applicable to descriptive/hypothesis-test
  parity. Any future predictive functionality requires a separate approved plan.

## M0 one-sample t-test specification

- Consumer: `gghistostats` walking skeleton.
- Input: one named numeric Polars column, a finite scalar test value, confidence
  level strictly between zero and one, and alternative in `two-sided`, `less`,
  or `greater`.
- Sample: drop nulls and record their count; reject NaN and infinities; require at
  least two observations and nonzero sample standard deviation.
- Estimand: population mean and its difference from the test value.
- Test: SciPy one-sample Student t-test with sample standard deviation using
  `ddof=1`; statistic `(mean - test_value) / (s / sqrt(n))`; `df = n - 1`.
- Interval: two-sided Student-t confidence interval for the population mean at
  `conf_level`. For one-sided tests the same two-sided estimation interval is
  retained and labeled as such.
- Effect size: Cohen's one-sample `d = (mean - test_value) / s`, with the sample
  standard deviation. Effect-size uncertainty is not implemented in M0 and the
  result must carry an explicit prototype warning.
- Upstream adaptation: pinned `ggstatsplot` reports Hedges' g with an ncp
  interval and accepts the retained non-finite and zero-variance boundary
  fixtures. The M0 Python contract instead reports Cohen's d without an interval
  and rejects both boundary states. Oracle verification treats these as explicit
  adaptations while requiring parity for the t statistic, degrees of freedom,
  p-value, sample counts, mean interval, and independently computed Cohen's d.
- Presentation: retain full precision in the result; round only the subtitle.
- Randomness: none.
- Missing features: Bayesian/nonparametric/robust modes, effect-size interval,
  centrality configuration, annotation overrides, grouped plots, and full R
  argument parity are outside the walking skeleton.

## Model and numerical specification

- Statsmodels class/version: no Statsmodels model is used by the M0 prototype;
  the locked version remains the default for future regression/ANOVA work.
- Polars-to-model boundary: validate one selected series, drop declared nulls,
  copy to a one-dimensional float64 NumPy array, assert shape and finiteness.
- Formula/design matrix/intercept/weights/covariance: not applicable to M0.
- Multiple testing: none in M0. Future pairwise/matrix families must define the
  family and correction before tests are run.
- Random seeds: owned `numpy.random.Generator` required for future stochastic
  code; seed equality is not a cross-language reproducibility claim.
- Numerical tolerances: analytic M0 cases use `rtol=1e-12`, `atol=1e-12` for
  mean, sample deviation, t statistic, df, p-value, and interval on well-scaled
  fixtures. Oracle tolerances may differ only through reviewed method records.

## M2 classical frequentist proposal

`docs/M2_STATISTICAL_METHODS.md` specifies the approved labeled-dot summaries,
grouped test-family scope, Pearson correlation and Fisher interval, pairwise
correlation-matrix missingness, Holm adjustment, grouped correction scopes, and
resource limits. Joshua Myers approved U2, G1, C1, C2, and G2 without revision
on 2026-09-14; the earlier U1 approval remains in force.

## M3 classical comparison proposal

`docs/M3_STATISTICAL_METHODS.md` specifies Welch independent comparisons,
Holm-adjusted pairwise Welch contrasts, explicit-subject paired comparisons,
Greenhouse–Geisser-corrected repeated-measures ANOVA, complete-block repeated
pairwise tests, grouped correction scopes, and resource limits. Joshua Myers
approved B1–B3/G3 and W1–W3/G4 without revision on 2026-09-14.

## M4 classical categorical proposal

`docs/M4_STATISTICAL_METHODS.md` specifies approved raw/count-weighted one-way Pearson
goodness-of-fit, independent Pearson association, exact two-category paired
inference, pairwise and stratum Holm families, noncentral effect intervals,
strict sparse-table failure, and grouped correction scope. C1–C5/G5 and the
count/resource/tolerance policy were approved by Joshua Myers without revision
on 2026-09-14.

## Diagnostics and validation

- Identification/rank/residual diagnostics: method-specific; not applicable to
  the M0 one-sample test beyond minimum sample, finite values, and nonzero scale.
- Baselines: analytic calculations and SciPy results are compared separately to
  frozen R results. The R oracle is not the only reference.
- Sensitivity: include location/scale transformations, row permutations where
  valid, category relabeling/order, ties, extreme but finite values, and method
  boundary cases.
- Calibration: stochastic intervals require repeated-simulation coverage
  studies with declared error bounds and retained aggregate evidence.
- Failure thresholds: mismatched sample, method metadata, df, sidedness,
  correction, interval target, or non-finite output is blocking regardless of
  rounded visual similarity.
- Development/selection/final boundary: tune tolerances and designs on
  development fixtures; lock them before evaluating held-out fixtures.

## Evidence and approval

- Commands and artifacts: `make check`, `uv build`, oracle generator command,
  `docs/upstream/manifest.json`, method specs, and hashed parity fixtures.
- Evidence schemas: checked-in schema-v1 files under `schemas/`, including
  `categorical-result.schema.json`.
- Results: report estimates and uncertainty, never p-values alone.
- Invalidating conditions: unsupported method/parameter combination, violation
  of the accepted license posture, unreviewed statistical spec, oracle drift,
  failed diagnostics, or stale dependency lock.
- Monitoring/rollback: run parity and numerical-drift suites on dependency
  updates. Yank and patch a defective release; never silently revise a result.
- Approval: Joshua Myers approved the M0 one-sample specification and documented
  upstream adaptations on 2026-09-14 and approved the M2 classical
  specification on the same date. Joshua Myers approved the M3 classical
  comparison specification and the M4 classical categorical specification on
  2026-09-14. Later method families require separate approvals under this plan.
