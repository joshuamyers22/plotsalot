# M6B Method-entry Audit

- Date: 2026-09-15
- Starting revision: `d4e6ccd`
- Scope: evidence used to prepare B1–B6; not implementation evidence
- Decision state: B1–B6 approved by Joshua Myers on 2026-09-15

## Pinned upstream behavior

The source audit used the accepted R 4.5.1 oracle and
`ggstatsplot@7a724cd0ab55668b9d0b2e84b12c711c5be68ac8`. The lock contains
`statsExpressions==2.1.1`, `BayesFactor==0.9.12-4.8`, and
`bayestestR==0.19.0`.

Applicable inspected paths were:

| Surface | Pinned backend behavior |
|---|---|
| `gghistostats`/`ggdotplotstats` | Bayesian one-sample helper; `BayesFactor::ttestBF(x, mu, rscale=bf.prior)` |
| `ggscatterstats` | Bayesian correlation helper receiving `bf.prior` |
| `ggcorrmat` | `correlation::correlation(..., bayesian=TRUE, bayesian_prior=bf.prior)` for each matrix pair |
| `ggbetweenstats` | two-level `ttestBF`; multi-level `anovaBF(y ~ x, rscaleFixed=bf.prior)` plus pairwise helpers |
| `ggwithinstats` | repeated `anovaBF` with subject row identity as a random term and `rscaleRandom=1` plus pairwise helpers |
| `ggbarstats`/`ggpiestats` | `contingencyTableBF(..., sampleType="indepMulti", fixedMargin="rows", priorConcentration=...)` for two-way tables |

The public surfaces commonly default `bf.prior` to `0.707`. The backend families
do not share one likelihood, nuisance prior, posterior algorithm, or sampling
plan. Upstream qualitative captions and package defaults therefore cannot serve
as a plotsalot B1–B6 specification.

The current BayesFactor manual confirms that `contingencyTableBF` distinguishes
Poisson, joint-multinomial, independent-multinomial, and hypergeometric sampling
plans; for `indepMulti`, a fixed row or column margin is required. It also
documents `priorConcentration=1` as the default. Source:
<https://cran.r-project.org/web/packages/BayesFactor/BayesFactor.pdf>.

## Python engine feasibility

The released project contract is Python `>=3.11`, with NumPy `>=2,<3` and SciPy
`>=1.16,<2`. The 2026-09-15 lock resolves separate Python-3.11 and Python-3.12+
NumPy/SciPy versions and already provides special distributions, log-gamma,
adaptive quadrature, and scrambled Sobol sequences.

PyMC and ArviZ remain legitimate future optional-engine candidates, but their
latest releases at audit time both require Python `>=3.12`. PyMC also brings a
probabilistic-programming/compiler stack that is unnecessary for the proposed
conjugate models. Pinning older releases only for Python 3.11 would add a split
engine/diagnostic contract without supplying the required family-wide Bayes
factor definitions. Sources:

- <https://pypi.org/project/pymc/> (PyMC 6.3.2, Python `>=3.12`, released
  2026-09-08);
- <https://pypi.org/project/arviz/> (ArviZ 1.3.0, Python `>=3.12`, released
  2026-08-11); and
- <https://docs.scipy.org/doc/scipy/reference/stats.qmc.html> (SciPy QMC and
  scrambled Sobol interface).

The exact bivariate-normal sampling distribution used in B2 traces to Fisher's
derivation (`doi:10.1093/biomet/10.4.507`). The proposed hypergeometric kernel
was separately checked at `rho=0` against the closed beta-form null density for
`n=4,5,10,30` before the proposal was marked review-ready. That check is entry
evidence only and must become a retained independent test during implementation.

This compatibility finding does not prove that MCMC is statistically unsuitable.
It supports the narrower B6 proposal: use the existing core for M6B models that
have exact marginal likelihoods/posteriors or bounded low-dimensional numerical
work, and require a new approval if M6C needs a full sampler.

## Deliberate method adaptations

| Concern | Upstream observation | B1–B6 proposal |
|---|---|---|
| Prior meaning | `bf.prior` is reused across helpers with backend-specific meaning | Explicit outcome-unit continuous scale, bounded-correlation prior, or Dirichlet cell concentration |
| Evidence display | Qualitative BF labels are common | Natural-log BF10 retained; bounded numeric BF10 display only |
| Posterior interval | Backend-dependent posterior summaries | Posterior median and equal-tail interval throughout |
| Independent groups | JZS t/ANOVA family | Proper homoscedastic conjugate cell-means model |
| Repeated conditions | `anovaBF` subject random term | Complete-block Helmert/compound-symmetry conjugate model |
| Correlation | Backend Bayesian correlation helper | Exact sample-correlation likelihood plus one-dimensional quadrature |
| Categorical | Gunel-Dickey family with selectable sampling plans | Fixed-total goodness-of-fit and fixed-row independent multinomial only |
| Computation | Backend defaults and posterior sampling | Closed form, bounded quadrature, or fixed RQMC with typed diagnostics |
| Failure | Backend warning/fallback behavior is not a plotsalot contract | Atomic typed failure; no retry, fallback, or partial plot |

## Entry conclusion

B1–B6 were approved without revision by Joshua Myers on 2026-09-15. Bayesian
implementation and fixtures may proceed under those exact decisions. Technical
verification, independent review, release acceptance, R4/M6C, final M6, and
`0.4` remain separate gates.
