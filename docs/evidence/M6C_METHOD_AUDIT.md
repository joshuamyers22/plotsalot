# M6C Method-entry Audit

- Date: 2026-09-15
- Starting revision: `d8f0485520fa6b5dd883eecba9504b0f899e2447`
- Scope: evidence used to prepare R4/B5; not implementation evidence
- Decision state: R4/B5 entry proposal approved by Joshua Myers on 2026-09-15

## Inherited surface and contract

The accepted M5 `ggcoefstats` surface already separates strict reported
coefficient tables from exact fitted Statsmodels OLS results and requires an
explicit independent aggregate-study table for meta-analysis. Its renderer,
identity, scale, study, and no-refit boundaries are suitable for M6C and do not
need a second plotting API.

The pinned upstream `ggcoefstats` source exposes robust and Bayesian meta modes
through broad R backend dispatch. That behavior does not identify one Python
likelihood, robustness tuning rule, prior, prediction target, diagnostic,
convergence threshold, or bounded-work policy. It is therefore presentation and
orientation evidence, not the M6C statistical authority.

## Robust meta-analysis review

Wang et al. propose a tractable tMeta hierarchy in which the same latent weight
scales within- and between-study variation, producing a marginal Student-t
distribution for each aggregate estimate. They show that posterior latent
weights decrease for distant studies and use an ECME maximum-likelihood
algorithm. Source: <https://pmc.ncbi.nlm.nih.gov/articles/PMC12527545/>.

The authors' public R reference was inspected at commit
`14425a10e6ad8535100aa091d3f1b7b62503fd55`. The inspected hashes are:

- `tmeta.R`: `39074a69a5a6470f7c87b8cb4d21f91a6117486724f47c9d88590bdd81897a0a`;
- `metaini.R`: `9e55f9ac2b6e4e2879f7cabd833de3f308ebd2ac0628bad554cbd2fa91f6d06c`.

That source is GPL-licensed. Plotsalot is MIT-licensed. The reference code may
be executed outside the package as black-box development evidence, but its code,
comments, tests, and implementation structure must not be copied. Production
formulas are derived from the published model and independently implemented and
reviewed.

The paper estimates degrees of freedom adaptively. M6C instead proposes
`nu=4` as a deliberate compatibility adaptation. Estimating a robustness
parameter from small collections creates a weakly identified third parameter
and permits silent convergence toward a Gaussian analysis. Fixed `nu` makes
the sensitivity estimand, weight calculation, and resource contract stable.
The proposal also declines the paper's asymptotic outlier classification:
weights are retained as model diagnostics, never converted into automatic
deletion or a dichotomous outlier claim.

## Bayesian meta-analysis review

The normal-normal hierarchical model provides analytic Gaussian calculations
conditional on heterogeneity and leaves only one-dimensional integration over
`tau`. Röver's `bayesmeta` work documents direct evaluation of posterior mean,
heterogeneity, shrinkage, and prediction without a general MCMC engine:
<https://arxiv.org/abs/1711.08683>.

Röver et al. review weakly informative heterogeneity priors, including the
half-normal family, emphasize that the scale must be meaningful on the effect
scale, and note that proper priors are necessary for marginal likelihoods and
Bayes factors:
<https://arxiv.org/abs/2007.08352>.

Those findings support a caller-supplied proper normal prior for `mu`, a
caller-supplied proper half-normal prior for `tau`, half/double sensitivity, and
deterministic one-dimensional quadrature. They do not support a universal
heterogeneity scale. M6C therefore adds no default prior scale, MCMC engine,
PyMC/ArviZ extra, draw artifact, RQMC seed, or hidden data-dependent prior.

## Coefficient-summary review

A reported interval or posterior summary cannot prove the validity of the model,
covariance estimator, robustness claim, likelihood, prior, or computation that
produced it. M6C therefore uses complete table-wide profiles and an explicit
`caller_reported_unverified` marker. Robust coefficients include no reconstructed
test. Posterior coefficients include no reconstructed Bayes factor. Fitted
robust/Bayesian object support remains deferred until an exact class, extraction
surface, model identity, and independent evidence are separately approved.

## Entry conclusion

The approved R4/B5 methods are narrow enough for the existing core architecture:
strict table ingestion, a fixed robust likelihood, and a conjugate Bayesian
hierarchy with bounded quadrature. They resolve the method, prior, dependence,
heterogeneity, prediction, diagnostics, small-study, work, license, and fallback
questions left open by M6B B5. Joshua Myers approved the entry decisions without
revision on 2026-09-15; implementation and fixture construction are authorized,
while technical verification and later acceptance remain separate gates.
