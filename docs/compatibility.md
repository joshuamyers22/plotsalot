# Upstream Compatibility Matrix

- Baseline revisions: see `upstream/manifest.json`
- Status: M0–M4 complete; M5 detailed contract prepared

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
| `ggbetweenstats` | `ggbetweenstats` | 0.1 | Adapted; Welch parametric/Holm mode implemented |
| `ggcoefstats` | `ggcoefstats` | 0.3 | Contracted; implementation blocked on M5 method approval |
| `ggcorrmat` | `ggcorrmat` | 0.1 | Adapted; Pearson/Holm mode implemented |
| `ggdotplotstats` | `ggdotplotstats` | 0.1 | Adapted; labeled parametric mode implemented |
| `gghistostats` | `gghistostats` | M0/0.1 | Adapted; one-sample parametric mode implemented |
| `ggpiestats` | `ggpiestats` | 0.2 | Adapted; shared classical categorical analysis and faceted pies implemented |
| `ggscatterstats` | `ggscatterstats` | 0.1 | Adapted; Pearson mode implemented |
| `ggwithinstats` | `ggwithinstats` | 0.2 | Adapted; explicit-subject complete-block parametric mode implemented |
| `grouped_ggbarstats` | same name | 0.2 | Adapted; atomic grouped categorical bars implemented |
| `grouped_ggbetweenstats` | same name | 0.1 | Adapted; atomic per-group Welch container implemented |
| `grouped_ggcorrmat` | same name | 0.1 | Adapted; atomic per-group plot container implemented |
| `grouped_ggdotplotstats` | same name | 0.1 | Adapted; atomic per-group plot container implemented |
| `grouped_gghistostats` | same name | 0.1 | Adapted; atomic per-group plot container implemented |
| `grouped_ggpiestats` | same name | 0.2 | Adapted; atomic grouped categorical pies implemented |
| `grouped_ggscatterstats` | same name | 0.1 | Adapted; atomic per-group plot container implemented |
| `grouped_ggwithinstats` | same name | 0.2 | Adapted; atomic per-group complete-block container implemented |
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
| `gghistostats` | one-sample parametric test, `test_value`, three alternatives, `conf_level`, `binwidth`, `title` | nonparametric, robust, Bayesian, effect-size interval, centrality controls, and arbitrary ggplot layers deferred |
| `ggdotplotstats` | one-sample parametric annotation, per-label mean intervals, `show_intervals`, resource limits | other test families, interval families, label expressions, and arbitrary layers deferred |
| `ggscatterstats` | two-sided Pearson test and Fisher interval | regression smoothing, marginal distributions, partial correlation, point labels, robust/Bayesian modes, and other correlation methods deferred |
| `ggcorrmat` | Pearson, pairwise completeness, Holm or no adjustment, `sig_level` | other correlations, corrections, matrix layouts, partial correlations, and Bayesian output deferred |
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
| `ggbetweenstats` | two-sided parametric mode; Welch t for two levels; Welch ANOVA for 3–20 levels; Welch pairwise t; Holm or no adjustment; pointwise mean and contrast intervals; Hedges' g or partial omega squared | upstream Games–Howell post-hoc comparisons are adapted to the approved Welch-plus-Holm family; equal-variance, nonparametric, robust, Bayesian, effect-size intervals, arbitrary contrasts, and arbitrary layers are deferred |
| `ggwithinstats` | explicit `subject_id`; complete pairs/blocks; paired t for two conditions; repeated-measures ANOVA for 3–20; always-primary Greenhouse–Geisser correction; paired post-hoc t tests; Holm or no adjustment | omitted/inferred subjects and upstream row-index fallback are rejected; incomplete subjects are excluded from both inference and rendering; the omnibus effect is the approved F-to-partial-omega conversion, not upstream sums-of-squares output; other missingness, sphericity-switch, correction, robust, and Bayesian modes are deferred |
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
| `ggbarstats`, `ggpiestats` | raw or nonnegative integer `counts`; one-way Pearson goodness-of-fit with exact keyed `ratio`; two-way Pearson independence; binary paired exact-binomial inference; noncentral effect intervals; count/percentage labels | upstream Pearson omnibus statistics are retained; Pearson's C is adapted to Cohen's w/Cramér's V; upstream asymptotic McNemar is adapted to exact binomial/Cohen's g; continuity correction, nonparametric, robust, Bayesian, simulation, structural-zero, and multicategory paired paths are deferred |
| independent follow-ups | complete `x`-level pairwise Pearson family and per-`y` goodness-of-fit family; Holm or no adjustment; display filtering | upstream Fisher exact pairwise tests are adapted to Pearson behind the approved adequacy gate; upstream unadjusted stratum labels are adapted to a separate Holm family |
| grouped categorical surfaces | one explicit outer group, first-observed group order, common `x` color domain, complete nested results, atomic failure | no correction is pooled across outer groups; partial success, nested grouping, and category-domain sampling are rejected/deferred |

Every Pearson test requires all expected counts at least one and, for 2×2
tables, all at least five; other tables require at least 80% at five or more.
Failure never triggers an automatic exact or simulated replacement. Defaults
limit inputs to one million rows, 20 levels per axis, 400 cells/labels, 190
pairwise hypotheses, 20 groups, and weighted total 1,000,000,000.

## M5 planned disposition

`MILESTONE_5.md` contracts `ggcoefstats` as a strict Polars coefficient-table
and narrow fitted-Statsmodels adapter rather than universal R-style model
tidying. M5 requires estimate-only and approved inferential coefficient modes,
plus one approved frequentist random-effects meta-analysis over independent,
comparable study estimates. Exact K1–K4/MA1–MA4 method decisions remain blocked
pending Joshua Myers's approval.

Robust/Bayesian meta-analysis, Bayes-factor captions, automatic term creation,
heuristic duplicate-term concatenation, arbitrary model dispatch, ANOVA effect
sizes, exponentiated/transformed parameters, ellipsis forwarding, and dynamic R
plotting objects are provisionally deferred. Final classifications require M5
implementation evidence and accountable review.
