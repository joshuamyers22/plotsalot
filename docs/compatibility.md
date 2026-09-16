# Upstream Compatibility Matrix

- Baseline revisions: see `upstream/manifest.json`
- Status: M0–M6 complete; combined 0.4 product gate accepted; M7 closure
  ledger approved 2026-09-15

The approved machine-readable M7 disposition ledger is
[`m7/compatibility-disposition.json`](m7/compatibility-disposition.json). It
stabilizes the existing adapted surface for all 22 exports, records explicit
post-1.0 or rejected dispositions for remaining capability clusters, and is
validated against the pinned upstream revision and public Python exports.
Joshua Myers approved this 1.0 scope through M7-D1 on 2026-09-15. Milestone-era
sections below retain milestone provenance, but their disposition text has been
reconciled to the current M6 implementation so an implemented robust or Bayesian
mode is never described as currently deferred.

Definitions:

- `prototype`: an intentionally incomplete walking-skeleton implementation.
- `planned`: accepted product scope but not implemented.
- `adapted`: Python exposes the capability through a different object model.
- `deferred`: deliberately outside the current release plan.
- `blocked`: implementation cannot start until a named decision is approved.

## ggstatsplot

| Export | Python surface | Target | Status |
|---|---|---:|---|
| `combine_plots` | `combine_plots` | 0.1 | Adapted; typed result-preserving raster composition implemented |
| `extract_caption` | `extract_caption` | 0.1 | Adapted; implemented for individual and grouped containers |
| `extract_stats` | `extract_stats` | 0.1 | Adapted; implemented for individual and grouped containers |
| `extract_subtitle` | `extract_subtitle` | 0.1 | Adapted; implemented for individual and grouped containers |
| `ggbarstats` | `ggbarstats` | 0.2 | Adapted; shared classical categorical analysis and normalized bars implemented |
| `ggbetweenstats` | `ggbetweenstats` | 0.1/M6A | Adapted; Welch parametric and Yuen/Welch–Yuen robust modes implemented |
| `ggcoefstats` | `ggcoefstats` | 0.3 | Adapted M5A strict table/OLS and M5B REML/Hartung–Knapp modes implemented and accepted |
| `ggcorrmat` | `ggcorrmat` | 0.1/M6A | Adapted; Pearson and bounded Winsorized/Holm modes implemented |
| `ggdotplotstats` | `ggdotplotstats` | 0.1/M6A | Adapted; labeled parametric and fixed-trim robust modes implemented |
| `gghistostats` | `gghistostats` | M0/0.1/M6A | Adapted; one-sample parametric and analytic fixed-trim robust modes implemented |
| `ggpiestats` | `ggpiestats` | 0.2 | Adapted; shared classical categorical analysis and faceted pies implemented |
| `ggscatterstats` | `ggscatterstats` | 0.1/M6A | Adapted; Pearson and seeded marginal-Winsorized modes implemented |
| `ggwithinstats` | `ggwithinstats` | 0.2/M6A | Adapted; explicit-subject complete-block parametric and robust modes implemented |
| `grouped_ggbarstats` | same name | 0.2 | Adapted; atomic grouped categorical bars implemented |
| `grouped_ggbetweenstats` | same name | 0.1/M6A | Adapted; atomic per-group Welch and robust containers implemented |
| `grouped_ggcorrmat` | same name | 0.1/M6A | Adapted; atomic classical/robust containers with stable streams implemented |
| `grouped_ggdotplotstats` | same name | 0.1/M6A | Adapted; atomic classical/robust containers implemented |
| `grouped_gghistostats` | same name | 0.1/M6A | Adapted; atomic classical/robust containers implemented |
| `grouped_ggpiestats` | same name | 0.2 | Adapted; atomic grouped categorical pies implemented |
| `grouped_ggscatterstats` | same name | 0.1/M6A | Adapted; atomic classical/robust containers with stable streams implemented |
| `grouped_ggwithinstats` | same name | 0.2/M6A | Adapted; atomic classical/robust complete-block containers implemented |
| `theme_ggstatsplot` | `theme_ggstatsplot` | 0.1 | Adapted; immutable local Matplotlib theme implemented |

## Known adaptation rules

- Dotted R parameters become snake_case.
- Columns are explicit names/selectors, not tidy-evaluated expressions.
- `ggplot2` and `ggproto` composition become typed specifications and owned
  Matplotlib artists.
- R model objects become an allowlist of Statsmodels results plus a tidy
  coefficient-table protocol.
- Custom distributions are explicit protocol objects; names are never resolved
  through dynamic global lookup.
- Visual equivalence means statistical and semantic-layer parity, not pixels.

## M2 method and argument disposition

The implemented public signatures are allowlists. Arguments exposed in those
signatures are supported as specified in `M2_STATISTICAL_METHODS.md`; other
upstream arguments fail as unknown Python keyword arguments and are deferred.

| Surface | Supported method/arguments | Explicit M2 disposition |
|---|---|---|
| `gghistostats` | one-sample parametric test, `test_value`, three alternatives, `conf_level`, `binwidth`, `title`; fixed-trim robust and approved Bayesian modes added by M6 | nonparametric modes, effect-size intervals, centrality controls, and arbitrary ggplot layers remain deferred |
| `ggdotplotstats` | one-sample parametric annotation, per-label mean intervals, `show_intervals`, resource limits; fixed-trim robust and approved Bayesian modes added by M6 | other test and interval families, label expressions, and arbitrary layers remain deferred |
| `ggscatterstats` | two-sided Pearson test and Fisher interval; Winsorized robust and approved Bayesian correlation modes added by M6 | regression smoothing, marginal distributions, partial correlation, point labels, and other correlation methods remain deferred |
| `ggcorrmat` | Pearson, pairwise completeness, Holm or no adjustment, `sig_level`; Winsorized robust and approved Bayesian matrices added by M6 | other correlations, corrections, matrix layouts, and partial correlations remain deferred |
| grouped M2 surfaces | one explicit group column, first-observed order, at most 20 groups, per-group rendering | pooled cross-group corrections, facets, nested groups, and partial success rejected/deferred |

All M2 renderers use owned Matplotlib objects. Grouped functions return one
validated `StatsPlot` per group inside `GroupedStatsPlot`; they do not claim
equivalence to an upstream combined ggplot object.

## M3 method and argument disposition

The M3 public signatures are allowlists governed by
`M3_STATISTICAL_METHODS.md`. Unsupported upstream parameters fail as unknown
Python keyword arguments; accepted selector values are validated rather than
ignored.

| Surface | Supported method/arguments | Explicit M3 disposition |
|---|---|---|
| `ggbetweenstats` | two-sided parametric Welch family with Holm or no adjustment and pointwise intervals/effects; fixed-trim Yuen/Welch–Yuen and approved Bayesian modes added by M6 | upstream Games–Howell is adapted to Welch-plus-Holm; equal-variance, nonparametric, effect-size intervals, arbitrary contrasts, and arbitrary layers remain deferred |
| `ggwithinstats` | explicit-subject complete-block parametric family; fixed-trim robust and approved Bayesian modes added by M6 | omitted/inferred subjects and row-index fallback are rejected; incomplete subjects are excluded from inference and rendering; other missingness populations, sphericity switching, and corrections remain deferred |
| grouped comparison surfaces | one explicit outer-group column, first-observed outer-group order, deterministic inner-level order, at most 20 outer groups, per-group correction families, atomic failure | no adjustment is pooled across outer groups; nested grouping, partial success, and inferred subject scope are rejected/deferred |
| `combine_plots` | individual or grouped plotsalot containers, deterministic automatic or explicit rectangular layout, `guides="keep"`, shared labels, titles/subtitles/captions, optional alphabetic/numeric panel tags, at most 20 flattened panels | source typed result objects and grouped identities are retained, while source figures are rasterized; guide collection, shared-axis inference, patchwork expressions, and arbitrary Matplotlib figures are deferred |
| `theme_ggstatsplot` | immutable `StatsTheme` with local figure, axes, grid, text, and accent settings | returns/applies an owned Matplotlib style and never mutates `rcParams`; ggplot theme objects and pixel-identical styling are deferred |

For repeated designs, a duplicate subject-condition cell fails before null-value
removal so ambiguity cannot be hidden by missingness. Condition/level order is
categorical order when explicitly declared and otherwise deterministic scalar
order. The R oracle is a compatibility reference: upstream and Python test
statistics are compared where their approved methods coincide, while the
pairwise and effect-size adaptations above are asserted separately by analytic
and independent-reference tests.

## M4 method and argument disposition

The M4 bar and pie signatures are explicit allowlists governed by
`M4_STATISTICAL_METHODS.md`. Both renderers consume the same owned table and
typed result; visual differences do not imply separate inference.

| Surface | Supported method/arguments | Explicit M4 disposition |
|---|---|---|
| `ggbarstats`, `ggpiestats` | classical count-table families plus approved fixed-total/fixed-row Bayesian modes added by M6 | Pearson's C is adapted to Cohen's w/Cramér's V and asymptotic McNemar to exact binomial/Cohen's g; continuity correction, nonparametric, robust, paired Bayesian, simulation, structural-zero, and multicategory paired paths remain deferred |
| independent follow-ups | complete `x`-level pairwise Pearson family and per-`y` goodness-of-fit family; Holm or no adjustment; display filtering | upstream Fisher exact pairwise tests are adapted to Pearson behind the approved adequacy gate; upstream unadjusted stratum labels are adapted to a separate Holm family |
| grouped categorical surfaces | one explicit outer group, first-observed group order, common `x` color domain, complete nested results, atomic failure | no correction is pooled across outer groups; partial success, nested grouping, and category-domain sampling are rejected/deferred |

Every Pearson test requires all expected counts at least one and, for 2×2
tables, all at least five; other tables require at least 80% at five or more.
Failure never triggers an automatic exact or simulated replacement. Defaults
limit inputs to one million rows, 20 levels per axis, 400 cells/labels, 190
pairwise hypotheses, 20 groups, and weighted total 1,000,000,000.

## M5 disposition

`MILESTONE_5.md` contracts `ggcoefstats` as a strict Polars coefficient-table
and narrow fitted-Statsmodels adapter rather than universal R-style model
tidying. M5 requires estimate-only and approved inferential coefficient modes,
plus one approved frequentist random-effects meta-analysis over independent,
comparable study estimates. Joshua Myers approved K1–K4 for strict
estimate/interval/full-inference tables and an exact fitted-OLS adapter. M5A
implementation is authorized. Joshua Myers also approved MA1–MA4, authorizing
M5B implementation. The explicit Polars study-effect path, owned arrays,
schema-v1 result, REML weights and convergence record, modified
Hartung–Knapp inference, prediction behavior, heterogeneity records, semantic
forest renderer, extraction, and composition are now implemented.

M5A implements four explicit table profiles and one exact fitted Statsmodels OLS
adapter. It rejects broad model dispatch, WLS/GLS/GLM and raw result objects,
uses explicit structured identities and intercept metadata, retains reported or
model-derived inference provenance, and makes no multiplicity or model-validity
claim. This is adapted rather than equivalent to upstream's broad R tidying
dispatch.

The approved MA1–MA4 specification retains upstream's REML between-study
variance estimator but adapts its default normal pooled inference to a modified
Hartung–Knapp t method. It requires explicit independent-study and common-scale
declarations, computes a prediction interval only with at least five studies,
and forbids estimator fallback. The Python path is therefore classified as
adapted rather than equivalent to upstream's default normal pooled inference.
The pinned-R fixture retains the raw upstream object, independently solves the
approved REML/modified-Hartung–Knapp path in base R, and verifies pinned
metafor's normal and `adhoc` results at its iterative precision. Joshua Myers
independently reviewed and accepted both tracks and the combined M5/`0.3`
candidate on 2026-09-14.

Robust/Bayesian coefficient and meta-analysis paths were deferred at M5 and are
now implemented under the approved M6C contract below. Bayes-factor captions,
automatic term creation, heuristic duplicate-term concatenation, arbitrary
model dispatch, ANOVA effect sizes, exponentiated/transformed parameters,
ellipsis forwarding, and dynamic R plotting objects remain deferred. The M5
classifications passed their implementation evidence and accountable review.

## M6A robust-method disposition

M6A adds only `type="robust"` on the continuous M2/M3 families and their
existing grouped variants. These paths are classified as adapted because the
approved estimands, intervals, degree-of-freedom rules, RNG, and failure policy
are explicit plotsalot contracts rather than an unqualified copy of upstream
defaults.

| Surface | Implemented M6A behavior | Upstream/adaptation disposition |
|---|---|---|
| `gghistostats`, `ggdotplotstats` | fixed `trim_fraction=0.20`; analytic trimmed-mean t test and two-sided interval; raw difference; per-label trimmed centrality | Adapted from upstream bootstrap-t one-sample intervals; standardized robust effect is deliberately absent |
| `ggscatterstats` | marginal 20% Winsorized Pearson estimate/test; WRS2-style `h-2` reference df; required unsigned-64-bit seed; paired type-7 percentile bootstrap interval | Adapted from upstream ordinary `n-2` test reference and normal interval; marginal Winsorization is explicitly not described as high-breakdown bivariate robustness |
| `ggcorrmat` | every pair retained; pairwise completeness; identity-derived deterministic streams; Holm or none; pointwise bootstrap intervals | Adapted with owned RNG/work accounting; partial correlations and other robust estimators remain deferred |
| `ggbetweenstats` | two-level Yuen; 3–20-level Welch–Yuen omnibus; complete Yuen pairwise family; raw trimmed-location effects | Adapted; stochastic/standardized upstream robust effects are not emitted, and intervals remain pointwise |
| `ggwithinstats` | explicit-subject complete blocks; two-level trimmed subject differences; WRS2-style Winsorized repeated omnibus; matching subject-difference pairwise family | Adapted from upstream marginal two-level comparison; inferred subjects, alternative missingness populations, and fallback corrections are rejected/deferred |
| grouped M6A surfaces | atomic preflight/execution; stable typed identity streams; per-group hypothesis families; retained root work | Adapted; partial success, pooled cross-group corrections, hidden RNG, and automatic work reduction are rejected |

`bootstrap_resamples` is restricted to odd values from 999 through 9,999.
Default and hard resample-work ceilings are 100,000,000 and 500,000,000 sampled
pairs. The full request is rejected before drawing if it exceeds its selected
ceiling; rows, pairs, variables, or groups are never silently reduced. Invalid
effective counts, non-finite input, degenerate Winsorized scale/covariance,
insufficient valid bootstrap replicates, and robust repeated-matrix degeneracy
fail without returning a classical result. Robust categorical analysis remains
deferred; robust coefficient/meta-analysis is handled separately by M6C.

## M6B Bayesian-method disposition

M6B adds explicit `type="bayes"` paths to the retained data-analysis surfaces.
Every path is classified as adapted and reports only numeric BF10 values with
H1/H0 orientation; upstream qualitative evidence labels are not reproduced.

| Surface | Implemented M6B behavior | Upstream/adaptation disposition |
|---|---|---|
| `gghistostats`, `ggdotplotstats` | proper standardized normal-inverse-gamma model; posterior medians/equal-tail intervals; exact BF10 and half/double prior sensitivity | Adapted proper conjugate model; no data-derived prior scale |
| `ggscatterstats`, `ggcorrmat` | exact sampling-density correlation posterior and BF10 under a transformed symmetric-beta prior; adaptive bounded quadrature | Adapted from upstream correlation BF helpers with explicit prior and numerical provenance |
| `ggbetweenstats` | homoscedastic conjugate cell-means model; common-mean H0; complete pointwise posterior contrast/BF family | Heteroscedastic selection and qualitative BF thresholds are rejected |
| `ggwithinstats` | explicit complete blocks; orthonormal Helmert/compound-symmetry inference; Savage–Dickey pair evidence | Inferred subjects, imputation, sphericity switching, and fallback models are rejected |
| `ggbarstats`, `ggpiestats` | fixed-total/fixed-row Dirichlet-multinomial models; zero cells retained; row/category contrasts and posterior Cramer's V | Paired categorical Bayesian inference and structural-zero models are deferred |
| grouped M6B surfaces | atomic execution; aggregate work provenance; identity-derived seeds and preflight before RQMC generation | Partial results, hidden retries, and automatic work reduction are rejected |

The native engine uses locked NumPy/SciPy exact expressions, adaptive
Gauss–Kronrod quadrature, or eight independently scrambled 4,096-point Sobol
replicates. Bayesian coefficient and meta-analysis are handled separately by M6C.

## Approved M6C coefficient/meta disposition

The approved R4/B5 contract in `M6C_STATISTICAL_METHODS.md` keeps
`ggcoefstats` behind strict Polars boundaries and adds no fitted robust/Bayesian
model adapter or posterior-draw input.

| Surface | Approved M6C behavior | Upstream/adaptation disposition |
|---|---|---|
| robust coefficients | caller-reported point/confidence interval plus explicit unverified method/tuning/interval provenance; no reconstructed test | Adapted strict summary profile; fitted robust objects remain deferred |
| posterior coefficients | caller-reported median/equal-tail credible interval/directional probability partition plus explicit unverified model/prior/computation provenance | Adapted estimation-only profile; draws, fitted objects, and reconstructed BF remain deferred |
| robust aggregate meta-analysis | fixed-Student-t4 independent-study hierarchy; deterministic multistart ML and profile-likelihood inference; latent weights retained; no automatic outlier flag or prediction interval | **Experimental for 1.0** after the locked M7B mapping retained an ambiguous-optimum failure; runtime behavior and strict no-fallback refusal are retained, but its dedicated types and serialized variant are outside the stable 1.x promise |
| Bayesian aggregate meta-analysis | normal-normal hierarchy; caller-supplied proper normal/half-normal scales; numeric BF10, posterior heterogeneity, true-effect prediction, four sensitivity fits, bounded quadrature | Adapted proper-prior native model; universal/data-derived priors and MCMC are rejected |

Joshua Myers approved these entry classifications without revision on
2026-09-15. The robust and posterior coefficient analysis profiles passed the
M6C pass-1 technical gate. Both aggregate engines are implemented. The M7
mapping and confirmation retained no undercoverage flags, but one mapping fit
failed with `robust_meta_ambiguous_optimum`; the approved plan therefore blocked
reaffirmation. After independent review, Joshua Myers reclassified robust
aggregate meta-analysis as experimental for 1.0 on 2026-09-15. The shared
semantic renderer, exact result extraction, heterogeneous composition, and
resource benchmark retain their accepted technical evidence.
