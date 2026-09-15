# M6 Robust and Bayesian Method Specification

- Status: M6A R1–R3/G6 and M6B B1–B6 implemented and accepted; R4 pending
- Version: 0.1.0
- Date: 2026-09-14
- Statistical owner/reviewer: Joshua Myers
- Applies to: approved M6A robust continuous-analysis track
- Companion proposal: `M6B_STATISTICAL_METHODS.md`
- Reserved for later review: R4

## Decision boundary

This specification fixes the first M6A robust estimands and algorithms. Joshua
Myers approved R1–R3, G6, ADR-005, ADR-006, and the stated evidence/resource
policies without revision on 2026-09-14, authorizing M6A implementation and
normative fixture construction.

The resulting implementation and evidence were independently reviewed and
accepted by Joshua Myers on 2026-09-14, closing M6A without authorizing R4 or
B1–B6.

The proposed M6A methods are based on 20% trimmed means and Winsorized
dispersion. “Robust” here means bounded tail contribution to specified location,
association, and comparison estimators. It does not mean assumption-free,
immune to leverage or dependence, universally superior to the classical mode,
or permission to delete observations.

M6A is caller-selected with `type="robust"`. It never activates because a
normality test, outlier rule, residual diagnostic, classical failure, or sample
size threshold fired.

## Provenance and reference basis

The method entry audit used the accepted upstream revision
`ggstatsplot@7a724cd0ab55668b9d0b2e84b12c711c5be68ac8` in the pinned R 4.5.1
oracle. Its robust paths call `statsExpressions==2.1.1`, `WRS2==1.1-7`, and
`correlation`. The inspected backend uses:

- `WRS2::trimcibt` for robust one-sample inference;
- a Winsorized Pearson calculation through `correlation::correlation` for
  robust associations;
- `WRS2::yuen`/`yuend` for independent/dependent two-sample comparisons;
- `WRS2::t1way`/`rmanova` for independent/repeated omnibus comparisons; and
- `WRS2::lincon`/`rmmcp` for robust pairwise comparisons.

The proposal retains the 20% trimmed/Winsorized estimands and the documented
Yuen/Welch-style reference formulas, but deliberately adapts upstream behavior:

- no R global RNG or hidden random work;
- no 100–500 replicate acceptance baseline;
- no hard-coded 95% interval inside an otherwise configurable call;
- no ordinary Pearson degrees of freedom applied to Winsorized observations;
- no stochastic omnibus effect point estimate for unequal group sizes;
- no silent invalid bootstrap replicate, fallback, or method switch; and
- no standardized robust effect until a stable target and interval receive
  separate approval.

Primary references are Yuen's unequal-variance trimmed-mean test
(`doi:10.1093/biomet/61.1.165`), the Wilcox/WRS2 robust-method definitions and
reference manual (`doi:10.3758/s13428-019-01246-w` and the pinned WRS2 1.1-7
manual), and Keselman et al.'s independent/correlated-groups treatment
(`doi:10.1111/1469-8986.00060`). Bootstrap quantiles use the explicitly named
Hyndman–Fan type 7 definition (`doi:10.1080/00031305.1996.10473566`).

## Shared trimmed and Winsorized definitions

For a finite retained sample `x` of size `n` and trim fraction `gamma=0.20`:

1. Sort values ascending with their source audit already fixed.
2. Set `g=floor(gamma*n)` and effective count `h=n-2g`.
3. The 20% trimmed mean `theta` is the arithmetic mean of sorted elements
   `g` through `n-g-1`.
4. The Winsorized sample replaces the lowest `g` values by the first retained
   value and the highest `g` values by the last retained value.
5. `s_w^2` is the ordinary sample variance of the Winsorized values with
   denominator `n-1`.
6. The estimated variance of the trimmed mean is
   `q=(n-1)*s_w^2/(h*(h-1))`, with standard error `sqrt(q)`.

The production kernel must retain `n`, `g`, `h`, the two Winsorization boundary
values, `theta`, `s_w^2`, `q`, and the fixed trim fraction. It must not retain a
sorted caller data copy in the public result.

A usable sample requires `n>=5`, `g>=1`, `h>=3`, finite boundaries/statistics,
and strictly positive Winsorized variance. Null handling and original/analyzed
row reconciliation remain inherited from the applicable M2/M3 sample boundary.
NaN and infinity fail before sorting. Ties are allowed unless they make a
required Winsorized variance/covariance or standard error degenerate.

The first M6A release supports only `gamma=0.20`. The Python keyword is
`trim_fraction`; any other value fails. Fixing rather than tuning the value
limits multiplicity and prevents an apparently cosmetic argument from changing
the estimand after data inspection.

## R1: robust one-sample and centrality inference

### Population and estimand

- Population target: the 20% trimmed location of the distribution represented
  by the retained numeric sample.
- Estimate: `theta`, the sample 20% trimmed mean.
- Null: the population trimmed location equals the finite caller `test_value`.
- Raw effect: `theta-test_value`, in the source measurement units.
- A standardized effect is not reported in M6A. The result carries
  `standardized_effect_unavailable="not_approved_for_m6a"`.

### Test and interval

Set `se=sqrt(q)`, `df=h-1`, and
`t=(theta-test_value)/se`. The p-value uses the Student t distribution with
`df` and the caller-selected `two-sided`, `less`, or `greater` alternative.

The estimation interval is always the two-sided Student-t interval
`theta +/- t_(1-alpha/2,df)*se` at `conf_level`, matching the existing contract
that a one-sided hypothesis still receives a two-sided estimation interval.
The interval targets the population 20% trimmed location, not the ordinary mean
or an individual observation.

This deterministic analytic interval is an adaptation from pinned upstream's
bootstrap-t `trimcibt` path. Oracle evidence must retain both outputs and label
the difference; acceptance is based on the approved Python formula plus
independent calculations, not numeric equality to the upstream bootstrap.

### Consumers and presentation

- `gghistostats(type="robust")` uses R1 for the overall analysis and the
  centrality line/label.
- `ggdotplotstats(type="robust")` uses R1 for its overall test and the same
  trimmed kernel for each label-level centrality interval.
- Grouped variants apply R1 independently after all groups preflight under G6.
- Subtitles name the 20% trimmed-mean t procedure, raw difference, interval
  target, effective count, and absence of a standardized effect.

## R2: robust association and matrix inference

### Population and sample

- Population target: Pearson correlation after marginal 20% Winsorization of
  both variables, denoted `rho_w`.
- Selection: the existing explicit pairwise-complete Polars boundary is used.
- Minimum retained pairs: eight, with `g>=1` and `h=n-2g>=4`.
- Both Winsorized marginal sample variances must be strictly positive.
- Winsorization is marginal; it bounds tail values separately and is not a
  high-breakdown defense against arbitrary bivariate leverage. The result and
  documentation state this limitation.

### Estimate and hypothesis test

Winsorize `x` and `y` using their own sorted boundaries and compute their
ordinary Pearson correlation `r_w`. Under `H0: rho_w=0`, for `abs(r_w)<1` use

`t = r_w * sqrt((n-2)/(1-r_w^2))`

with Student reference degrees of freedom `df=h-2` and a two-sided p-value.
This follows the pinned WRS2 `wincor` test rather than upstream ggstatsplot's
ordinary `n-2` Pearson reference after Winsorization.

If finite arithmetic produces exact `r_w=+/-1`, retain the boundary estimate,
store no finite test statistic, set the limiting two-sided p-value to zero, and
emit `perfect_winsorized_correlation`. Values outside `[-1,1]` beyond the
approved rounding tolerance fail; within tolerance they are clamped and the
clamp is tested.

### Confidence interval

The interval is a paired nonparametric percentile bootstrap of `r_w`:

- `bootstrap_resamples` defaults to 1,999 and must be an odd integer from 999
  through 9,999;
- `random_seed` is a required integer in `[0,2^64-1]`;
- each replicate samples the retained pair indices with replacement, applies
  the same marginal 20% Winsorization, and computes `r_w`;
- the two-sided bounds use Hyndman–Fan type 7 quantiles at
  `(1-conf_level)/2` and `1-(1-conf_level)/2`;
- non-finite or zero-Winsorized-variance replicates are counted as failed rather
  than imputed or redrawn; and
- inference succeeds only with at least
  `max(950,ceil(0.99*bootstrap_resamples))` valid replicates. Otherwise the
  entire association analysis fails.

The result retains requested, valid, and failed replicate counts, the interval
quantile method, root/child seed identity, and work limit. It does not retain
bootstrap samples or replicate estimates.

### Correlation matrix family

`ggcorrmat(type="robust")` computes R2 for every unique variable pair using
the same pairwise-complete population rule as M2. Pair identities and child
seeds are derived before analysis. P-values are adjusted across the full matrix
pair family with Holm by default or left unadjusted only when `p_adjust="none"`.
Intervals remain pointwise and are labeled unadjusted. Significance display is
based on the retained adjusted p-value and never changes matrix membership.

Partial correlation, alternative robust correlation estimators, and one-sided
association tests are not included.

## R3: robust independent and repeated comparisons

### Shared population and centrality

- `type="robust"` retains the existing explicit group/condition order and
  missingness audit.
- Every independent group and every complete repeated condition must have
  `n>=5`, `g>=1`, `h>=3`, and positive Winsorized variance where required.
- Each level reports its 20% trimmed mean and R1 two-sided interval.
- The primary effects are raw trimmed-location differences in outcome units.
  M6A reports no standardized robust effect and records the typed reason
  `robust_standardized_effect_not_approved`.
- Two-level alternatives may be `two-sided`, `less`, or `greater`; omnibus and
  pairwise families are two-sided.

### Two independent groups: Yuen unequal-variance test

For ordered groups 1 and 2, compute `theta_j`, `h_j`, and
`q_j=(n_j-1)*s_wj^2/(h_j*(h_j-1))`. Define:

- estimate `delta=theta_1-theta_2`;
- standard error `se=sqrt(q_1+q_2)`;
- statistic `t=delta/se`; and
- Satterthwaite degrees of freedom
  `df=(q_1+q_2)^2/(q_1^2/(h_1-1)+q_2^2/(h_2-1))`.

The p-value uses the selected Student-t tail. The estimation interval is the
two-sided `delta +/- t_(1-alpha/2,df)*se`, even for a one-sided hypothesis.
Group order and the sign of every estimate/statistic are retained.

### Three or more independent groups: Welch–Yuen omnibus

For `J` groups, set `w_j=1/q_j`, `U=sum(w_j)`, and weighted trimmed location
`theta_w=sum(w_j*theta_j)/U`. Define:

- `A=sum(w_j*(theta_j-theta_w)^2)/(J-1)`;
- `C=sum((1-w_j/U)^2/(h_j-1))/(J^2-1)`;
- `F=A/(1+2*(J-2)*C)`;
- `df1=J-1`; and
- `df2=1/(3*C)`.

The omnibus p-value is the upper tail of `F(df1,df2)`. Nonpositive `q_j`, `C`,
or denominator and non-finite fields fail. No stochastic omnibus effect point
estimate is produced.

All pairwise contrasts use the two-group Yuen formula in stable source level
order. Holm is the default full-family p-value adjustment; `none` is the only
alternative. Contrast intervals are pointwise at `conf_level` and explicitly
unadjusted. `pairwise_display` remains presentation-only.

### Two repeated conditions: trimmed subject-level difference

Use the inherited explicit-subject complete-block population. For each subject,
form the ordered difference `d_i=y_i1-y_i2`, then apply R1 to the difference
sample with null zero. The estimand is the population 20% trimmed subject-level
difference. This is deliberately coherent with multi-condition pairwise
contrasts and is adapted from pinned `WRS2::yuend`, which compares marginal
trimmed locations using Winsorized covariance.

### Three or more repeated conditions: robust repeated omnibus

For a complete `N x J` subject-by-condition matrix:

1. Set `g=floor(0.20*N)` and `h=N-2g`; compute each condition's trimmed mean.
2. Winsorize each condition marginally with the same tail count.
3. Let `qc=h*sum((theta_j-mean(theta))^2)`.
4. Double-center the Winsorized matrix by subject and condition and let `qe` be
   the sum of squared centered residuals.
5. Set `F=qc/(qe/(h-1))`.
6. Compute the WRS2 `rmanova` covariance epsilon from the Winsorized covariance
   matrix; require finite positive numerator/denominator and clamp the retained
   epsilon to `[1/(J-1),1]`.
7. Use `df1=(J-1)*epsilon` and `df2=(J-1)*epsilon*(h-1)` with the upper F tail.

For step 6, let `V` be the `J x J` sample covariance matrix of the Winsorized
condition columns, `v_bar` the mean of all entries, `v_diag` the mean diagonal,
and `v_j` the mean of row `j`. Define

- `A=J^2*(v_diag-v_bar)^2/(J-1)`;
- `B=sum(V_jk^2)-2*J*sum(v_j^2)+J^2*v_bar^2`;
- `e_hat=A/B`; and
- `e_raw=(N*(J-1)*e_hat-2)/((J-1)*(N-1-(J-1)*e_hat))`.

The retained `epsilon` is `e_raw` clamped to `[1/(J-1),1]`. `B<=0`, a
nonpositive `e_raw` denominator, `e_raw<=0`, or a non-finite intermediate fails
rather than substituting the classical Greenhouse–Geisser epsilon.

The result retains the uncorrected dimensions, epsilon inputs/result, corrected
degrees of freedom, `qc`, `qe`, statistic, and p-value. A zero/negative `qe`,
degenerate Winsorized covariance, invalid epsilon denominator, or nonpositive
degree of freedom fails.

Every pairwise repeated contrast forms the ordered subject-level difference and
uses R1 with null zero. Holm/none and pointwise-interval semantics match the
independent family. There is no automatic sphericity switch and no classical
Greenhouse–Geisser fallback.

## G6: grouping, randomness, resources, and presentation

### Mode and argument allowlist

M6A adds `type="robust"` to the existing analysis/render entry points without
changing the classical defaults. Proposed public robust options are:

- `trim_fraction=0.20`, with no other accepted value in M6A;
- `bootstrap_resamples=1999` and required `random_seed` only on R2 association
  paths;
- inherited `alternative`, `conf_level`, `p_adjust`, `pairwise_alpha`,
  `pairwise_display`, and family-specific row/level/label/artist ceilings; and
- `maximum_resample_work=100_000_000`, overridable only to the hard maximum
  `500_000_000`.

Supplying resampling options to deterministic R1/R3 paths fails as unused rather
than being ignored. `centrality_type` is not independently selectable in M6A:
robust mode renders the matching 20% trimmed centrality. Nonparametric values,
other trim fractions, other robust estimators, generic method arguments, and
ellipsis forwarding fail or remain absent.

### RNG and child identities

R2 uses `numpy.random.Generator(numpy.random.PCG64DXSM(seed))` under the locked
NumPy version. For matrices and grouped operations, canonical UTF-8 encodings of
the analysis name and typed variable/group identities are hashed with SHA-256.
The digest plus root seed initializes a NumPy `SeedSequence`; each child receives
one deterministic PCG64DXSM stream.

The mapping is independent of Python `hash()`, worker timing, plotting order,
and failure order. Reordering variables or groups changes presentation order but
the same typed identity under the same root seed receives the same child stream.
Duplicate canonical identities fail during preflight.

M6A execution is synchronous and serial. It adds no worker-count, queue,
cancellation, or progress callback surface. Those behaviors remain deferred.

### Resource accounting

One association resample-work unit is one retained pair sampled for one
bootstrap replicate. A scatter consumes `n*B` units; a matrix or grouped call
consumes the sum across all pair/group analyses. The complete request is
preflighted against `maximum_resample_work` before any random draw or figure.

Bootstrap implementation processes bounded batches of at most 1,000,000 sampled
indices and never allocates the full `B x n` index matrix when that exceeds the
batch limit. The result records the requested/hard work ceiling, calculated
work, batch ceiling, and replicate counts.

All inherited row, variable, level, group, hypothesis, subject-path, label,
point, and composition ceilings remain active. Raising one ceiling never raises
another. No path subsamples rows, drops matrix pairs, reduces resamples, or
suppresses groups to fit a budget.

### Atomic grouped behavior

Grouped robust calls validate all scalar identities, child samples, options,
work, and seeds before analysis. One invalid group, failed robust kernel,
inadequate bootstrap, or renderer failure returns no grouped result. Group
correction families retain their M2/M3 scopes; group-local hypotheses are not
silently pooled across groups.

### Rendering

Renderers consume only typed robust results. They display the 20% trimmed
centrality, approved raw differences, intervals, tests, and family adjustments;
they never sort/truncate data differently or invoke an RNG. Subtitles name
trimmed/Winsorized targets and pointwise versus adjusted inference. Extraction
and composition preserve exact result identity and robust warnings.

## Result contract

The M6A schema revision must retain:

- `analysis`, `mode="robust"`, method name/version, software versions, and
  compatibility tier;
- original sample/group/subject/pair audit and existing resource limits;
- `trim_fraction`, `n`, `g`, `h`, Winsorization bounds, trimmed estimates,
  Winsorized variances/covariances needed to audit displayed inference;
- hypothesis target, null, alternative, statistic, reference distribution,
  degrees of freedom, raw/adjusted p-values, and family identity;
- interval target, method, level, sidedness, and bounds;
- raw difference/effect target and typed standardized-effect absence;
- repeated omnibus correction inputs, epsilon, sums, and corrected degrees of
  freedom when applicable;
- resampling algorithm, RNG/bit-generator, root/child seed identity,
  requested/valid/failed replicates, quantile method, calculated work, batch
  limit, and requested/hard resource ceilings when applicable; and
- stable typed warnings and absence reasons.

Constructors reject cross-field contradictions, including wrong effective
counts, estimates inconsistent with retained kernels, R1/R3 analytic intervals
not containing their two-sided estimate, R2 bounds inconsistent with the
retained percentile algorithm, mismatched test/df/p-value, broken pair
direction, incorrect Holm family, seed/work mismatch, invalid replicate totals,
or robust metadata attached to a classical result. An R2 percentile interval is
not required to contain the point estimate.

## Numerical, oracle, and calibration policy

- Production uses finite `float64`; integer counts/work use exactly represented
  Python integers. Scaling is applied before squared calculations where needed
  and transformed results are mapped back to source units.
- Analytic well-scaled fixtures target `rtol=1e-10`, `atol=1e-12` against
  separately coded equations. Scale-equivariance tests span at least `1e-100`
  through `1e100` where finite representation permits.
- Pinned-R raw objects and normalized WRS2 fields are retained for every R1–R3
  family. Exact parity is required only for identical approved formulas; every
  deliberate difference is asserted and documented.
- R2 same-seed cross-language equality is not expected. Deterministic Python
  replay must be exact under the locked NumPy bit-generator contract. Bootstrap
  interval validation uses independent seeded implementations and simulation
  coverage with predeclared Monte Carlo bounds.
- Calibration studies include symmetric normal, skewed, heavy-tailed,
  heteroscedastic, tied/discrete, and controlled-contamination populations.
  Development simulations select no acceptance threshold after seeing the
  locked validation results.
- Mutation, metamorphic, fault-injection, and boundary tests cover every formula,
  result invariant, seed mapping, work ceiling, and no-fallback condition.
- The retained benchmark separates selection, analytic robust calculation,
  resampling, summarization, and rendering, including 10K/100K/1M analytic
  workloads and R2 accepted/rejected work-boundary cases.

## Compatibility disposition proposed for M6A

| Upstream behavior | Proposed Python disposition |
|---|---|
| `type="robust"` on histogram/dot | Adapted: deterministic analytic 20% trimmed-mean t inference instead of upstream bootstrap-t |
| `tr` | Adapted as `trim_fraction`; fixed at 0.20 in first M6A release |
| robust scatter/matrix | Adapted: WRS2-style effective-df test plus explicit seeded percentile interval instead of ordinary Pearson inference after Winsorization |
| independent robust two-level | Adapted Yuen unequal-variance trimmed-location test with configurable confidence level and raw difference |
| repeated robust two-level | Adapted to trimmed subject-level differences for coherent paired estimand |
| independent robust multi-level | Adapted Welch–Yuen omnibus and Holm pairwise family; standardized omnibus effect deferred |
| repeated robust multi-level | Adapted WRS2-style Winsorized repeated omnibus and trimmed-difference Holm pairs; standardized effect deferred |
| `centrality.type` override | Deferred; robust method and centrality remain aligned |
| upstream hidden/default bootstrap counts | Rejected; explicit B/seed/work plan required |
| automatic/global RNG | Rejected |
| nonparametric mode | Deferred outside M6A |
| robust categorical mode | Not implemented; no advertised pinned upstream mode |
| robust coefficients/meta-analysis | Assigned to M6C/R4 |

## Explicit M6A exclusions

- median/rank/nonparametric tests;
- percentage-bend, skipped, biweight, Spearman, or Kendall association;
- user-selected trimming other than 20%, adaptive trimming, and automatic
  outlier detection/removal;
- standardized robust effects, robust effect-size thresholds, and automatic
  practical-significance language;
- bootstrap-t, BCa, permutation, wild, cluster, block, Bayesian, or generic
  resampling beyond the R2 paired percentile bootstrap;
- incomplete repeated-block imputation or available-case condition pairs;
- partial correlation, covariates, factors/interactions, mixed effects, robust
  regression, or arbitrary contrasts;
- robust categorical analysis and robust coefficient/meta-analysis;
- caller generators, parallel workers, callbacks, cancellation, persisted
  replicates, or external compute; and
- arbitrary upstream/R arguments or plot-layer forwarding.

## Reserved later decisions

R4 robust coefficient/meta-analysis remains intentionally unprepared. B1–B6
were approved on 2026-09-15 in `M6B_STATISTICAL_METHODS.md` and implemented in
the M6B technical candidate. ADR-006 defines the accepted isolation boundary;
independent review and release acceptance remain open. M6C remains blocked on
its later R4/B5 record.

## M6A approval record

Joshua Myers approved without revision on 2026-09-14:

1. R1's fixed 20% trimmed-location estimand, analytic t inference, raw effect,
   centrality behavior, minimum/effective sample, and no standardized effect;
2. R2's marginal 20% Winsorized Pearson estimand, WRS2-style effective-df test,
   explicit seeded 1,999-replicate percentile interval, valid-replicate rule,
   and Holm matrix family;
3. R3's independent Yuen and Welch–Yuen paths, trimmed subject-difference and
   WRS2-style repeated paths, raw contrasts, Holm pairwise families, and no
   standardized robust effect;
4. G6's explicit robust mode/options, identity-based PCG64DXSM streams, serial
   atomic grouping, 100-million default/500-million hard resample-work limits,
   inherited artist/data ceilings, and semantic rendering;
5. ADR-005's native bounded implementation and no-fallback architecture;
6. ADR-006's core/optional-Bayesian boundary, which adds no M6A dependency; and
7. the numerical, independent/oracle, calibration, compatibility, resource,
   and explicit-deferral policies exactly as written.

The approval authorizes M6A implementation and acceptance-fixture construction for
R1–R3/G6 only. It does not approve R4, any B1–B6 Bayesian method or dependency,
the later M6A release candidate, M6B/M6C, or final M6/`0.4` acceptance. Those
remain separate gates.
