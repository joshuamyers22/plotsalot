# M3 Classical Comparison Method Specification

- Status: Approved
- Version: 0.1.0
- Date: 2026-09-14
- Statistical owner/reviewer: Joshua Myers
- Applies to: M3's first supported mode for each between- and within-group
  statistical surface

## Provenance and compatibility target

This specification was prepared against:

- `ggstatsplot@7a724cd0ab55668b9d0b2e84b12c711c5be68ac8`, the approved
  upstream revision in `docs/upstream/manifest.json`;
- `statsExpressions` 2.1.1 at tag commit `f993d5f3`, the statistical backend
  pinned in `oracle/renv.lock`;
- SciPy 1.18.1 and Statsmodels 0.15.0, pinned in `uv.lock`.

The pinned upstream defaults to Welch tests for independent parametric designs,
unbiased effect sizes, Holm pairwise adjustment, paired t tests for two repeated
conditions, and repeated-measures ANOVA for three or more conditions. Upstream
behavior is one reference, not proof of correctness. The Python methods below
are specified independently and deliberately adapt subject identity,
missingness, pairwise, effect-size, and result-retention behavior where needed
for an auditable contract.

## Common data and reporting policy

- Inputs are Polars dataframes and explicit column names. The response column
  must have a numeric dtype. Comparison, subject, and outer-group identities
  must be stable Polars scalars that serialize unambiguously to JSON.
- Comparison levels use an explicit ordered categorical order when supplied;
  otherwise they use ascending scalar order (false before true, numeric or
  temporal order, and Unicode code-point string order). Input-row permutations
  never change the resolved level order, pairing, or values within a named
  contrast.
- Null removal is method-specific below. Every result records input, retained,
  analyzed, and excluded counts at each relevant row, level, subject, and
  comparison boundary.
- NaN or infinite values in a participating numeric column fail the entire
  operation. They are never converted to null or silently removed.
- Caller data is not mutated. Analysis owns read-only float64 values and owned
  immutable identity arrays.
- No automatic outlier removal, imputation, variance pretest, or assumption-
  based method switching is performed.
- The first M3 slice is two-sided and parametric. `alternative="two-sided"`,
  `p_adjust="holm"`, and `p_adjust="none"` are the supported inferential
  choices. Other alternatives and correction methods fail explicitly.
- `conf_level` and `alpha` must be finite and strictly between zero and one.
  Full-precision values are retained; rounding affects presentation only.
- A pairwise display choice controls rendered brackets only. All computed
  hypotheses, estimates, intervals, raw probabilities, adjusted probabilities,
  significance flags, and family metadata remain in the typed result.
- Confidence intervals for individual pairwise mean differences are pointwise,
  not simultaneous. Holm controls the declared family of p-values; the result
  labels the distinct interval and test scopes so their interpretations cannot
  be conflated.

## B1: Two independent groups

`ggbetweenstats(data, x, y, ...)` selects B1 when exactly two non-null levels of
`x` remain. Rows with null `x` or null `y` are removed before levels are formed.
Both levels must contain at least two observations and have positive finite
sample variance.

The estimand is the population mean difference `mu_1 - mu_2`, oriented from the
first comparison level to the second. The hypothesis is `H0: mu_1 - mu_2 = 0`
against the two-sided alternative.

- The test is Welch's independent-samples t test. With sample means `m_i`,
  variances `s_i^2`, and sizes `n_i`, the statistic is
  `(m_1 - m_2) / sqrt(s_1^2/n_1 + s_2^2/n_2)`.
- Degrees of freedom use the Welch–Satterthwaite expression
  `(v_1 + v_2)^2 / (v_1^2/(n_1-1) + v_2^2/(n_2-1))`, where
  `v_i = s_i^2/n_i`.
- The two-sided p-value uses the Student-t survival function at those degrees of
  freedom.
- The confidence interval targets `mu_1 - mu_2` and is the observed difference
  plus or minus the two-sided Student-t critical value times the Welch standard
  error.
- The standardized effect is Hedges' g using the unpooled root-mean-square
  standardizer `sqrt((s_1^2 + s_2^2)/2)`. Cohen's standardized difference is
  multiplied by the exact gamma-function small-sample correction
  `J(r)=Gamma(r/2)/(sqrt(r/2)*Gamma((r-1)/2))` at `r=n_1+n_2-2`.
  Its orientation matches the mean difference.
- An effect-size interval is not part of the first supported slice. The result
  represents that absence explicitly and compatibility is adapted rather than
  claiming full upstream effect-size parity.

The result also retains per-level arithmetic means, sample deviations, and
two-sided Student-t intervals for each population mean. These intervals are
descriptive and receive no multiplicity correction.

## B2: Three or more independent groups

`ggbetweenstats` selects B2 when three through twenty non-null levels of `x`
remain. Rows with null `x` or null `y` are removed before levels are formed.
Each retained level must contain at least two observations and have positive
finite sample variance.

The omnibus hypothesis is equality of all population means against the
alternative that at least one differs.

- The test is Welch's unequal-variance one-way ANOVA, matching
  `scipy.stats.f_oneway(equal_var=False)` and an independently implemented Welch
  weight/denominator calculation.
- With `w_i=n_i/s_i^2`, `W=sum(w_i)`, weighted mean
  `m_w=sum(w_i*m_i)/W`, and
  `A=sum((1-w_i/W)^2/(n_i-1))`, the statistic is
  `[sum(w_i*(m_i-m_w)^2)/(k-1)] / [1+2*(k-2)*A/(k^2-1)]` and its denominator
  degrees of freedom are `(k^2-1)/(3*A)`.
- The result retains the F statistic, numerator degrees of freedom `k-1`,
  Welch–Satterthwaite denominator degrees of freedom, and upper-tail
  probability.
- The omnibus effect is partial omega squared derived from the Welch F statistic:
  `max(0, df_1 * (F - 1) / (df_1 * F + df_2 + 1))`. The result names this
  conversion explicitly; it is not presented as raw sums-of-squares omega
  squared.
- An omnibus effect-size interval is not supported in the first slice and is
  represented explicitly as absent.

Per-level means, sample deviations, and pointwise Student-t mean intervals are
retained for the renderer and sample audit.

## B3: Independent pairwise comparisons

B2 computes every unordered comparison in resolved level order. For `k` levels,
the correction family contains exactly `k * (k - 1) / 2` hypotheses.

- Each comparison uses B1's Welch statistic, Welch degrees of freedom,
  two-sided raw p-value, mean-difference interval, and Hedges' g definition.
- Holm's step-down Bonferroni method is the default and is implemented through
  Statsmodels plus an independent ordered cumulative-maximum calculation.
  `p_adjust="none"` retains raw and adjusted values as identical.
- Contrast orientation is always earlier level minus later level. Comparison
  order is lexicographic over the resolved level positions, never over rendered
  labels or observed p-values.
- `pairwise_display` supports `"significant"`, `"non-significant"`, `"all"`,
  and `"none"`. Significance and bracket filtering use the adjusted p-value and
  `pairwise_alpha`; no display choice changes the result family.
- Pairwise comparisons are retained whether or not the omnibus test rejects.
  The result makes no protected-testing or gatekeeping claim.

This is an adapted pairwise contract. The pinned upstream labels unequal-
variance pairwise comparisons as Games–Howell before applying the requested
adjustment. The first Python slice instead uses individually inspectable Welch
contrasts followed by one declared Holm family. It must not label those
comparisons Games–Howell or claim numerical equivalence for their probabilities.

## G3: Grouped independent comparisons

`grouped_ggbetweenstats` splits on one explicit outer-group column. Rows with a
null outer-group value are excluded and counted at the grouped-container level.
Non-null outer groups use first-observed order.

Each outer group independently applies B1 or B2/B3 based on its own retained
comparison levels. B3 correction occurs separately inside each B2 result. No
correction is applied across outer groups, and the grouped result records
`correction_scope="within_each_comparison_result_none_across_outer_groups"`.

The operation is atomic. An invalid outer group identifies that group and
returns no partial grouped result.

## W1: Two repeated conditions

`ggwithinstats(data, x, y, subject_id=..., ...)` selects W1 when exactly two
non-null conditions remain. An explicit `subject_id` is mandatory; row-position
pairing is unsupported because it can silently change the scientific unit.

Rows with null subject or condition identities are excluded and counted. Before
null response values are removed, more than one row for a subject-condition cell
is an error, including duplicates where one value is null. Subjects missing a
finite response in either condition are excluded as incomplete pairs. Only the
same complete pairs are plotted and analyzed.

At least three complete subjects and positive finite variation in the paired
differences are required. The estimand is the population mean of
`condition_1 - condition_2`, oriented by resolved condition order.

- The test is the paired Student t test on the owned vector of within-subject
  differences, with statistic `mean(d) / (sd(d)/sqrt(n))`, `df=n-1`, and a
  two-sided p-value.
- The confidence interval targets the population mean paired difference and
  uses the two-sided Student-t critical value with `df=n-1`.
- The standardized effect is Hedges' g-z: Cohen's `d_z=mean(d)/sd(d)` multiplied
  by the exact gamma-function correction `J(n-1)`.
- An effect-size interval is not included in the first slice and is represented
  explicitly as absent.

The result retains condition means and intervals for description, but paired
inference is always computed from subject-aligned differences.

This is adapted from upstream: an omitted subject identifier is rejected, and
partial subjects are excluded from both the plot and analysis instead of being
plotted without contributing to inference.

## W2: Three or more repeated conditions

`ggwithinstats` selects W2 when three through twenty conditions remain. The W1
identity, duplicate-cell, null, and complete-subject rules apply across the full
condition block. At least three complete subjects are required.

The omnibus hypothesis is equality of all condition means in a one-factor
repeated-measures design.

- The uncorrected statistic uses the standard complete-block decomposition into
  condition, subject, and residual sums of squares. It retains F,
  `df_1=k-1`, and `df_2=(n-1)(k-1)`.
- Greenhouse–Geisser epsilon is computed from the sample covariance projected
  into the within-condition contrast space. For
  `C=I_k-(1/k)11'`, sample covariance `S`, and `A=CSC`, epsilon is
  `trace(A)^2 / ((k-1)*trace(A^2))`, clipped to its mathematical range
  `[1/(k-1), 1]` for floating-point noise. A nonpositive denominator fails the
  method as a degenerate repeated-measures design.
- The result retains both uncorrected and Greenhouse–Geisser-corrected degrees
  of freedom and p-values. The corrected p-value is primary for `k>=3`; there
  is no data-dependent Mauchly-test switch.
- The omnibus effect is partial omega squared from the uncorrected F and degrees
  of freedom using the B2 conversion. The result identifies that construction
  and does not imply correction by epsilon.
- An omnibus effect-size interval is not supported in the first slice.

Always reporting the corrected primary p-value avoids a fragile preliminary
sphericity test while retaining the uncorrected value for transparent
comparison with upstream and independent references.

## W3: Repeated pairwise comparisons

W2 computes all condition pairs using the same complete-block subject cohort as
the omnibus analysis.

- Each contrast applies W1's paired t test, mean-difference interval, and
  Hedges' g-z to its condition difference vector.
- The Holm/none, family size, ordering, display, alpha, retention, and no-
  gatekeeping rules from B3 apply.
- Pair-specific availability never changes the cohort. A subject excluded from
  the complete omnibus block is excluded from every W3 contrast, making sample
  counts and family membership stable.

## G4: Grouped repeated comparisons

`grouped_ggwithinstats` applies W1 or W2/W3 inside each non-null outer group.
The subject key is `(outer_group, subject_id)`, so the same subject scalar may
appear safely in different outer groups.

Holm correction is separate within each W3 family and is not pooled across
outer groups. The grouped result records
`correction_scope="within_each_repeated_result_none_across_outer_groups"` and
fails atomically with the invalid outer-group identity. Subject identity is
scoped by the composite key, so the same raw subject scalar may be reused safely
in different outer groups.

## Rendering policy

- Between-group figures contain owned violin, Tukey box, retained-observation,
  mean, mean-interval, and typed statistical-annotation layers. Within-group
  figures use the same distribution summaries plus subject paths sourced from
  the complete analyzed block.
- Any horizontal point displacement is deterministic from retained row/subject
  position and does not use global or caller random state.
- A bracket is rendered only from a retained pairwise result satisfying the
  display rule. Its endpoints, height order, and text are deterministic.
- Subtitles identify the test, estimand orientation where applicable, statistic,
  degrees of freedom, p-value, effect, confidence level, analyzed sample, and
  correction/correction scope where applicable.
- Renderers consume typed results and owned analyzed values. They never rerun a
  test, correction, effect-size calculation, or subject matching operation.
- `results_subtitle=False` may suppress the rendered statistical subtitle, but
  never removes the typed result.

## Resource limits

- Maximum input rows: 1,000,000 by default.
- Maximum comparison levels or conditions: 20 by default.
- Maximum outer groups: 20 by default.
- Maximum pairwise hypotheses: 190, implied by the twenty-level ceiling.
- Maximum rendered observations: 1,000,000 by default.
- Maximum rendered subject paths: 10,000 by default; a larger complete analysis
  may be returned by the analysis-only API, while rendering requires an
  explicit positive override.
- Maximum composed panels: 20 by default.
- Overrides must be explicit positive integers and are retained in result or
  composition provenance wherever they alter an enforced limit.
- No M3 method is stochastic or resampling-based, so no generator or replicate
  budget is used.

## Numerical verification

- Well-scaled analytic values use `rtol=1e-12`, `atol=1e-12` for means,
  deviations, differences, standard errors, t/F statistics, degrees of freedom,
  p-values, intervals, and standardized effects.
- Holm-adjusted probabilities use `rtol=1e-12`, `atol=1e-15` and must also
  satisfy ordering, monotonicity, family-size, and `[0, 1]` invariants.
- Greenhouse–Geisser epsilon and corrected probabilities use `rtol=1e-11`,
  `atol=1e-12`, with independent covariance/projection calculations.
- Extreme-scale fixtures compare scale/translation invariants and finite result
  behavior rather than accepting a wider tolerance without rationale.
- More permissive tolerances require a fixture-specific reviewed conditioning
  rationale. Displayed rounding never defines a tolerance.
- R-oracle differences are classified under ADR-004 and never silently
  relabeled as equivalence.

## Explicitly deferred modes

- Nonparametric independent and repeated tests and their rank effect sizes.
- Equal-variance Student independent tests and ordinary fixed-effects ANOVA.
- Games–Howell, Tukey, Dunn, Durbin–Conover, and arbitrary contrast families.
- One-sided comparison alternatives and correction methods beyond Holm/none.
- Effect-size confidence intervals.
- Robust and Bayesian modes, which remain assigned to M6.
- Multifactor, covariate-adjusted, mixed-effects, and cluster-robust models.

Each deferred public argument must raise a specific unsupported-mode error and
receive an explicit compatibility disposition before M3 closeout.

## Approval requested

Approval of this specification authorizes implementation of B1, B2, B3, G3,
W1, W2, W3, and G4 exactly as written. It does not approve any explicitly
deferred method, alternative, correction, interval, or model.

Joshua Myers approved this specification without revision on 2026-09-14.
