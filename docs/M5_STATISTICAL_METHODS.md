# M5 Coefficient and Meta-analysis Method Specification

- Status: K1–K4 and MA1–MA4 approved
- Version: 0.1.0
- Date: 2026-09-14
- Statistical owner/reviewer: Joshua Myers
- Applies to: approved M5A coefficient plots and approved M5B frequentist
  random-effects meta-analysis

## Provenance and compatibility target

This specification was prepared against:

- `ggstatsplot@7a724cd0ab55668b9d0b2e84b12c711c5be68ac8`, the approved
  upstream revision in `docs/upstream/manifest.json`;
- pinned `R/ggcoefstats.R` with SHA-256
  `8d920502e98d25f482f727c54d0dbe1917ffa4db5fad7364677f1d142ffb90c0`;
- Statsmodels 0.15.0, NumPy 2.x, SciPy 1.18.1, Polars 1.44.1+, and Matplotlib
  3.10+, pinned or bounded in `uv.lock` and `pyproject.toml`.

The upstream function accepts many R model classes through broad external
tidying dispatch and also accepts tidy dataframes. M5A instead specifies one
strict Polars table protocol and one exact fitted-Statsmodels OLS adapter.
Upstream behavior is compatibility evidence, not proof of statistical identity
or permission to accept arbitrary Python objects.

## Common scope and reporting policy

- M5A plots reported coefficients; it does not fit, choose, diagnose, or approve
  a regression model.
- The estimand and scientific interpretation belong to the model or table that
  produced each estimate. The result records the declared estimate label,
  additive scale, units, direction, and null value without inventing a universal
  coefficient interpretation.
- Supported coefficient scales are untransformed additive scales with a finite
  null value, zero by default. Exponentiation and automatic odds-, risk-, or
  hazard-ratio interpretation are unsupported.
- The reported coefficient estimate is the effect measure. M5A computes no
  additional standardized effect size.
- All supported coefficient tests are two-sided. Full precision is retained;
  digits and formatting affect presentation only.
- M5A applies no multiplicity correction and makes no family-wise or false-
  discovery-rate claim. Every p-value is labeled as reported/model-derived and
  unadjusted.
- The caller dataframe and fitted result are never mutated. The analysis owns
  immutable copies of all retained values and identities.
- Null and non-finite participating values fail. M5A does not silently remove
  estimates, impute inference, refit a model, or switch covariance/test methods.
- `conf_level` and `alpha` must be finite and strictly between zero and one.
  Significance is defined as `p_value < alpha`; equality is not significant.
- No stochastic or resampling method is included in M5A.

## K1: Coefficient identity, estimand, and input profiles

The canonical input is a Polars dataframe with required columns:

- `term`: non-null, nonempty UTF-8 string;
- `estimate`: non-null, finite numeric value on the declared additive scale.

The caller may supply any subset of `response`, `component`, and `group` as
structured identity columns. Every supplied identity value must be a non-null,
nonempty UTF-8 string. Row identity is the ordered tuple of supplied identity
fields followed by `term`. It must be unique. M5A never concatenates columns to
make a duplicate disappear; the renderer builds any composite display label
from the retained structured fields.

An optional non-null Boolean `is_intercept` column identifies table intercepts.
When absent, every table row is treated as a non-intercept. Intercept status is
not guessed from term text.

Exactly one table-wide profile is resolved from the participating columns:

1. `estimate_only`: `term` and `estimate`; no uncertainty or test is claimed.
2. `interval`: both `conf_low` and `conf_high` are present for every row and use
   the operation's single `conf_level`; no test or significance is claimed.
3. `full_t`: interval fields plus `standard_error`, `statistic`, `df`, and
   `p_value`; `statistic_kind="t"` is explicit.
4. `full_z`: interval fields plus `standard_error`, `statistic`, and `p_value`;
   `statistic_kind="z"` is explicit and `df` is absent.

Participating inference columns cannot be partially populated, mixed across
rows, or silently ignored. Additional nonparticipating dataframe columns are
not selected, retained, or interpreted.

For every interval/full profile, `conf_low` and `conf_high` must be finite,
ordered, and contain `estimate`. For full profiles, `standard_error` is finite
and strictly positive, `statistic` is finite, `p_value` is finite and in
`[0, 1]`, and `df` for `full_t` is finite and strictly positive.

Reported table inference is authoritative after structural validation. M5A does
not reconstruct a p-value or interval and does not require
`statistic == (estimate-null)/standard_error`, because reported covariance,
constraints, transformations before input, and rounding cannot be inferred
safely. The result explicitly labels these values `reported` and records that
their scientific and model validity was not independently established.

`sort="none"` retains physical source order. `sort="ascending"` and
`sort="descending"` use estimate order with original row position as the stable
tie breaker. Source position and displayed position are both retained.

## K2: Coefficient inference and confidence semantics

For an interval/full table profile, the interval is a reported two-sided
confidence interval for the same coefficient estimand and additive scale at the
single declared `conf_level`. Mixing confidence levels within one operation is
unsupported. Bayesian credible intervals and one-sided intervals are outside
M5A.

For `full_t`, the reported hypothesis is
`H0: coefficient = null_value` against the two-sided alternative, with the
reported Student-t statistic, positive degrees of freedom, and p-value. For
`full_z`, the same hypothesis uses the reported standard-normal statistic and
p-value. The caller asserts that the supplied fields share this hypothesis and
scale; plotsalot validates shape, presence, finiteness, bounds, and interval
containment but does not reverse-engineer their originating estimator.

M5A supports no F, chi-squared, likelihood-ratio, score, Wald-block, omnibus,
one-sided, bootstrap, permutation, or Bayesian test profile. It does not derive
a full profile from an estimate and standard error alone.

`stats_labels=True` is valid only for a full profile. `stats_labels=False` may
be used with any profile. `only_significant=True` is valid only when statistical
labels are enabled and filters labels with `p_value < alpha`; it never removes a
coefficient row, point, interval, or serialized inference record.

The default label identifies the estimate, interval confidence level,
statistic kind/value, degrees of freedom for t, unadjusted two-sided p-value,
and inference source. The result stores values, not pre-rounded label text.

## K3: Fitted Statsmodels OLS adapter

The first fitted-model adapter accepts only an exact
`statsmodels.regression.linear_model.RegressionResultsWrapper` whose exact
underlying model class is `statsmodels.regression.linear_model.OLS`. WLS, GLS,
GLM, discrete, time-series, survival, mixed-effects, regularized, Bayesian,
third-party, raw unwrapped results, subclasses with changed semantics, and
duck-typed lookalikes are rejected.

The result must already be fitted. The adapter never refits it and accepts only
`cov_type="nonrobust"` or `cov_type="HC3"`. It respects the fitted result's
Boolean `use_t`:

- `use_t=True` produces a model-derived t profile using `df_resid`;
- `use_t=False` produces a model-derived z profile with no coefficient-level
  degrees of freedom.

The adapter snapshots, without modifying them:

- unique nonempty string names from `model.exog_names`;
- one-dimensional `params`, `bse`, `tvalues`, and `pvalues` with equal length;
- a two-column interval from `conf_int(alpha=1-conf_level)` using the fitted
  covariance and reference distribution;
- `nobs`, `df_model`, `df_resid`, covariance type, `use_t`, exact model/result
  class identities, Statsmodels version, and finite AIC/BIC when available.

All participating arrays and summary values must be finite. Standard errors
must be strictly positive; p-values must lie in `[0, 1]`; intervals must be
ordered and contain their estimates; `nobs` must be an exactly representable
positive integer; and `df_resid` must be positive. The design must have full
reported column rank: `model.rank` equals the number of parameters. An aliased,
rank-deficient, empty, zero-residual-df, non-finite, or shape-inconsistent result
fails before an analysis object is returned.

Intercept identity comes only from the fitted OLS design metadata:
`model.k_constant` and `model.data.const_idx` must agree. With no constant, no
term is an intercept. With one constant, `const_idx` must identify exactly one
valid parameter position. Ambiguous constant metadata fails; the adapter does
not guess from the name `const` or `Intercept`.

The model-derived coefficient hypothesis is
`H0: beta_j = 0` against a two-sided alternative on the fitted OLS coefficient
scale. Consequently, the OLS adapter uses `null_value=0`; callers cannot
override it. Nonrobust inference inherits the fitted homoskedastic OLS covariance
assumptions. HC3 inference inherits Statsmodels' fitted heteroskedasticity-
consistent covariance and its recorded t/normal reference. The plot reports
that inference and does not certify causal identification, linear specification,
independence, exogeneity, or model adequacy.

AIC and BIC are retained only as finite reported model-summary values. They are
not recomputed and the caption describes them without claiming that they are
universally comparable or evidence of model validity.

## K4: Selection, ordering, labels, and renderer semantics

`exclude_intercept=False` retains all rows. When true, rows explicitly marked as
intercepts by K1 or K3 are excluded from the displayed coefficient set and
identified in the audit. If no explicit intercept exists, the operation is
unchanged. Excluding every row is an error.

The analysis result retains input row count, retained row count, excluded
intercept identities, source/display position, profile, scale declaration,
confidence level, alpha, label policy, and the complete coefficient/inference
records. Sorting and exclusion occur once during analysis; rendering does not
reselect rows.

The semantic Matplotlib renderer uses one horizontal point per retained
coefficient in result order, shown top to bottom. Complete intervals become
horizontal whiskers. The vertical reference line is exactly the typed
`null_value`. Estimate-only input creates no whiskers or statistical labels;
interval input creates whiskers but no statistical labels.

Model-derived and reported inference use the same geometry/result schema but
retain different provenance. Display labels must never make reported table
values appear recomputed or model-validated.

`stats_labels=False`, `only_significant`, interval visibility, title, subtitle,
caption, colors, and axis labels are presentation choices. They never alter the
typed coefficient family. Default model caption content may include retained
AIC/BIC; table inputs receive no fabricated model caption.

M5A does not define a multiplicity family across coefficients. Significance
labels use each unadjusted reported/model-derived p-value and must say so. A
future adjusted family requires a separate approved record with complete
hypothesis membership and correction scope.

Term labels and statistical labels remain associated with their structured row
under sorting, filtering, row permutation, repeated base term names, and
injection tests. Collision handling and figure growth are deterministic and
bounded; no point or requested eligible label is silently sampled or dropped.

The public M5A defaults are:

- maximum input/retained coefficient rows: 500;
- maximum rendered coefficient points: 500;
- maximum rendered statistical labels: 200;
- maximum structured identity columns: 8, of which M5A names three;
- maximum serialized model-summary fields: 32.

Every applied ceiling is serialized. Explicit positive overrides remain bounded
by package-wide numeric and rendering safety checks. Oversized requests fail
before a partial result or figure is returned.

## MA1: Study estimand, scale, and input contract

M5B is an aggregate-data meta-analysis of independent estimates. It is selected
only by an explicit `meta_analytic_effect=True` request over a Polars dataframe.
It never pools ordinary coefficients automatically.

The required columns are:

- `term`: a unique, non-null, nonempty UTF-8 study identity;
- `estimate`: a non-null finite estimate;
- `standard_error`: a non-null finite strictly positive sampling standard
  error for that estimate.

Meta mode rejects coefficient confidence bounds, test statistics, p-values,
intercept markers, and structured coefficient identity fields rather than
silently choosing between reported and computed inference. Additional
nonparticipating dataframe columns are not selected or retained.

The caller must explicitly declare nonempty `estimand`, `effect_scale`,
`effect_direction`, and `effect_units` strings, a finite `null_value`, and
`dependence="independent"`. These declarations state that all retained rows
estimate comparable quantities on one additive analysis scale, with sampling
errors independent across studies. Plotsalot records but cannot scientifically
verify those assertions.

Values are analyzed exactly on the supplied scale. A caller may supply an
already transformed additive measure, such as a log ratio, but M5B does not
perform or reverse a transformation, change the null, or relabel the result on
an exponentiated scale.

The sampling model is:

`estimate_i | theta_i ~ Normal(theta_i, standard_error_i^2)` and
`theta_i ~ Normal(mu, tau^2)`.

The population estimand is `mu`, the mean of the declared normal distribution
of comparable true effects. It is not a common effect shared by every study.
The primary hypothesis is `H0: mu = null_value` against a two-sided alternative.

At least three and at most 500 studies are required by default. Nulls,
non-finite values, duplicate studies, zero/negative standard errors, or fewer
than three studies fail without deletion or imputation. Source row order and
exact study count are retained; row permutations cannot change a named study's
estimate, standard error, or weight.

For rendering and transparent per-study context, M5B computes a two-sided
normal-approximation interval and z test for each study:

- `z_i = (estimate_i - null_value) / standard_error_i`;
- `p_i = 2 * NormalSF(abs(z_i))`;
- interval `estimate_i +/- z_(1-alpha/2) * standard_error_i`.

These unadjusted study tests are descriptive, do not determine inclusion or the
pooled method, and make no multiplicity claim. Their inference source is named
`study_normal_approximation_from_reported_standard_error`.

## MA2: REML between-study variance and random-effects weights

M5B uses a single intercept-only random-effects model. Between-study variance
`tau^2 >= 0` is estimated by restricted maximum likelihood (REML); no
DerSimonian–Laird, Paule–Mandel, empirical-Bayes, fixed-effect, or data-dependent
estimator switch is available.

For candidate `tau^2`, define:

- `v_i = standard_error_i^2`;
- `w_i(tau^2) = 1 / (v_i + tau^2)`;
- `mu(tau^2) = sum(w_i * estimate_i) / sum(w_i)`;
- restricted score, omitting a positive constant,
  `S(tau^2) = sum(w_i^2 * (estimate_i-mu)^2) - sum(w_i)
  + sum(w_i^2)/sum(w_i)`.

If `S(0)` is nonpositive within the declared score tolerance, the REML estimate
is the boundary `tau^2=0`. Otherwise, a nonnegative score root is bracketed by
deterministic upper-bound expansion and solved with Brent's method. The initial
upper bound is the maximum of one, the sample variance of scaled estimates, and
the maximum scaled sampling variance; it is doubled at most 60 times until the
score is negative. Root solving permits at most 100 iterations. The solved root
must improve the restricted log-likelihood over the zero boundary and satisfy
the declared score tolerance or the operation fails.

Before solving, estimates centered at `null_value` and standard errors are
divided by the positive factor
`max(max(abs(estimate-null_value)), max(standard_error))`. This scale-equivariant
rescaling improves conditioning; `tau^2`, `tau`, pooled estimates, and intervals
are transformed back exactly to the caller's scale. The factor and convergence
record are retained.

Score boundary tolerance is
`1e-12 * max(1, sum(w_i(0)))` on the scaled problem. Brent solving uses absolute
tolerance `1e-12`, relative tolerance `8 * machine_epsilon`, and the iteration
limit above. A failed bracket, nonconvergence, non-finite intermediate, negative
variance outside roundoff tolerance, or nonpositive total weight raises an
identified numerical error. There is no fallback estimator.

Final random-effects weights are `1/(v_i+tau^2)` and normalized to sum to one.
The pooled estimate is their weighted mean. The result retains raw and
normalized weights, sampling variances, weighted contributions, `tau^2`,
`tau=sqrt(tau^2)`, score/residual, boundary status, bracket, iterations,
tolerances, method identity `reml_intercept_only`, and convergence state.

## MA3: Modified Hartung–Knapp pooled inference and prediction

Let `W=sum(w_i)`, `mu_hat=sum(w_i*estimate_i)/W`, `df=k-1`, and

`q_hk = sum(w_i * (estimate_i-mu_hat)^2) / df`.

M5B uses the conservative ad-hoc modification
`q_star=max(1, q_hk)`. The pooled variance is `q_star/W`, its standard error is
the square root, and the method is named
`modified_hartung_knapp_random_effects_mean`. This prevents the adjustment from
producing a smaller standard error than conventional random-effects inference.

The pooled test and confidence interval use the Student-t distribution with
`df=k-1`:

- `t = (mu_hat-null_value) / pooled_standard_error`;
- `p = 2 * StudentTSF(abs(t), df)`;
- interval `mu_hat +/- t_(1-alpha/2, df) * pooled_standard_error`.

The result retains `q_hk`, `q_star`, conventional variance `1/W`, adjusted
variance/standard error, statistic, degrees of freedom, p-value, confidence
level, interval target `mean_of_true_effect_distribution`, and two-sidedness.
Neither significance nor the heterogeneity test selects a different model.

A prediction interval targets the true effect in a new study drawn from the
same declared normal distribution of effects. For `k>=5`, it is

`mu_hat +/- t_(1-alpha/2, k-1) * sqrt(tau^2 + pooled_standard_error^2)`.

It is labeled an approximate
`modified_hartung_knapp_normal_random_effects_prediction_interval`. For three or
four studies it is absent with reason `fewer_than_five_studies`; the pooled
confidence interval remains available with a small-study warning. The threshold
is fixed before analysis and is not changed by the estimated heterogeneity.

When `tau^2=0` and a prediction interval is available, its endpoints equal the
pooled confidence interval by construction. A confidence interval is never
substituted or relabeled as a prediction interval.

## MA4: Heterogeneity, boundaries, and interpretation

Cochran's Q uses fixed inverse-sampling-variance weights solely as a
heterogeneity diagnostic:

- `a_i=1/v_i`;
- `mu_fixed=sum(a_i*estimate_i)/sum(a_i)`;
- `Q=sum(a_i*(estimate_i-mu_fixed)^2)`;
- `df_Q=k-1`;
- `p_Q=ChiSquareSF(Q, df_Q)`.

M5B does not expose fixed-effect pooled inference and does not select the
random-effects model based on Q. `mu_fixed` is retained as the Q reference mean,
not labeled as a second pooled estimand.

I-squared is `max(0, (Q-df_Q)/Q)` when `Q>0`, otherwise zero, and is bounded in
`[0,1]`. The result reports the proportion and its percentage presentation;
cutoffs such as low/moderate/high are not assigned. `tau^2` and `tau` remain on
the squared and original declared effect scales. No confidence interval for
`tau^2` is included in the first M5B slice, and this absence is explicit.

The result retains Q, its df and p-value, Q reference mean, I-squared, tau,
tau-squared, convergence and boundary metadata, and warnings for `k<5`,
`tau^2=0`, or a prediction interval crossing the null where applicable. These
are descriptive diagnostics and never trigger study deletion, reweighting,
fallback, scale transformation, or method switching.

The random-effects mean is interpreted only for the declared distribution of
studies and may be misleading under selection bias, incomparable estimands,
dependence, or asymmetric biases. M5B does not diagnose publication bias,
causal validity, normality of true effects, or correctness of reported sampling
standard errors.

## Shared structured result

The schema-v1 coefficient result must include:

- analysis identity, source kind (`table` or exact Statsmodels OLS adapter),
  inference profile/source, estimate label, additive scale, units/direction,
  null value, confidence level when applicable, alpha, and two-sidedness;
- complete source/retained/excluded audit and stable source/display positions;
- structured term identity, intercept status, estimate, optional standard
  error/interval/statistic/df/p-value, and unadjusted significance for every
  retained row;
- exact model/result class, Statsmodels version, covariance type, `use_t`, nobs,
  model/residual df, rank, finite AIC/BIC, and adapter warnings when applicable;
- sorting, interval and label visibility, significance-label policy, resource
  ceilings, compatibility adaptations, and absence reasons for unsupported
  optional records;
- an explicit absent meta-analysis field during M5A, reserved for the approved
  MA1–MA4 M5B extension.

When M5B is active, the meta-analysis field must retain MA1 declarations, every
study's computed normal inference and random-effects weight/contribution, the
complete MA2 REML convergence record, MA3 pooled and prediction records, and MA4
heterogeneity records. It cannot coexist with fitted-model provenance,
coefficient intercept exclusions, or caller-reported coefficient inference.

`CoefficientAnalysis` owns the immutable table and result. The analysis module
does not import Matplotlib. `render_ggcoefstats` accepts the retained analysis,
and `ggcoefstats` is the explicit convenience operation. Rendering never calls
Statsmodels or recomputes inference.

Every public number is finite or an explicitly schema-permitted absence. Public
serialization contains no Polars, NumPy, SciPy, Statsmodels, Matplotlib, R,
callable, model object, or caller dataframe.

## Numerical and independent verification policy

- Table estimates and reported inference pass through at full binary-float
  precision and require exact association with their typed row identities.
- Analytic full-rank OLS fixtures independently compute
  `(X'X)^(-1)X'y`, residual variance, nonrobust covariance, standard errors,
  t statistics, residual degrees of freedom, two-sided Student-t probabilities,
  intervals, AIC, and BIC.
- HC3 fixtures independently compute leverage and the sandwich covariance
  `bread * X' diag(e_i^2/(1-h_ii)^2) X * bread`, then the approved t or normal
  reference from `use_t`.
- Well-conditioned OLS estimates, covariance entries, standard errors,
  statistics, probabilities, intervals, AIC, and BIC use `rtol=1e-11` and
  `atol=1e-12`. Rank, identity, counts, profile, covariance/test names, and
  positions require exact equality.
- Pinned-R fixtures retain raw `ggcoefstats` objects for a tidy estimate-only
  table, full-inference table, and an ordinary linear model. Normalized oracle
  comparison is limited to shared coefficient/interval/test/ordering behavior;
  broad R tidying, arbitrary model support, and visual pixel parity are not
  claimed.
- Renderer injection tests replace analysis values with unmistakable finite
  values and prove point, whisker, reference, label, title/subtitle/caption, and
  extraction fields originate only in the typed result.
- All fixtures are synthetic and redistributable. R, Docker, and network access
  remain development-only.

For M5B additionally:

- Equal-variance analytic fixtures reduce the pooled estimate to the arithmetic
  mean; exact-null and identical-estimate cases exercise the `tau^2=0` boundary.
- Independent formulas reproduce study z inference, Q, I-squared, the REML
  score/root, random weights/contributions, modified Hartung–Knapp scale,
  pooled t inference, and prediction intervals.
- Well-conditioned pooled estimates, weights, tests, intervals, Q, I-squared,
  tau, and tau-squared use `rtol=1e-10`, `atol=1e-12`. Root score residuals use
  the tighter of the declared absolute score tolerance and a fixture-specific
  scale-aware tolerance recorded before evaluation.
- Pinned-R raw `ggcoefstats(meta.analytic.effect=TRUE,
  meta.type="parametric")` objects verify upstream behavior. Independent
  `metafor::rma(method="REML", test="adhoc")` and base-R formulas verify the
  approved estimator/inference separately.
- Upstream's default REML estimate, random-effects weights, pooled estimate, Q,
  and heterogeneity fields must agree where definitions coincide. Its default
  normal pooled inference is deliberately adapted to modified Hartung–Knapp;
  the oracle asserts rather than conceals that difference.

## Explicitly deferred behavior

- MA1–MA4 meta-analysis implementation until this M5B proposal is approved;
- robust and Bayesian coefficients/meta-analysis, credible intervals, and Bayes
  factors assigned to M6;
- WLS, GLS, GLM, discrete, survival, mixed-effects, time-series, regularized,
  multivariate, Bayesian, and third-party fitted-model adapters;
- automatic model tidying, duck-typed models, formula evaluation, refitting,
  covariance replacement, standardization, marginal effects, contrasts, and
  arbitrary inference derivation;
- exponentiated coefficients, odds/risk/hazard ratios, response/link-scale
  transformations, one-sided intervals/tests, and nonzero-null OLS inference;
- ANOVA/effect-size rows, F or chi-squared coefficient labels, omnibus tests,
  block tests, likelihood-ratio tests, and multiplicity adjustment;
- null-estimate removal, auto-generated terms, heuristic duplicate-term
  concatenation, inferred intercept names, and mixed inference profiles;
- grouped coefficient plots, arbitrary ggplot/Matplotlib layer injection,
  dynamic palette lookup, R themes, ellipsis forwarding, and pixel identity.

All deferred selector values fail explicitly or are absent from the public
signature. They are never accepted and ignored.

## M5A approval record

Joshua Myers is asked to approve or revise:

1. K1's strict Polars identity, intercept, estimate-only, interval, full-t, and
   full-z profiles;
2. K2's two-sided reported-inference semantics, structural validation,
   unadjusted p-values, and presentation-only significance filtering;
3. K3's exact fitted Statsmodels OLS adapter, nonrobust/HC3 covariance
   provenance, `use_t` reference rule, rank/intercept checks, and no-refit
   boundary;
4. K4's source/stable-estimate ordering, explicit intercept exclusion,
   dot/whisker/reference/label behavior, model summaries, and resource limits;
5. the numerical tolerances, independent/oracle evidence plan, compatibility
   adaptations, and explicit M5A deferrals.

Approval authorizes implementation and acceptance fixtures for M5A exactly as
written. It does not approve MA1–MA4, M5B implementation, the later M5A release
candidate, or final M5/`0.3` acceptance; those remain separate gates.

Joshua Myers approved K1–K4, the numerical and evidence policy, resource
limits, compatibility adaptations, and explicit M5A deferrals without revision
on 2026-09-14.

## M5B approval request

Joshua Myers is asked to approve or revise:

1. MA1's independent aggregate-estimate population, strict study input,
   mandatory estimand/scale/direction/units/dependence declarations, normal
   sampling model, three-study minimum, and computed descriptive study z
   inference;
2. MA2's intercept-only REML tau-squared score/root, scale normalization,
   deterministic convergence limits, boundary behavior, weights, and no-
   fallback rule;
3. MA3's modified Hartung–Knapp t test and mean-effect confidence interval,
   approximate prediction interval for at least five studies, and explicit
   distinction between interval targets;
4. MA4's Cochran-Q/I-squared/tau reporting, lack of fixed-effect pooled
   inference or tau-squared interval, non-switching diagnostics, and
   interpretation warnings;
5. the numerical tolerances, independent/metafor/oracle evidence plan,
   500-study resource ceiling, compatibility adaptations, and M5B deferrals.

Approval authorizes M5B implementation and acceptance fixtures exactly as
written. It does not approve the later M5A/M5B release candidates or final
M5/`0.3` acceptance; those remain separate gates.

Joshua Myers approved MA1–MA4, the numerical and evidence policy, resource
limits, compatibility adaptations, and explicit M5B deferrals without revision
on 2026-09-14.
