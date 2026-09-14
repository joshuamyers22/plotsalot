# M2 Classical Frequentist Method Specification

- Status: Approved
- Version: 0.1.0
- Date: 2026-09-14
- Statistical owner/reviewer: Joshua Myers
- Applies to: M2's first supported mode for each univariate and correlation
  surface

## Provenance and compatibility target

This specification was prepared against:

- `ggstatsplot@7a724cd0ab55668b9d0b2e84b12c711c5be68ac8`, the approved
  upstream revision in `docs/upstream/manifest.json`;
- `statsExpressions` 2.1.1, the statistical backend pinned in
  `oracle/renv.lock` (tag commit `f993d5f3`);
- `correlation` 0.8.8, pinned in `oracle/renv.lock`;
- SciPy 1.18.1 and Statsmodels 0.15.0, pinned in `uv.lock`.

Upstream behavior is one reference, not proof of correctness. Python methods
below are specified independently, tested against analytic fixtures, and
classified as adapted wherever the initial renderer or API is narrower.

## Common data policy

- Inputs are Polars dataframes and explicit column names.
- Required analysis columns must have numeric dtypes. Label and grouping columns
  may use stable scalar Polars dtypes that can be represented unambiguously in a
  JSON-safe result.
- Null removal is operation-specific below. Every result records input,
  analyzed, and dropped-row counts at the level where removal occurs.
- NaN or infinite values in a participating numeric column fail the entire
  operation; they are never converted to null or silently removed.
- Caller data is not mutated. The analysis owns read-only float64 arrays.
- No automatic outlier removal is performed.
- `conf_level` must be finite and strictly between zero and one.
- All tests are two-sided in the first M2 association slice. The already
  approved one-sample method retains its approved alternatives.

## U1: Parametric histogram

`gghistostats` retains the M0-approved one-sample Student t-test, two-sided
Student-t interval for the population mean, and Cohen's d standardized by the
sample standard deviation (`ddof=1`). Nulls in `x` are dropped. At least two
finite observations and nonzero sample variation are required.

Compatibility remains adapted: upstream reports Hedges' g with a noncentral-t
interval, while the initial Python result reports Cohen's d without effect-size
uncertainty. The limitation remains a typed warning and documented limitation;
it is not described as numerical equivalence for effect size.

## U2: Parametric labeled dot plot

`ggdotplotstats(data, x, y, ...)` uses two related result levels:

1. The plot-level subtitle uses the U1 one-sample method over all retained `x`
   observations.
2. Each distinct non-null `y` label receives a descriptive arithmetic mean and
   a two-sided Student-t confidence interval for its population mean.

Rows with null `x` or null `y` are dropped before either level is computed.
Labels are ordered by ascending mean, with first-observed order breaking exact
ties. Per-label sample counts and dropped-row counts are retained.

For a label with at least two observations and nonzero variation, its interval
uses the sample standard deviation (`ddof=1`) and `t_(1-alpha/2, n-1)`. For a
singleton or constant label, the mean point is retained, the interval is absent,
and a typed warning identifies that label. These descriptive intervals receive
no multiplicity adjustment. The overall U1 test is the only hypothesis test in
the first dot-plot mode.

The first renderer is adapted: it provides labeled estimates, optional error
bars, and the overall one-sample annotation, but does not claim pixel parity or
arbitrary ggplot layer compatibility.

## G1: Grouped univariate plots

`grouped_gghistostats` and `grouped_ggdotplotstats` split on one explicit
grouping column. Rows with a null grouping value are excluded and counted at
the grouped-container level. Non-null groups follow first-observed order.

Each group independently applies U1 or U2 and retains its own sample audit.
Results are atomic: if any group violates the selected method's requirements,
the operation fails with the group identity and returns no partial grouped
result.

The individual group tests are presented as separate panel analyses. M2 does
not adjust p-values across groups and does not make a joint family-wise claim.
The grouped result records `correction_scope = "none_across_groups"` so this
choice cannot be mistaken for an adjusted family.

## C1: Parametric scatter correlation

`ggscatterstats` estimates the population Pearson product-moment correlation
for paired observations and tests `H0: rho = 0` against `H1: rho != 0`.

- Rows are pairwise retained only when both selected values are non-null.
- At least four pairs and nonzero variation in both columns are required. The
  four-pair minimum guarantees a defined Fisher-transformation standard error.
- Inputs that trigger SciPy's constant or near-constant correlation warnings are
  rejected instead of returning an unreliable estimate.
- The coefficient and two-sided p-value use `scipy.stats.pearsonr` with its
  default exact beta-distribution null calculation.
- Degrees of freedom are `n - 2`. The reported Student statistic is
  `r * sqrt((n - 2) / (1 - r**2))` when `abs(r) < 1`.
- Exact perfect correlation is accepted with `r = +/-1`, `p = 0`, a degenerate
  interval at the coefficient, and no finite Student statistic. The typed test
  field is therefore nullable only for this declared boundary case.
- The two-sided coefficient interval uses the Fisher transform:
  `z = atanh(r)`, standard error `1 / sqrt(n - 3)`, normal critical value, and
  inverse `tanh` transform. SciPy's default `confidence_interval` result is a
  locked cross-check, not the sole implementation oracle.

The first scatter renderer shows the retained pairs and typed correlation
annotation. Regression smoothing, marginal histograms, jitter, and dynamic
point-label expressions are deferred and rejected explicitly; the initial
surface is therefore adapted.

## C2: Parametric correlation matrix

`ggcorrmat` accepts an explicit ordered list of two through fifty numeric
columns. For each unique off-diagonal pair it applies C1 using pairwise-complete
rows and records both column identities, `n`, `r`, interval, raw p-value,
adjusted p-value, and significance flag.

- Each unordered off-diagonal pair is one hypothesis in the matrix family.
- The default adjustment is Holm's step-down Bonferroni procedure, implemented
  with `statsmodels.stats.multitest.multipletests(method="holm")` and
  independently checked from the ordered cumulative-max formula.
- `p_adjust = "none"` is also supported and retains identical raw and displayed
  p-values. Other adjustment methods are rejected in the first slice.
- `sig_level` must be finite and strictly between zero and one. Significance is
  determined from adjusted p-values when Holm is selected.
- Diagonal cells contain `r = 1`, the non-null count for that column, no test,
  no p-value, and no confidence interval; they are excluded from correction.
- Estimate, count, and test matrices are symmetric even when the renderer shows
  only one triangle. Column order follows the caller's explicit order.
- Any selected column with a non-finite value fails the whole operation. A pair
  with fewer than four complete rows or invalid variation identifies the pair
  and fails atomically rather than producing a partially valid matrix.

The renderer is a semantic heatmap with coefficients and explicit
non-significance markers. Pixel parity is not required.

## G2: Grouped association plots

`grouped_ggscatterstats` and `grouped_ggcorrmat` use the G1 group selection,
ordering, null-group handling, atomicity, and resource limits. C1 scatter tests
receive no correction across groups and record
`correction_scope = "none_across_groups"`. C2 applies Holm correction separately
within each group's matrix and records
`correction_scope = "within_group_matrix"`; it does not pool hypotheses across
groups.

## Resource limits

- Maximum input rows: 1,000,000 by default.
- Maximum groups: 20 by default.
- Maximum correlation-matrix variables: 50.
- Maximum labeled dot-plot labels: 200 by default, bounding one point/error-bar
  artist per label; an explicit positive override is supported.
- Overrides must be explicit positive integers and are retained in result
  provenance where they alter an enforced limit.
- M2 contains no stochastic or resampling method, so no random generator or
  replicate budget is used.

## Numerical verification

- Well-scaled analytic values use `rtol=1e-12`, `atol=1e-12` for means,
  standard deviations, t statistics, Pearson coefficients, p-values, and
  independently computed intervals.
- Holm-adjusted p-values use `rtol=1e-12`, `atol=1e-15` and must also satisfy
  ordering, monotonicity, and `[0, 1]` bounds.
- More permissive tolerances require a fixture-specific reviewed rationale for
  conditioning; displayed rounding never defines a tolerance.
- R-oracle differences are classified under ADR-004 and never silently
  relabeled as equivalence.

## Approval requested

Approval of this specification authorizes implementation of U1, U2, G1, C1,
C2, and G2 exactly as written. It does not approve nonparametric, robust,
Bayesian, partial-correlation, resampling, regression-smoothing, or additional
multiplicity modes.

Joshua Myers approved this specification without revision on 2026-09-14.
