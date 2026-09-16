# M6C Coefficient and Meta-analysis Method Proposal

- Status: accepted M6 implementation; M7B reclassified R4-M as experimental for 1.0
- Version: 0.1.0
- Date: 2026-09-15
- Product/statistical owner: Joshua Myers
- Implementation owner: Codex
- Applies to: R4/B5 coefficient-summary and aggregate meta-analysis work only

## Approval boundary

This companion to `M6_STATISTICAL_METHODS.md` and
`M6B_STATISTICAL_METHODS.md` proposes the final R4 and B5 decisions required to
enter M6C. Joshua Myers approved every decision and entry control in this
proposal without revision on 2026-09-15, authorizing M6C implementation and
acceptance-fixture construction exactly as specified. The approval does not
accept an implementation, close M6C, close M6, or approve the `0.4` candidate.
Those remain distinct gates in `MILESTONE_6.md`.

After all three implementation passes and production gates completed, Joshua
Myers independently reviewed and accepted the M6C candidate on 2026-09-15. The
combined M6/`0.4` decision remains separate.

The proposal deliberately keeps `ggcoefstats` a reporting and aggregate-data
surface. It adds no regression fitting, arbitrary fitted-result dispatch,
posterior-draw ingestion, formula language, participant-level meta-analysis,
or automatic method selection. Robust and Bayesian modes are selected only by
the caller. A diagnostic, outlier, prior, convergence issue, or failed
classical assumption never changes the requested mode.

The four approval decisions are:

- R4-C: strict caller-reported robust coefficient intervals;
- B5-C: strict caller-reported posterior coefficient summaries;
- R4-M: one fixed-Student-t aggregate robust random-effects sensitivity model;
  and
- B5-M: one proper-prior Bayesian normal-normal aggregate random-effects model.

M6C uses the accepted native NumPy/SciPy boundaries in ADR-005 and ADR-006. The
approved design adds no MCMC engine, Bayesian extra, new runtime dependency,
hidden retry, or fallback.

## Common public and data boundary

M6C adds an explicit keyword-only
`type: Literal["parametric", "robust", "bayes"] = "parametric"` to
`analyze_ggcoefstats` and `ggcoefstats`.

- `type="parametric"` preserves every accepted M5 table, exact fitted-OLS, and
  REML/modified-Hartung-Knapp behavior without numerical change.
- `type="robust"` selects R4-C when `meta_analytic_effect=False` and R4-M when
  `meta_analytic_effect=True`.
- `type="bayes"` selects B5-C when `meta_analytic_effect=False` and B5-M when
  `meta_analytic_effect=True`.

All new inputs are Polars dataframes. M6C adds no fitted robust or Bayesian
adapter. The inherited unique structured coefficient identity, explicit
intercept marker, stable sorting, immutable owned data, 500-row default ceiling,
500 rendered-point ceiling, 200-label ceiling, extraction, composition, and
analysis-free renderer contracts remain binding.

An M6C operation accepts exactly one table-wide profile. Participating fields
must be present and non-null for every retained row. Unknown extra dataframe
columns remain nonparticipating as in M5, but columns reserved by another
coefficient/meta profile are rejected so a confidence interval, credible
interval, test, or standard error cannot be silently ignored.

All scales are additive. Automatic exponentiation, back-transformation,
standardization, and odds/risk/hazard interpretation remain unsupported. The
caller declares nonempty `estimand`, `effect_scale`, `effect_direction`, and
`effect_units` strings and a finite `null_value` for either meta-analysis.
Plotsalot records these assertions and validates structural consistency; it
cannot establish scientific comparability, identification, or model adequacy.

## R4-C: caller-reported robust coefficient intervals

### Supported profile

The only new robust coefficient profile is `robust_interval`. It requires:

- `term`: the inherited unique structured row identity;
- `estimate`: a finite reported robust point estimate;
- `conf_low` and `conf_high`: finite ordered bounds containing `estimate`;
- one operation-wide `conf_level` from `0.80` through `0.99`;
- nonempty operation-wide `robust_method`, `robust_tuning`, and
  `interval_method` provenance strings, each at most 200 Unicode scalar values
  with no control characters; and
- the inherited additive scale, units, direction, and finite null declaration.

The three method strings are opaque caller assertions. They are preserved
verbatim after whitespace normalization and labeled
`caller_reported_unverified`; plotsalot does not infer a method from a tuning
name or claim that an interval is robust merely because the caller says so.
Examples such as `Huber M-estimator`, `c=1.345`, and `sandwich Wald` belong in
documentation, not in an allowlist that would imply scientific validation.

`standard_error`, `statistic`, `df`, `p_value`, posterior probability, Bayes
factor, and credible-interval columns are forbidden in this profile. M6C does
not reconstruct tests from reported intervals and does not provide robust
coefficient significance filtering. `only_significant=True` fails.
`stats_labels=True` may identify the estimate, confidence level, method,
tuning, interval method, and unverified source; it never adds a p-value or a
qualitative claim.

An M5 HC3 OLS result remains an accepted M5 model-derived covariance profile.
It does not become an R4-C robust point-estimation adapter and is not relabeled.
Robust regression fitting, covariance selection, coefficient dependence,
simultaneous intervals, multiplicity, and model diagnostics are outside M6C.

## B5-C: caller-reported posterior coefficient summaries

### Supported profile

The only new Bayesian coefficient profile is `posterior_summary`. It requires:

- `term` plus the inherited optional structured identity and intercept fields;
- `posterior_median`, `credible_low`, and `credible_high`, all finite, with
  ordered bounds containing the median;
- `probability_above_null`, `probability_below_null`, and
  `probability_at_null`, each finite in `[0, 1]` and summing to one within
  `1e-12` absolute tolerance;
- one operation-wide equal-tail `credible_level` from `0.80` through `0.99`;
- a finite operation-wide `null_value`; and
- nonempty operation-wide `posterior_model`, `likelihood`,
  `prior_description`, and `computation_method` strings subject to the same
  length/control-character rules as R4-C.

The point mass field is required rather than assumed to be zero; this prevents
a continuous posterior and a spike-and-slab posterior from sharing false
directional semantics. The four provenance strings are caller-reported and
unverified. Plotsalot validates only the summary's shape, bounds, probability
partition, common interval definition, identity, and scale.

No model object, posterior object, draw array, chain, arbitrary callable, or
artifact reference is accepted. `estimate`, confidence bounds, standard error,
test statistic, degrees of freedom, p-value, and Bayes-factor columns are
forbidden in this profile. M6C cannot recover a marginal likelihood or model
comparison from posterior quantiles, so B5-C reports no BF and makes no evidence
claim. This is estimation-only input, not an exception that permits incomplete
B1 evidence to masquerade as a plotsalot-fitted Bayesian analysis.

The renderer uses `posterior_median` for the point and the credible bounds for
the whisker. `stats_labels=True` may show the numeric directional probabilities,
credible level, and `caller_reported_unverified` source. It emits no
`significant`, evidence-strength, or ROPE language. `only_significant=True`
fails. Intervals are pointwise; no simultaneous or multiplicity claim is made.

## R4-M: fixed-Student-t robust aggregate meta-analysis

**1.0 status:** experimental. M7 retained the implementation and its strict
failure behavior but excluded this method, its seven dedicated `RobustMeta*`
types, and its schema-v2 serialized variant from the stable 1.x promise after a
locked mapping fit failed with `robust_meta_ambiguous_optimum`. This status does
not weaken any estimator, convergence, work, or no-fallback rule below.

### Role and study population

R4-M is an explicitly requested sensitivity analysis for independent aggregate
study estimates. It reuses the accepted M5 `term`, `estimate`, and strictly
positive `standard_error` table and all MA1 declarations. It does not replace
the M5 classical result automatically, detect whether a robust analysis is
needed, remove a study, or certify that an unusual study is erroneous.

The method requires 10 through 500 studies. Ten is a product floor for the
two-parameter likelihood and repeated asymptotic profile-likelihood inference,
not a claim that every 10-study analysis is reliable. Results with 10 through 19
studies retain `few_studies_robust_profile_likelihood` as a visible warning.
Fewer than 10 studies fail with `robust_meta_requires_at_least_10_studies` and
do not fall back to M5.

### Model and estimand

Fix `nu=4`; it is not estimated or caller-adjustable in M6C. For study `i`,

```text
lambda_i ~ Gamma(shape=nu/2, rate=nu/2)
theta_i | lambda_i ~ Normal(mu, tau_squared/lambda_i)
y_i | theta_i, lambda_i ~ Normal(theta_i,
                                 standard_error_i_squared/lambda_i)
```

so the observed aggregate estimate has marginal model

```text
y_i ~ StudentT(df=4,
               location=mu,
               scale=sqrt(standard_error_i_squared + tau_squared)).
```

The common latent precision scales both within- and between-study components.
This is the tMeta accommodation mechanism, adapted by plotsalot to fixed four
degrees of freedom. Fixing `nu` avoids estimating a robustness parameter from a
small study collection, makes the analysis identity reproducible, and prevents
the method from drifting silently toward the Gaussian model. The Student-t
`scale` is not its standard deviation.

The estimand is `mu`, the location and median of the declared Student-t
distribution of comparable aggregate estimates (and its mean because
`nu > 1`). `tau_squared >= 0` is the between-study scale component in the
hierarchy. Neither quantity is the M5 normal-normal REML estimand under a new
name, and robust and classical estimates need not agree.

### Maximum likelihood and convergence

M6C maximizes the complete marginal Student-t log likelihood after the exact
internal transformation

```text
center = null_value
scale = max(median(standard_error),
            1.4826*median(abs(y-median(y))),
            max(abs(y-null_value))*sqrt(machine_epsilon),
            sqrt(smallest_positive_normal))
y_scaled = (y-center)/scale
standard_error_scaled = standard_error/scale.
```

The final result is mapped back exactly. Three deterministic starts are
required:

1. the accepted M5 REML pooled estimate and `tau_squared`;
2. the sample median and
   `max(0, (1.4826*MAD)^2-median(standard_error_squared))`;
3. the inverse-variance mean at `tau_squared=0`.

For fixed `nu=4`, an ECME/fixed-point cycle computes

```text
d_i_squared = (y_i-mu)^2 / (standard_error_i_squared+tau_squared)
lambda_hat_i = (nu+1) / (nu+d_i_squared)
```

then applies, using the previous cycle's
`D_i=standard_error_i_squared+tau_squared`,

```text
mu_next = sum(lambda_hat_i*y_i/D_i) / sum(lambda_hat_i/D_i)
tau_squared_next = max(
    0,
    sum((lambda_hat_i*(y_i-mu_next)^2-standard_error_i_squared)/D_i^2)
    / sum(1/D_i^2),
)
```

as the ECME/fixed-point updates. The implementation must derive and
independently test these score equations; it must not copy the GPL reference
source reviewed in the method-entry audit.

Each start has at most 10,000 cycles. A start converges only after three
successive cycles satisfy both relative log-likelihood change `<=1e-10` and
maximum scale-adjusted parameter change `<=1e-8`, the marginal log likelihood
has not decreased beyond `64*machine_epsilon*(1+abs(log_likelihood))`, and the
final interior score norm is `<=1e-8`. A boundary `tau_squared=0` instead must
satisfy the matching one-sided KKT condition within `1e-8`.

The converged solution with the greatest full-precision likelihood is retained.
Solutions whose likelihoods agree within `1e-8*(1+abs(best_log_likelihood))`
must also agree in scaled `mu` and `tau_squared` within `1e-7`; otherwise the
analysis fails with `robust_meta_ambiguous_optimum`. No converged start,
non-finite arithmetic, a failed score/KKT check, or work exhaustion fails
atomically. There is no REML, normal, alternate-tuning, interval, or optimizer
fallback.

### Pooled inference and influence

The primary two-sided hypothesis is `H0: mu=null_value`. The pooled confidence
set is the connected component containing the MLE obtained by inverting the
profile likelihood-ratio statistic against `chi_squared(df=1)` at the requested
`conf_level`. Every constrained profile evaluation uses the same three-start,
convergence, score/KKT, ambiguity, and work rules with `mu` fixed. Its two
finite endpoints are found by bracketed root solving.
The two-sided p-value is the chi-squared-1 upper-tail probability for the
profile likelihood ratio at `null_value`. These are explicit asymptotic
profile-likelihood results, not Hartung-Knapp, Wald, bootstrap, or Bayesian
intervals. A disconnected set, missing finite endpoint, or profile optimizer
failure is a typed failure.

For every study, retain the full-precision standardized residual,
`lambda_hat_i`, effective precision
`lambda_hat_i/(standard_error_i_squared+tau_squared)`, and its normalized share.
Normalized shares sum to one within `1e-12`. A small `lambda_hat_i` describes
downweighting under the fitted working model; M6C emits no automatic outlier
flag, deletion suggestion, cutoff, or p-value. Source order and study identity
remain attached under row permutation.

R4-M retains `tau` and `tau_squared`. It does not emit Cochran Q, I-squared, or
their p-values because those are tied to the Gaussian inverse-variance contract.
Their typed absence reason is `not_defined_for_student_t4_working_model`.
Likewise, no robust prediction interval is reported in M6C: a plug-in
Student-t interval would omit parameter uncertainty, while an approved
small-sample predictive construction is not available. The absence reason is
`robust_meta_prediction_method_not_approved`. A confidence interval must never
be drawn or labeled as prediction.

## B5-M: Bayesian normal-normal aggregate meta-analysis

### Likelihood, population, and priors

B5-M reuses the independent M5 aggregate study table and declarations and
requires 3 through 500 studies. Its likelihood is

```text
y_i | theta_i ~ Normal(theta_i, standard_error_i_squared)
theta_i | mu, tau ~ Normal(mu, tau_squared)
```

and therefore `y_i | mu,tau ~ Normal(mu,
standard_error_i_squared+tau_squared)`. The targets are the population mean
effect `mu`, nonnegative heterogeneity `tau`/`tau_squared`, and the true effect
`theta_new` in a new exchangeable study. Prediction is about `theta_new`, not a
future noisy reported estimate with an unspecified standard error.

The caller must supply two finite positive scales in the declared effect units,
chosen before examining the result:

```text
H1: mu ~ Normal(null_value, prior_mean_scale_squared)
H0: mu = null_value
both: tau ~ HalfNormal(prior_tau_scale)
```

The priors are independent and proper. There is no data-derived scale or
universal default. Documentation must show the implied 95% prior interval for
`mu` and the median/95% quantile and prior-predictive effect dispersion implied
by `prior_tau_scale`. Changing either scale changes the analysis identity.

The primary analysis is accompanied by four one-at-a-time sensitivity fits:
`0.5*prior_mean_scale`, `2*prior_mean_scale`, `0.5*prior_tau_scale`, and
`2*prior_tau_scale`, holding the other primary scale fixed. Sensitivities retain
the same targets, BF orientation, numerical checks, and complete prior record.
They never silently replace the primary analysis.

### Exact conditional calculations and bounded quadrature

At fixed `tau`, write `D_i=standard_error_i_squared+tau_squared`. Under H1,
the conditional posterior of `mu` is normal with

```text
v_mu(tau) = 1 / (1/prior_mean_scale_squared + sum(1/D_i))
m_mu(tau) = v_mu(tau) *
            (null_value/prior_mean_scale_squared + sum(y_i/D_i)).
```

The implementation analytically integrates `mu` to obtain the H1 marginal
likelihood conditional on `tau`; H0 evaluates the same likelihood at the fixed
null. Each is integrated against the identical normalized half-normal prior for
`tau`. The canonical evidence is finite natural-log

```text
log_bf10 = log p(y | H1) - log p(y | H0).
```

Prior model odds are not inferred. Renderers use the accepted B1 bounded
numeric BF10 display and no qualitative adjective.

Adaptive Gauss-Kronrod quadrature operates on `x in [0,1)` using
`tau=prior_tau_scale*x/(1-x)` and the exact Jacobian. Calculations use scaled
log densities and explicit endpoint limits. The primary and each sensitivity
fit use `epsabs=1e-12`, `epsrel=1e-10`, and at most 200 subdivisions. The result
retains transformation, tolerances, evaluations, error estimates, normalization
checks, root brackets, software identity, and convergence status.

The posterior CDFs of `mu` and `tau` are inverted with bracketed roots to obtain
posterior medians and equal-tail intervals. Conditional on `tau` and the data,

```text
theta_new ~ Normal(m_mu(tau), tau_squared+v_mu(tau)),
```

so its posterior median, equal-tail prediction interval, and directional
probabilities are obtained by integrating this conditional CDF over the
posterior of `tau`. No posterior draws or RQMC points are needed.

Every normalization, marginal likelihood, tail probability, and displayed
quantile must have estimated absolute error no greater than
`max(epsabs, epsrel*abs(integral))`. Quadrature warning, subdivision exhaustion,
lost tail mass, non-finite term, invalid bracket, non-monotone CDF, non-finite
BF, or failed tolerance is atomic. Work is not increased, tolerances are not
loosened, and no alternate prior, sampler, classical result, or partial plot is
returned.

### Posterior reporting and small-study behavior

The point summary for `mu`, `tau`, `tau_squared`, and `theta_new` is the
posterior median. Intervals are two-sided equal-tail credible intervals for
parameters and an equal-tail posterior prediction interval for `theta_new`, at
one finite level from `0.80` through `0.99`. Results retain
`P(mu>null_value)`, `P(mu<null_value)`, `P(theta_new>null_value)`, and
`P(theta_new<null_value)`; continuous-model point mass is exactly zero.

Every 3- or 4-study result visibly retains `few_studies_prior_sensitive`; the
primary and all four sensitivity records are mandatory. A wide, boundary-heavy,
or prior-sensitive heterogeneity posterior is reported rather than converted to
Q/I-squared or used to select another model. B5-M emits no heterogeneity
p-value, automatic model-selection rule, publication-bias correction, or
small-study-effect test.

Study-specific shrinkage estimates are deferred. The forest layer continues to
show each supplied study estimate and its M5 normal sampling interval; the
Bayesian pooled and prediction layers are visually distinct and consume only
the retained posterior summaries. The supplied study intervals are not
posterior intervals and must remain labeled as such.

## Numerical work, resources, and failure policy

R4-M is deterministic and B5-M is analytic/quadrature-based. Neither accepts a
seed. One robust marginal-likelihood/score evaluation and one Bayesian
integrand evaluation count as one M6C work unit. Root-solving endpoint
evaluations count in full. Complete primary, sensitivity, quantile, prediction,
and label work is conservatively preflighted before inference.

The default maximum is `100_000_000` work units and the hard maximum is
`500_000_000`. The selected limit and reserved/actual work are retained.
Study, coefficient, artist, and serialized-field ceilings remain independent.
Rows, studies, sensitivities, hypotheses, intervals, or diagnostics are never
sampled, reduced, or dropped to meet a limit.

Every new error has a stable public code and a contextual message. Input,
optimization, profile, quadrature, invariant, and resource failures return no
analysis or figure. Warning records describe valid but qualified results only;
they cannot carry a nonconvergence or tolerance failure.

## Results, schemas, and rendering

M6C follows the established mode-version convention:

- existing classical coefficient/meta results remain schema version 1;
- robust coefficient/meta variants use schema version 2; and
- posterior coefficient/Bayesian meta variants use schema version 3.

The coefficient JSON schema becomes a discriminated union without weakening
the existing v1 invariants. New immutable variants retain:

- analysis/mode/method identity and compatibility tier;
- exact coefficient or study identity, source/display positions, and input
  profile;
- estimand, scale, units, direction, null, dependence, and study-count audit;
- reported robust or posterior provenance and its unverified-source marker;
- pooled/posterior targets, intervals, evidence where defined, and explicit
  non-applicability reasons;
- robust residual/latent-weight/normalized-contribution records or complete
  Bayesian priors/sensitivities;
- optimizer/quadrature convergence, tolerances, work, software, warnings, and
  resource limits; and
- every value needed by the semantic renderer.

Constructors reject contradictory mode/method/profile identities, confidence
versus credible semantics, inconsistent probability partitions, interval
targets, BF orientation, incomplete sensitivity sets, non-reconciled work,
weight totals, study mappings, warning/error states, and renderer-facing values.
JSON contains no NaN or infinity.

The shared horizontal forest renderer performs no inference, optimization,
quadrature, or probability calculation. Robust/posterior coefficient rows use
the existing point/whisker geometry with explicit interval vocabulary. Meta
study, pooled-mean, and Bayesian prediction layers have distinct artist roles.
The null line is exactly the retained `null_value`. Extraction and heterogeneous
composition preserve the exact result object and all qualifications.

Implementation status (2026-09-15): this renderer and its extraction,
composition, identity-validation, and semantic-injection tests passed the M6C
pass-3 technical gate. Independent candidate review remains separate.

There is no grouped `ggcoefstats` surface in M6C. General regression,
meta-regression, dependent effects, multivariate/network/diagnostic meta-analysis,
publication-bias correction, selection models, model averaging, transformed
display scales, and raw-outcome effect-size calculation remain outside scope.

## Verification and acceptance criteria

### Formula and oracle evidence

- R4-M requires separately written log-density, score/KKT, latent-weight, and
  profile-likelihood checks in high precision. Fixed-`nu=4` R `dt`/
  `optimize` calculations may be retained as a development oracle. The authors'
  GPL reference implementation may be executed as external comparison evidence
  but no source or tests are copied into this MIT project.
- B5-M requires independently coded high-precision conditional/marginal
  calculations and locked `bayesmeta` comparisons using identical proper
  priors. Marginal likelihood, posterior `mu`/`tau`, prediction, and half/double
  sensitivity values are checked separately.
- Reported-summary paths require hand-built fixtures, source permutation,
  interval/probability boundary, Unicode/control-character, reserved-column,
  mutation, and exact JSON round-trip tests.
- Pinned ggstatsplot objects remain presentation/orientation evidence. Expected
  differences from upstream robust/Bayesian defaults are asserted explicitly
  and never tolerance-masked.

### Statistical and numerical validation

- R4-M uses locked development and held-out clean/contaminated grids at
  `k=10,20,50,500`, unequal standard errors, `tau=0` and positive heterogeneity,
  null and non-null means, one mild/gross displaced study, and row/unit
  transformations. The robust estimate must be affine-equivariant; at fixed
  fitted `mu`, `tau`, and standard error, a study's latent weight must decrease
  monotonically as its absolute residual displacement increases; and at gross
  displacement the pooled movement must be smaller than the M5 Gaussian REML
  movement on every locked fixture.
- On at least 2,000 held-out clean Student-t4 simulations per declared cell,
  the two-sided 99% Wilson interval around the observed coverage of the 95%
  R4-M profile interval must contain `0.95` for every `k>=20, tau>0` cell. For
  the visibly warned `k=10` through `k=19` band, or for a declared generating
  boundary cell with exactly `tau=0`, the 99% Wilson upper bound must be at
  least `0.95`; conservative overcoverage does not fail that cell. Joshua Myers
  approved the small-study rule on 2026-09-15 after the first locked
  `k=10, tau=0` finding, then provisionally approved the boundary-only extension
  after the fresh confirmation found conservative coverage at `k=50, tau=0`.
  The extension applies only to clean simulation acceptance; it changes no
  estimator, fitted-model behavior, reported interval, or runtime warning.
  Both failed runs remain retained with their original rules and statuses, and
  the post-confirmation exception is not described as predeclared evidence.
  M7 must explicitly reaffirm, replace, or remove the `tau=0` extension before
  1.0.
  Under the locked 10%
  gross-contamination grid, its median absolute pooled error must not exceed M5
  REML's. Simulation seeds and exact case counts are frozen before held-out
  execution; failing cells are not pooled away.
- B5-M requires scale/translation and study-permutation invariance, H0/H1 BF
  reciprocity, posterior-CDF monotonicity/normalization, tail-mass stress,
  boundary heterogeneity, dominant-study, three-study, and 500-study fixtures.
- Prior-predictive simulation-based calibration uses at least 2,000 locked
  held-out datasets for `mu` and `tau`. For each parameter, the maximum distance
  between the empirical posterior-CDF-at-truth distribution and Uniform(0,1)
  must not exceed the predeclared 99% Dvoretzky-Kiefer-Wolfowitz bound
  `sqrt(log(2/0.01)/(2*N))`. No seed, prior grid, sample size, or tolerance is
  changed after held-out evaluation.
- Fault injection must prove atomic failure on iteration, score, profile-root,
  quadrature, tail, BF, sensitivity, work, constructor, renderer, and grouped-
  unsupported boundaries. Classical v1 results must remain byte-for-byte stable
  on retained serialization fixtures.

Every new M6C analysis/result module must reach at least 90% branch coverage.
The full `make check`, license/dependency audit, build, minimal-wheel/core-import
smoke, oracle verifier, retained benchmark/work verifier, and reproducibility
gate must pass. Earlier accepted workloads may not regress beyond the M6 20%
threshold without an approved disposition.

## Proposed compatibility disposition

| Upstream or existing behavior | M6C proposal |
|---|---|
| robust coefficient/model objects | Adapted to strict caller-reported interval tables; fitted robust adapters deferred |
| Bayesian coefficient/model objects or draws | Adapted to strict caller-reported posterior-summary tables; no draws, fitting, or reconstructed BF |
| `meta.type="robust"` | Adapted fixed-Student-t4 aggregate sensitivity model with ML/profile inference and explicit no-prediction disposition |
| `meta.type="bayes"` | Adapted proper-prior NNHM with deterministic quadrature, numeric BF10, posterior heterogeneity, and true-effect prediction |
| automatic method choice or outlier deletion | Rejected |
| hidden tuning, prior defaults, retry, fallback, or work growth | Rejected |
| arbitrary model dispatch, meta-regression, dependent effects, publication-bias models | Deferred beyond M6C |

## Approval record

Joshua Myers approved without revision on 2026-09-15:

1. R4-C reported robust interval profile, opaque unverified provenance, no test
   reconstruction, no fitted adapter, and no significance filtering;
2. B5-C reported posterior-median/equal-tail/directional-probability profile,
   complete caller provenance, and no draws, BF reconstruction, or evidence
   language;
3. R4-M fixed-Student-t4 hierarchy, 10-study floor, deterministic multistart
   ML, profile-likelihood inference, latent-weight diagnostics, and explicit
   Q/I-squared/prediction non-applicability;
4. B5-M proper normal/half-normal priors with caller-supplied scales, numeric
   BF10, posterior heterogeneity and true-effect prediction, four sensitivity
   fits, and deterministic bounded quadrature;
5. mode-specific schema v2/v3 results, common semantic renderer, work/error
   contract, no new runtime dependency, no MCMC/RQMC, and no fallback; and
6. the three-pass verification loop, oracle/license boundary, simulation and
   calibration thresholds, compatibility dispositions, and explicit exclusions.

Joshua Myers additionally approved the warned-small-study conservative-coverage
amendment above on 2026-09-15. It changes no estimator, likelihood, interval,
warning, study floor, or result field and does not retroactively convert the
first held-out finding into passing evidence.

After the fresh confirmation produced the separate `k=50, tau=0` finding,
Joshua Myers provisionally approved the boundary-only extension on 2026-09-15.
The approved one-sided conservative rule therefore applies when `k<20` or the
declared generating `tau=0`; the symmetric rule remains for `k>=20, tau>0`.
This owner disposition clears the pass-2 calibration gate without modifying or
relabeling either retained artifact. It is explicitly temporary governance
debt: M7/1.0 hardening must reconsider the boundary calibration and record a
final disposition.

M7 completed that reconsideration on 2026-09-15. After reviewing the sealed
76,000-fit mapping and independent-seed 40,000-fit confirmation, Joshua Myers
approved reclassification of R4-M as experimental for 1.0. The mapping's single
`robust_meta_ambiguous_optimum` failure blocks reaffirmation under the approved
plan even though neither retained run triggered an undercoverage flag. The
estimator and strict refusal behavior remain unchanged; only the 1.x stability
boundary changes.

At the method-entry gate, this approval authorized M6C implementation and
acceptance-fixture construction only. Independent review, M6C acceptance,
combined M6 acceptance, and the `0.4` product decision remained separate and
could not be self-approved by the implementation owner. The later M6C review
and acceptance are recorded above and in `evidence/M6C_SIGNOFF.md`.
