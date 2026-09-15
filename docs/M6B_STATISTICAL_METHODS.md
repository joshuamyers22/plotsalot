# M6B Bayesian Method Proposal

- Status: approved for implementation
- Version: 0.1.0
- Date: 2026-09-15
- Product/statistical owner: Joshua Myers
- Implementation owner: Codex
- Applies to: M6B Bayesian data-analysis surfaces only

## Approval boundary

This companion to `M6_STATISTICAL_METHODS.md` proposes B1–B6. It does not
by itself accept an implementation or close M6B. Joshua Myers approved B1–B6
without revision on 2026-09-15, authorizing Bayesian implementation, fixtures,
public API changes, and the B6 core-engine clarification exactly as specified.

The proposal deliberately adapts the pinned ggstatsplot/BayesFactor behavior.
It uses proper, fully parameterized plotsalot priors and reports numeric Bayes
factors without qualitative adjectives. It does not claim numerical equivalence
to the upstream JZS t/ANOVA models. The pinned R implementation remains an
oracle for surface and orientation checks; independent equations and calibration
are the acceptance authority for the adapted Python models.

M6B covers Bayesian univariate, correlation, independent/repeated comparison,
categorical, matrix, and existing grouped surfaces. Bayesian coefficient and
meta-analysis work remains in M6C. General regression, custom priors/models,
partial correlation, non-normal continuous likelihoods, missing-data models,
and paired categorical Bayesian analysis remain out of scope.

## Common notation and standardized continuous prior

Every continuous call receives a finite `prior_location` in outcome units and a
strictly positive finite `prior_scale` in outcome units. One-sample calls default
`prior_location` to their `test_value`; comparison calls require it explicitly.
No prior scale is estimated from the analyzed observations.

For a continuous response, define `z=(y-prior_location)/prior_scale`. The base
normal-inverse-gamma prior is

```text
sigma_squared ~ InverseGamma(shape=2, scale=1)
mu | sigma_squared ~ Normal(0, sigma_squared / 2)
```

and maps locations/effects back to source units. `InverseGamma` uses density
proportional to `b^a * x^(-a-1) * exp(-b/x)`. The model is proper. The main
prior is accompanied by sensitivity fits at `0.5 * prior_scale` and
`2 * prior_scale`; these are retained as separate evidence records and never
silently replace the requested analysis.

This prior is a product decision, not a universal default. Documentation must
show its prior-predictive implications and require callers to choose a scale
that is meaningful before examining the result. Changing `prior_location`,
`prior_scale`, or a categorical/correlation prior creates a different analysis
identity.

## B1: reporting, intervals, and evidence

### Posterior reporting

- The common point summary is the posterior median. For symmetric conjugate
  location posteriors it equals the posterior mean, but the retained target is
  still `posterior_median`.
- The uncertainty summary is a two-sided equal-tail credible interval, default
  level `0.95`; accepted levels are finite values from `0.80` through `0.99`.
- Directional output retains `P(effect > null)`, `P(effect < null)`, and any
  point mass exactly at the null. It does not convert them to p-values.
- Practical equivalence is absent unless a later approved API supplies an
  outcome-specific interval. M6B supplies no default ROPE and no automatic
  practical-significance statement.
- A posterior credible interval is never called a confidence, prediction, or
  simultaneous interval. Pairwise and matrix intervals are pointwise.

### Bayes-factor contract

All M6B inferential results include a Bayes factor. `BF10` always means

```text
p(retained data or sufficient statistic | H1)
------------------------------------------------
p(retained data or sufficient statistic | H0)
```

with prior model odds 1:1 only when posterior model probability is also shown.
The canonical stored quantity is finite natural-log `log_bf10`. A renderer may
show numeric `BF10` in `[1e-6, 1e6]`; values beyond that range render as a
one-sided numeric bound. No “anecdotal”, “moderate”, “strong”, “significant”, or
similar evidence adjective is produced.

Every evidence record names H0, H1, observation/sampling plan, prior, log base,
calculation algorithm, and whether it is omnibus or pointwise. Reciprocal output
is computed as `log_bf01=-log_bf10`, not by a second fit. Failure to obtain a
finite, tolerance-qualified value fails the analysis atomically. There is no
classical fallback and no caption based only on posterior interval exclusion.

The primary and two sensitivity `log_bf10` values are always retained. A
renderer displays only the primary value and exposes sensitivity through result
extraction. Prior-predictive validation is a locked development artifact for
each family; it is not a per-call accept/reject test.

Every top-level M6B analysis has the stated omnibus or scalar Bayes factor.
Derived posterior summaries do not automatically acquire a separate model
comparison: a contrast has its own BF only where B2–B4 explicitly defines its
null model and prior.

## B2: one-sample and association models

### One-sample normal location

For retained finite values `x_i`, use the standardized normal likelihood
`z_i ~ Normal(mu, sigma_squared)`. H0 fixes `mu=0`; H1 uses the common proper
normal-inverse-gamma prior. H0 uses the identical inverse-gamma scale prior.

The targets are the posterior population mean
`prior_location + prior_scale * mu`, its raw difference from `test_value`, and
their equal-tail intervals. The posterior median population mean is the
histogram/dot centrality. The null requires `test_value == prior_location`; a
different prior center is rejected rather than changing the BF hypothesis.
Bayes factors use the exact conjugate marginal likelihood in log space.

For the base univariate prior, set `a0=2`, `b0=1`, `kappa0=2`, and `m0=0`.
For sample count `n`, mean `z_bar`, and centered sum of squares `S`, retain

```text
kappa_n = kappa0 + n
m_n = (kappa0*m0 + n*z_bar) / kappa_n
a_n = a0 + n/2
b_n = b0 + S/2 + kappa0*n*(z_bar-m0)^2/(2*kappa_n)
```

and use the normal-inverse-gamma log marginal likelihood

```text
lgamma(a_n)-lgamma(a0) + a0*log(b0)-a_n*log(b_n)
+ 0.5*(log(kappa0)-log(kappa_n)) - n*log(2*pi)/2.
```

H0 integrates the identical inverse-gamma prior with `mu=0`; its `b_n` uses
`b0 + sum(z_i^2)/2` and omits the kappa term. Multigroup forms use the matching
Gaussian linear-model determinant formula, evaluated through factorizations and
solves rather than explicit inverses.

The inherited one-sample selection/missingness audit applies. At least three
finite observations are required. Ties and zero observed variance are allowed
because the proper variance prior keeps the posterior defined; a non-finite
posterior hyperparameter, nonpositive scale, or failed result invariant is not.

### Pearson correlation

For `n` pairwise-complete observations with sample Pearson correlation `r`, the
Bayesian observation model is the exact sampling density of `r` under iid
bivariate normal observations with population correlation `rho`. H0 fixes
`rho=0`. Under H1,

```text
(rho + 1) / 2 ~ Beta(correlation_prior_shape,
                     correlation_prior_shape)
```

with default shape `1.0` (uniform on `[-1, 1]`) and sensitivity shapes `0.5`
and `2.0`. This statistic-level model has no unrecorded location or marginal-
scale prior. Its target is `rho`, summarized by posterior median, equal-tail
interval, and directional probabilities.

After dropping factors constant in `rho`, the exact correlation likelihood
kernel is

```text
L(rho; r, n) =
  (1-rho^2)^((n-1)/2)
  * (1-rho*r)^(-(n-3/2))
  * hyp2f1(1/2, 1/2, n-1/2, (1+rho*r)/2).
```

The production calculation evaluates its logarithm, includes the normalized
beta prior and the Jacobian for `rho=tanh(u)`, and independently verifies that
the full density reduces to the known beta-form null density at `rho=0`.

Posterior normalization and `BF10` use independently checked adaptive
one-dimensional quadrature of the exact density. At least four complete pairs,
strictly positive marginal variances, and `abs(r)<1` are required. Perfect
sample correlation fails with `bayesian_perfect_correlation_unsupported` rather
than returning an infinite or boundary approximation.

`ggcorrmat(type="bayes")` analyzes every unique pair under the same prior. Each
pair is a pointwise model comparison with prior odds 1:1; Bayes factors are not
p-values and receive no Holm/FDR adjustment. Matrix membership never depends on
evidence, and presentation filtering cannot remove a pair from the result.
Partial correlation and one-sided model hypotheses are excluded.

## B3: independent and repeated comparisons

### Independent groups

For explicitly ordered groups, standardize the outcome and fit the homoscedastic
normal cell-means model

```text
z_i | group=j ~ Normal(mu_j, sigma_squared)
sigma_squared ~ InverseGamma(2, 1)
mu_j | sigma_squared ~ Normal(0, sigma_squared / 2)
```

independently across the `mu_j` conditional on the common variance. H1 includes
all ordered cell means. H0 replaces them with one common mean carrying the same
base prior. `BF10` is the exact conjugate marginal-likelihood ratio and tests
equality of group means under a common residual variance; it is not evidence
for equality of complete group distributions.

The posterior targets are each group population mean, every stable-order raw
mean contrast, and their posterior medians/equal-tail intervals/directional
probabilities. Each pairwise `BF10` compares the corresponding two-cell model
with its common-mean submodel using only those two retained groups. Omnibus and
pairwise Bayes factors are distinct pointwise evidence records. There is no
frequentist multiplicity adjustment or automatic evidence threshold; the full
declared family is retained.

Every group needs at least three observations and the total residual degrees of
freedom must be positive. The model deliberately assumes one residual variance;
heteroscedastic Bayesian comparison is excluded rather than selected by a
diagnostic. `prior_location` and `prior_scale` are shared across groups and must
be supplied before analysis.

### Repeated conditions

Use the inherited explicit-subject, complete-block population. Standardize all
outcomes with the shared caller prior. For `J` ordered conditions, let `H` be the
deterministic orthonormal Helmert matrix with `H.T @ 1 = 0`. For each subject,
split the response vector into its scalar subject mean `a_i` and within-subject
contrast vector `c_i=H.T @ z_i`.

The centrality component is the base normal-inverse-gamma model for `a_i` with
population grand mean `g`. The inferential component is

```text
c_i ~ MultivariateNormal(delta, sigma_squared * I_(J-1))
sigma_squared ~ InverseGamma(2, 1)
delta | sigma_squared ~ MultivariateNormal(0,
                                            sigma_squared / 2 * I_(J-1))
```

H0 fixes `delta=0`; H1 uses the stated prior. The exact conjugate marginal
likelihood gives omnibus `BF10`. This model assumes spherical covariance in the
orthonormal within-subject contrast space, equivalent to a compound-symmetry
condition covariance for the inferential component. No sphericity correction,
missing-block imputation, or mixed-model fallback is applied.

Condition means are reconstructed as `g + H @ delta` and mapped to source units.
Pairwise targets are ordered differences of those means. Pairwise Bayes factors
are exact marginal-likelihood comparisons for the corresponding linear
constraint within the full complete-block model; they are not refits on a
different subject subset. For contrast vector `l`, H0 fixes `l.T @ delta=0` and
retains the H1 conditional prior for all orthogonal nuisance contrasts. The
implementation evaluates the equivalent Savage–Dickey density ratio
`BF01 = posterior_density(0) / prior_density(0)` using the exact marginal
Student-t densities and verifies it against the constrained-model marginal
likelihood. All pairwise summaries and evidence are pointwise and retained in
stable order.

At least three complete subjects and two conditions are required, with inherited
subject/condition ceilings. Singular observed covariance does not itself reject
the proper posterior, but invalid prior/posterior matrices or numerical loss of
positive definiteness fails without jitter.

## B4: categorical models

### One-way goodness of fit

Counts use the exact M4 raw/count-weighted audit. H0 fixes category probabilities
to the keyed normalized `ratio` vector `q`. Under H1,

```text
p ~ Dirichlet(alpha)
alpha_k = prior_cell_concentration * K * q_k
```

where `K` is the retained category count. The default per-cell concentration is
`1.0`; sensitivities use `0.5` and `2.0`. All `q_k` and `alpha_k` must be
strictly positive. The exact multinomial and Dirichlet-multinomial marginal
likelihoods define `BF10` under a fixed-total sampling plan.

For counts `n_k`, `N=sum(n_k)`, and `A=sum(alpha_k)`, the retained H1 log
marginal is

```text
lgamma(N+1) - sum(lgamma(n_k+1))
+ lgamma(A) - lgamma(A+N)
+ sum(lgamma(alpha_k+n_k) - lgamma(alpha_k)).
```

H0 uses the matching multinomial log likelihood at `q`; its combinatorial term
cancels in `log_bf10` but remains independently testable.

Targets are each posterior category probability and deviation `p_k-q_k`, with
posterior median, equal-tail interval, and direction probabilities. No single
signed scalar is substituted for the global model comparison.

### Independent association

For an `R x K` table, row totals are fixed (`indepMulti`, fixed rows). H0 has one
shared column-probability vector with uniform base `q_k=1/K` and
`Dirichlet(prior_cell_concentration * K * q)`. H1 has one independent vector
with the identical prior for each row. The exact product-multinomial/
Dirichlet-multinomial marginal likelihood gives global `BF10`.

Posterior targets include every row-conditional probability, stable row-pair
probability contrast within each category, and Cramer's V computed from the
posterior joint table using the observed fixed row shares. All intervals are
pointwise. M6B defines only the global association Bayes factor for this family;
row-pair/category contrasts are posterior estimation records and are not given
an undeclared pairwise BF.

Zero observed cells are allowed. Empty retained margins, non-integer/negative
counts, nonpositive prior cells, and structural-zero specifications fail.
Bayesian paired categorical analysis is explicitly deferred; `subject_id` or a
paired Bayesian request fails rather than being treated as independent.

## B5: coefficient and meta-analysis boundary

B5 is not an M6B implementation item. M6B adds no coefficient-table posterior
profile, fitted Bayesian adapter, or Bayesian meta-analysis. Those remain M6C
work and require a separate B5/R4 proposal covering likelihoods, dependence,
heterogeneity, prediction, diagnostics, and small-study behavior.

Approval of this B5 boundary approves only the deferral. It does not authorize
M6C, and it prevents M6B results or quasi-Monte Carlo points from being passed
off as general fitted-model posterior draws.

## B6: native engine, numerical work, and reproducibility

### Engine decision

M6B uses the already required locked NumPy/SciPy core. It adds no PyMC, ArviZ,
JAX, compiler, Bayesian extra, network action, or persistent posterior artifact.
This resolves ADR-006 for M6B only; M6C may propose a separately isolated
sampling extra if its approved models require one.

Bayes factors and analytically available posterior summaries use closed-form log
marginal likelihoods and SciPy special distributions. Correlation uses adaptive
Gauss-Kronrod quadrature in transformed correlation space with
`epsabs=1e-12`, `epsrel=1e-10`, and at most 200 subdivisions. The result retains
algorithm, bounds/transformation, tolerances, evaluations, error estimate, and
convergence status. A warning, exhausted ceiling, non-finite term, or estimated
error above `max(epsabs, epsrel*abs(integral))` is a typed failure.

### Derived posterior approximation

When a nonlinear or multivariate derived target lacks a stable closed form,
plotsalot uses randomized quasi-Monte Carlo (RQMC), not MCMC. The approved design
is eight independently scrambled Sobol replicates of 4,096 points each, using
identity-derived child seeds and inverse-CDF transformations of the exact
conjugate posterior. A caller integer `random_seed` is required on those paths.
There is no warmup, adaptation, thinning, Markov chain, divergence, tree depth,
or acceptance statistic.

The result retains scrambler, dimension, replicate/point counts, root and child
seed identities, pooled summary, replicate estimates, and nested-prefix
stability checks. R-hat and MCMC ESS are marked with the typed reason
`not_applicable_rqmc_independent_replicates`; they are never populated with
invented values. Acceptance requires:

- every replicate and transformation to complete with finite values;
- replicate standard error for each displayed posterior median/probability no
  larger than `0.005` of that target's posterior interval width (or `1e-4` for
  dimensionless probabilities when the width is zero);
- each displayed interval endpoint to change by no more than `0.01` of the
  full-sample interval width between the nested 2,048- and 4,096-point summaries;
  and
- exact same-seed replay under the locked Python/NumPy/SciPy/platform contract.

Failure does not add points, retry with a new seed, loosen a tolerance, switch
algorithms, or return a partial plot. A later caller-adjustable approximation
budget requires separate approval.

### Work and grouped identity

One quadrature evaluation and one generated scalar RQMC coordinate each count
as one Bayesian work unit. Default maximum work is `100_000_000`; the hard
maximum is `500_000_000`. Complete scalar, matrix, pairwise, and grouped work is
preflighted before inference. Existing row, variable, group, level, subject,
hypothesis, category, cell, artist, and composition ceilings remain independent.
Correlation preflight reserves the conservative QUADPACK evaluation ceiling for
all normalization, sensitivity, quantile, and null-tail integrations; results
retain the lower actual evaluation/work count. Matrix and grouped preflights sum
that reservation for every member before the first member is evaluated.

Canonical analysis and typed group/pair/contrast/category identities plus the
root seed are hashed with SHA-256 into deterministic child seeds. Mapping cannot
depend on Python `hash()`, presentation order, worker timing, or failure order.
M6B is synchronous and serial. One invalid member or failed numerical diagnostic
makes the complete grouped/matrix result fail atomically.

### Results and rendering

Bayesian schema variants retain sample audit, likelihood, complete prior,
hypotheses, posterior targets, summaries, interval definition, directional
probabilities, primary/sensitivity evidence, numerical engine/version/settings,
work, diagnostics/applicability reasons, warnings, and compatibility tier.
Full RQMC points are not retained. Constructors reject contradictory priors,
orientations, intervals, model identities, sensitivity sets, seed/work records,
and renderer-facing values.

Renderers remain analysis-free. Centrality and interval artists consume the
retained posterior summaries; captions consume the retained bounded numeric
Bayes-factor representation. Extraction and composition preserve the exact
Bayesian result object and every qualification.

## Verification and compatibility policy

- Closed-form paths require separately coded log-marginal and posterior checks,
  reciprocal BF fixtures, affine/unit transformations, extreme finite inputs,
  and high-precision references.
- Correlation requires exact-density normalization checks, independent
  high-precision quadrature, null/positive/negative/boundary fixtures, and prior
  sensitivity.
- RQMC requires same-seed replay, identity-order invariance, alternate-seed
  agreement within declared error, nested-resolution diagnostics, ceiling and
  fault injection, and calibrated posterior coverage on locked validation
  simulations.
- Categorical models require hand-calculable beta/Dirichlet cases, category/row
  permutation metamorphics, sparse/zero cells, fixed-margin verification, and
  independent log-gamma calculations.
- Pinned R objects are retained for every public family. Expected differences
  from BayesFactor's JZS priors, posterior interval convention, evidence labels,
  and upstream sampling are explicitly asserted rather than tolerance-masked.
- Every new Bayesian analysis and result module must reach at least 90% branch
  coverage; the full check/audit/build/minimal-wheel/oracle/benchmark gates must
  pass before independent review.

## Proposed compatibility disposition

| Upstream behavior | M6B proposal |
|---|---|
| `type="bayes"` | Adapted explicit mode using plotsalot models and typed results |
| `bf.prior=0.707` JZS paths | Adapted to explicit outcome-unit normal-inverse-gamma prior or named correlation/categorical prior |
| qualitative BF labels | Rejected; numeric bounded BF10 display only |
| one-sample Bayesian subtitle | Adapted normal-location posterior/evidence with posterior-median centrality |
| Bayesian scatter/matrix | Adapted exact sample-correlation likelihood, pointwise BF family, no partial correlation |
| Bayesian between comparisons | Adapted homoscedastic conjugate cell-means model with complete pointwise contrasts |
| Bayesian repeated comparisons | Adapted complete-block Helmert/compound-symmetry conjugate model |
| categorical `indepMulti`, fixed rows | Adapted exact Dirichlet-multinomial model; structural zeros and paired mode rejected |
| arbitrary posterior/model inputs | Deferred to separately approved M6C boundaries |
| hidden RNG, retries, or fallback | Rejected |

## Approval record

Joshua Myers approved without revision on 2026-09-15:

1. B1 posterior-median/equal-tail reporting, numeric `BF10` orientation, required
   sensitivity records, and no qualitative evidence labels or default ROPE;
2. B2's proper conjugate one-sample model and exact sample-correlation model;
3. B3's homoscedastic independent cell-means model and complete-block
   Helmert/compound-symmetry repeated model, including pointwise pairs;
4. B4's fixed-total/fixed-row Dirichlet-multinomial models and paired deferral;
5. B5's complete deferral to a later M6C-specific proposal; and
6. B6's NumPy/SciPy closed-form/quadrature/RQMC engine, numerical thresholds,
   seed/work contract, MCMC-diagnostic non-applicability, and no fallback.

This approval authorizes implementation and acceptance-fixture construction for
M6B only. It does not accept an implementation, approve R4/M6C, close M6, or
approve the `0.4` release.
