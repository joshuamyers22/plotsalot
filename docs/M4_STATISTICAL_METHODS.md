# M4 Classical Categorical Method Proposal

- Status: Approved
- Version: 0.1.0
- Date: 2026-09-14
- Statistical owner/reviewer: Joshua Myers
- Applies to: the first supported M4 mode for categorical bar and pie surfaces

## Approval boundary

This file specifies the approved C1–C5 and G5 methods from `MILESTONE_4.md`.
Joshua Myers approved the proposal without revision on 2026-09-14, as recorded
in `evidence/M4_SIGNOFF.md`.

The proposed first slice is deterministic, two-sided, and classical:

- `type="parametric"` only;
- `alternative="two-sided"` only;
- `conf_level=0.95` by default;
- `p_adjust="holm"` or `"none"`;
- no automatic exact/asymptotic method switch;
- no Bayesian, Monte Carlo, resampling, or caller-visible randomness.

## Provenance and compatibility target

The proposal was prepared against:

- `ggstatsplot@7a724cd0ab55668b9d0b2e84b12c711c5be68ac8`;
- the statsExpressions backend pinned in `oracle/renv.lock`;
- SciPy 1.18.1 and Statsmodels 0.15.0 pinned in `uv.lock`.

The pinned upstream categorical core uses Pearson chi-square tests without
continuity correction for one-way and independent two-way designs, McNemar's
test without continuity correction for paired two-way designs, Cramér's V or a
related categorical effect, Fisher exact pairwise tables, per-stratum
goodness-of-fit labels, and optional count expansion. Python deliberately
adapts several details below for bounded computation, exact count ownership,
multiplicity integrity, and inspectable uncertainty.

## Common table, count, and reporting policy

- Inputs are a Polars dataframe, required categorical `x`, optional categorical
  `y`, optional integer `counts`, and optional outer `group` column. Supplied
  column names must be non-empty and distinct.
- With `counts=None`, each retained physical row has weight one. With `counts`,
  every non-null weight must be a nonnegative integer exactly representable as
  signed 64-bit, and the analyzed weighted total must not exceed the configured
  default of 1,000,000,000. Boolean, floating, negative, or overflowing count
  values fail. Zero counts are valid sampling zeros.
- Aggregate counts are summed directly by cell and are never expanded into
  repeated rows. Statistically equivalent raw and aggregate inputs must return
  identical tables, tests, effects, intervals, and displayed proportions.
- Rows null in `x`, applicable `y`, or `counts` are omitted once at the shared
  boundary and audited by reason. If multiple required fields are null in one
  row, a fixed precedence (`x`, then `y`, then `counts`) assigns that physical
  row to exactly one exclusion count. Null outer-group rows remain audited at
  the grouped boundary.
- Category identities are non-empty strings, booleans, integers, or finite
  floats. Declared Enum order is used when present; otherwise categories use
  deterministic scalar order (false before true, numeric ascending, strings by
  Unicode code point). Mixed identity types in one category column fail.
- The table is the ordered Cartesian product of resolved `x` and `y` levels.
  Zero observed cells are retained. A wholly empty margin in an independent or
  paired table fails; structural-zero models are not inferred.
- Reordering physical rows never changes axis order, paired-cell orientation,
  table values, hypothesis membership, or correction order.
- Full-precision finite values are retained. Counts/totals serialize as
  integers; rounding affects presentation only. No public mapping contains NaN
  or infinity.
- There is no category collapsing, imputation, pseudo-count, continuity
  correction, survey weighting, or silent method switching.
- Default ceilings follow the M4 contract: 1,000,000 physical rows, 20 levels
  per categorical axis, 400 cells, 190 pairwise hypotheses, 400 rendered cell
  labels, 20 outer groups, and weighted total 1,000,000,000. Applied limits are
  serialized.

## Expected-count adequacy policy

C1, C2, C4, and C5 use asymptotic Pearson chi-square inference. Each table is
checked after its expected counts are constructed:

- every expected count must be finite and at least 1;
- for a 2x2 table, every expected count must be at least 5;
- for any other table, at least 80% of expected counts must be at least 5.

Failure raises an identified sparse-table error before returning an analysis or
plot. The method does not warn and continue, automatically switch to Fisher's
exact test, pool categories, or run Monte Carlo simulation. Exact sparse-table
methods may be added only under a later approved method record.

Each eligible result retains the minimum expected count, number and fraction of
expected cells below 5, and the adequacy rule that was applied. These diagnostics
describe the predeclared computation; they are not a data-dependent method
selector because failure is terminal.

## Effect-size interval shared construction

C1, C2, C4, and C5 use a two-sided noncentral chi-square interval. Given
observed statistic `q`, degrees of freedom `df`, confidence level `1-alpha`,
and noncentrality `lambda >= 0`, the confidence set is obtained by inverting
the noncentral chi-square CDF:

- the lower endpoint solves `CDF_ncx2(q; df, lambda)=1-alpha/2`, truncated to
  zero when that root would be negative;
- the upper endpoint solves `CDF_ncx2(q; df, lambda)=alpha/2`;
- if the observed central CDF is already below the upper-endpoint tail target,
  so no nonnegative root exists at an exact or near-exact null fit, the upper
  endpoint is the mathematical effect bound rather than a fabricated root:
  `1` for Cramér's V and `sqrt(1/min(p_0)-1)` for Cohen's w under null vector
  `p_0`;
- deterministic bracket expansion and Brent root finding stop only at
  predeclared absolute/relative tolerances or raise a numerical error;
- no finite artificial upper endpoint is substituted after a failed bracket.

For Cohen's `w`, transform with `sqrt(lambda / N)` and cap at its null-vector
bound. For Cramér's `V`, transform with `sqrt(lambda / (N * m))`, where
`m=min(r-1, c-1)`, and cap at one. The estimate itself is computed from the
central Pearson statistic; the interval is an uncertainty statement about the
corresponding population effect under the multinomial model. The method is
named `noncentral_chi_square_equal_tail_bounded`. It is adapted from upstream
where interval sidedness, adjustment, or boundary handling differs.

## C1: One-way goodness-of-fit

`ggbarstats(data, x, y=None, ...)` and `ggpiestats` select C1.

The sampling unit is one retained row or one unit represented by its aggregate
count. The population parameter is the categorical probability vector
`p=(p_1,...,p_k)` in resolved `x` order. At least two resolved levels and a
positive weighted total are required.

The caller's `ratio` is an optional mapping from the exact typed `x` identities
to finite probabilities. It must contain every resolved level exactly once,
contain no unknown level, have all probabilities strictly greater than zero,
and sum to one within absolute tolerance `1e-12`. It is not reordered by string
conversion and is not silently normalized. With `ratio=None`, the null vector is
uniform (`p_i=1/k`).

- Null hypothesis: the population probabilities equal `ratio`.
- Alternative: at least one population probability differs.
- Test: Pearson goodness-of-fit statistic
  `X^2=sum((O_i-N*p_i)^2/(N*p_i))`, with `df=k-1` and upper-tail central
  chi-square p-value; no continuity correction.
- Effect: Cohen's `w=sqrt(X^2/N)`, nonnegative, with the shared noncentral
  chi-square interval.
- Cell records: level identity, observed count, expected count, observed and
  expected proportions, Pearson residual, and chi-square contribution.

The result labels the test `pearson_chi_square_goodness_of_fit` and the effect
`cohen_w`. A zero observed category is valid when its expected probability is
positive. A zero expected probability, a missing ratio level, or failure of the
adequacy policy is invalid.

## C2: Independent two-way association

`ggbarstats(data, x, y, paired=False, ...)` and `ggpiestats` select C2.

The sampling unit is one independently sampled retained row or one unit
represented by its aggregate cell count. `x` has `r>=2` levels, `y` has `c>=2`
levels, and `N>0`. The table orientation is rows=`x`, columns=`y` for analysis;
renderers may place `y` on the visible bar/facet axis without changing this
identity.

- Null hypothesis: `x` and `y` are independent.
- Alternative: they are associated.
- Expected count: `E_ij=row_total_i*column_total_j/N`.
- Test: Pearson independence statistic
  `X^2=sum((O_ij-E_ij)^2/E_ij)`, `df=(r-1)(c-1)`, upper-tail central chi-square
  p-value, and no Yates or other continuity correction.
- Effect: uncorrected Cramér's
  `V=sqrt(X^2/(N*min(r-1,c-1)))`, nonnegative, with the shared noncentral
  chi-square interval.
- Cell records: typed row/column identities, observed/expected counts,
  within-`y` displayed proportion, joint proportion, Pearson residual, and
  chi-square contribution.

No signed direction is attached to Cramér's V. Direction and cell structure are
available through the residuals and ordered table. Empty margins and tables
failing expected-count adequacy fail explicitly.

## C3: Paired two-category table

`ggbarstats(data, x, y, paired=True, ...)` and `ggpiestats` select C3 only when
`x` and `y` describe two categorical measurements on the same physical row and
resolve to the same two typed category identities in the same deterministic
order. Count-weighted rows represent repeated identical pairs. A subject column
is not required because the experimental unit is already the row-wise pair;
null in either measurement removes the entire pair and is audited.

Let the ordered categories be `(level_1, level_2)`, `b` the cell
`x=level_1, y=level_2`, and `c` the cell `x=level_2, y=level_1`.

- Null hypothesis: the two discordant transition probabilities are equal,
  equivalently `Pr(level_1 -> level_2 | discordant)=0.5`.
- Alternative: they differ.
- Test: exact two-sided binomial test of `b` successes among `b+c` discordant
  pairs at probability 0.5. The two-sided probability uses SciPy's documented
  probability-ordering definition, not a doubled one-sided approximation.
- Effect: signed Cohen's `g=b/(b+c)-0.5`, in `[-0.5,0.5]`. Positive values mean
  `level_1 -> level_2` discordance is more common under the recorded orientation.
- Interval: transform the two-sided exact Clopper–Pearson interval for the
  discordant transition probability by subtracting 0.5.

At least one discordant pair is required. A no-discordance table fails as
uninformative rather than returning an arbitrary full-width interval. More than
two paired categories, nonsquare support, asymptotic McNemar, continuity
correction, Stuart–Maxwell/Bowker tests, and automatic paired-method selection
are deferred. This is deliberately adapted from upstream's uncorrected
asymptotic McNemar path.

C4 and C5 are not computed for paired designs. Requests enabling those displays
with `paired=True` fail rather than being ignored.

`ratio` is invalid for C3. For C2 it is valid only when C5 is enabled; supplying
it while `proportion_test=False` fails as an unused inferential argument.

## C4: Independent pairwise association family

C4 is computed by default when C2 has at least three `x` levels. For `r` levels,
the family contains exactly `r*(r-1)/2` hypotheses in lexicographic resolved
level order. Each member subsets two `x` levels while retaining the resolved
`y` domain; a resulting empty `y` margin or expected-count failure identifies
the pair and fails the entire analysis atomically.

- Null hypothesis: within the selected pair of `x` levels, `x` and `y` are
  independent.
- Test: the C2 Pearson statistic on the 2x`c` table, no continuity correction,
  with `df=c-1` and a two-sided/upper-tail chi-square probability.
- Effect: Cramér's V and its shared noncentral chi-square interval.
- Estimate orientation: hypothesis identity is earlier `x` level versus later
  level; Cramér's V itself remains unsigned.
- Correction: Holm step-down Bonferroni across the complete C4 family by
  default. `p_adjust="none"` makes adjusted values equal raw values.
- Retention: pair identities, subtable, statistic, df, raw/adjusted p-values,
  effect and interval, adequacy diagnostics, alpha, and significance are always
  retained.

`pairwise_display` supports `"significant"`, `"non-significant"`, `"all"`, and
`"none"` and filters renderer annotations only. It never changes C4 computation
or serialization.

The pinned upstream family uses Fisher's exact test. Python's first slice uses
the bounded asymptotic Pearson method under the explicit adequacy gate, so this
family is classified adapted. Fisher–Freeman–Halton enumeration, Monte Carlo
Fisher inference, and odds-ratio output are deferred.

## C5: Within-stratum goodness-of-fit family

C5 is available only for C2. With `proportion_test=True` (the default), it
contains one C1-style goodness-of-fit hypothesis for every resolved `y` stratum,
using the common `x` ratio and only that stratum's total. Every stratum must
contain positive analyzed weight and pass the expected-count adequacy policy.

- Null hypothesis for stratum `j`: `Pr(x | y_j)` equals the common ratio.
- Test/effect/interval: C1 Pearson goodness-of-fit, Cohen's w, and noncentral
  chi-square interval using the stratum total.
- Family order: resolved `y` order.
- Correction: Holm across all `y` strata by default, or none when explicitly
  requested. Raw and adjusted probabilities are both retained.
- Scope: C5 is separate from the C2 omnibus and C4 pairwise family. No combined
  correction is claimed.

`proportion_test=False` omits the C5 family explicitly. A display selector may
hide C5 labels without deleting retained results. The pinned upstream displays
unadjusted per-stratum goodness-of-fit probabilities; the proposed Holm default
is a deliberate multiplicity adaptation.

## G5: Grouped categorical execution

Grouped bar and pie functions split on one explicit outer `group` column using
the established first-observed outer order. Null group rows are removed and
audited at the outer boundary. Category identities and level orders are then
resolved independently within each group for analysis, while the renderer uses
the ordered union of inner `x` identities for one common color/legend mapping.

- Each group receives the same design, ratio mapping, method, confidence level,
  correction, display, count, and resource configuration.
- Each inner C4 and C5 family is corrected only within that inner result. No
  probability correction is pooled across outer groups.
- Count weights contribute only to their physical outer group.
- Reuse of the same category identity in different outer groups is valid and
  maps to the same color. Missing inner categories remain absent from that
  group's analyzed total but present in the common legend domain.
- Any invalid/sparse inner group raises an error naming its typed group identity
  and returns no partial grouped object.
- Grouped bar and grouped pie rendering share the exact tuple of inner typed
  results by object identity.

## Shared structured result

The schema-v1 categorical result must include:

- analysis/design/method identities and `x`, optional `y`, optional `counts`;
- physical-row and weighted-unit sample audit with null-reason counts;
- ordered typed `x`/`y` levels, complete cell records, row/column/grand totals,
  and relevant observed/expected/display proportions;
- omnibus statistic, df, p-value, effect estimate and interval;
- expected-count adequacy metadata where applicable;
- complete C4 and C5 families with separate correction scopes;
- `ratio`, confidence level, alpha, p-adjustment and display policies;
- applied resource ceilings and warnings/adaptations.

Bar and pie analyses return this same result shape. Renderers consume a retained
analysis object and do not recompute table statistics. Every displayed number
must be traceable to a result field. Public serialization contains no Polars,
NumPy, SciPy, Statsmodels, Matplotlib, R, or arbitrary callable object.

## Numerical and independent verification policy

- Integer cells and totals require exact equality.
- Well-scaled analytic Pearson statistics, expected counts, residuals, effects,
  and central probabilities use `rtol=1e-12`, `atol=1e-12` against independently
  written formulas.
- Holm values are checked against Statsmodels and an independent sorted
  cumulative-maximum implementation at `1e-12` tolerance.
- Noncentral chi-square and Clopper–Pearson interval endpoints use
  predeclared `rtol=1e-10`, `atol=1e-12` and are checked against pinned R or a
  second independently implemented inversion.
- Exact binomial probabilities are checked by finite probability enumeration on
  small fixtures as well as SciPy.
- Pinned-R fixtures retain raw ggstatsplot objects for C1, C2, C3, C4, C5, raw
  counts, aggregate counts, bar, pie, and grouped cases. Oracle verification
  compares only fields whose approved methods coincide and asserts every named
  adaptation separately.
- Statistical and renderer fixtures use synthetic redistributable data only.
  R, Docker, and network access remain development-only.

## Explicitly deferred behavior

- `type="bayes"` and Bayesian hypothesis/estimation output (M6);
- Fisher exact/Fisher–Freeman–Halton, Monte Carlo, permutation, resampling, and
  other nonparametric modes not defined above;
- asymptotic McNemar, continuity-corrected McNemar, and paired designs with more
  than two categories;
- automatic sparse-table fallbacks or category pooling;
- one-sided alternatives;
- structural-zero, survey-weight, clustered, hierarchical, multiway,
  log-linear, multinomial, or ordinal models;
- arbitrary ggplot components, R theme objects, dynamic palette lookup, and
  untyped dataframe-output modes.

All deferred selector values fail explicitly or are absent from the Python
signature. They are never accepted and ignored.

## Approval request

Joshua Myers is asked to approve or revise:

1. C1 Pearson goodness-of-fit, strict keyed ratios, Cohen's w, and noncentral
   interval;
2. C2 uncorrected Pearson independence, explicit adequacy failure, Cramér's V,
   and noncentral interval;
3. C3 exact-binomial two-category paired test, signed Cohen's g, and exact
   interval;
4. C4 complete pairwise Pearson/Holm family as an adaptation from upstream
   Fisher tests;
5. C5 per-stratum Pearson/Cohen-w tests with a separate Holm family;
6. G5 atomic grouped scope and common category colors;
7. raw/count-weighted equivalence, fixed resource ceilings, numerical
   tolerances, and all explicit deferrals.

Approval of this proposal authorizes implementation and acceptance fixtures. It
does not approve the later release candidate; that remains a separate gate.

Joshua Myers approved C1–C5/G5 and the count, resource, tolerance, and deferral
policy without revision on 2026-09-14.
