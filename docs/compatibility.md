# Upstream Compatibility Matrix

- Baseline revisions: see `upstream/manifest.json`
- Status: M2 implemented-surface disposition

Definitions:

- `prototype`: an intentionally incomplete walking-skeleton implementation.
- `planned`: accepted product scope but not implemented.
- `adapted`: Python exposes the capability through a different object model.
- `deferred`: deliberately outside the current release plan.
- `blocked`: implementation cannot start until a named decision is approved.

## ggstatsplot

| Export | Python surface | Target | Status |
|---|---|---:|---|
| `combine_plots` | `combine_plots` | 0.1 | Planned |
| `extract_caption` | `extract_caption` | 0.1 | Adapted; implemented for individual and grouped containers |
| `extract_stats` | `extract_stats` | 0.1 | Adapted; implemented for individual and grouped containers |
| `extract_subtitle` | `extract_subtitle` | 0.1 | Adapted; implemented for individual and grouped containers |
| `ggbarstats` | `ggbarstats` | 0.2 | Planned |
| `ggbetweenstats` | `ggbetweenstats` | 0.1 | Planned |
| `ggcoefstats` | `ggcoefstats` | 0.3 | Planned |
| `ggcorrmat` | `ggcorrmat` | 0.1 | Adapted; Pearson/Holm mode implemented |
| `ggdotplotstats` | `ggdotplotstats` | 0.1 | Adapted; labeled parametric mode implemented |
| `gghistostats` | `gghistostats` | M0/0.1 | Adapted; one-sample parametric mode implemented |
| `ggpiestats` | `ggpiestats` | 0.2 | Planned |
| `ggscatterstats` | `ggscatterstats` | 0.1 | Adapted; Pearson mode implemented |
| `ggwithinstats` | `ggwithinstats` | 0.2 | Planned |
| `grouped_ggbarstats` | same name | 0.2 | Planned |
| `grouped_ggbetweenstats` | same name | 0.1 | Planned |
| `grouped_ggcorrmat` | same name | 0.1 | Adapted; atomic per-group plot container implemented |
| `grouped_ggdotplotstats` | same name | 0.1 | Adapted; atomic per-group plot container implemented |
| `grouped_gghistostats` | same name | 0.1 | Adapted; atomic per-group plot container implemented |
| `grouped_ggpiestats` | same name | 0.2 | Planned |
| `grouped_ggscatterstats` | same name | 0.1 | Adapted; atomic per-group plot container implemented |
| `grouped_ggwithinstats` | same name | 0.2 | Planned |
| `theme_ggstatsplot` | `theme_ggstatsplot` | 0.1 | Planned |

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
