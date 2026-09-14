# Upstream Compatibility Matrix

- Baseline revisions: see `upstream/manifest.json`
- Status: M0 inventory; classifications may narrow after statistical review

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
| `extract_caption` | `extract_caption` | 0.1 | Planned |
| `extract_stats` | `extract_stats` | 0.1 | Planned |
| `extract_subtitle` | `extract_subtitle` | 0.1 | Planned |
| `ggbarstats` | `ggbarstats` | 0.2 | Planned |
| `ggbetweenstats` | `ggbetweenstats` | 0.1 | Planned |
| `ggcoefstats` | `ggcoefstats` | 0.3 | Planned |
| `ggcorrmat` | `ggcorrmat` | 0.1 | Planned |
| `ggdotplotstats` | `ggdotplotstats` | 0.1 | Planned |
| `gghistostats` | `gghistostats` | M0/0.1 | Prototype |
| `ggpiestats` | `ggpiestats` | 0.2 | Planned |
| `ggscatterstats` | `ggscatterstats` | 0.1 | Planned |
| `ggwithinstats` | `ggwithinstats` | 0.2 | Planned |
| `grouped_ggbarstats` | same name | 0.2 | Planned |
| `grouped_ggbetweenstats` | same name | 0.1 | Planned |
| `grouped_ggcorrmat` | same name | 0.1 | Planned |
| `grouped_ggdotplotstats` | same name | 0.1 | Planned |
| `grouped_gghistostats` | same name | 0.1 | Planned |
| `grouped_ggpiestats` | same name | 0.2 | Planned |
| `grouped_ggscatterstats` | same name | 0.1 | Planned |
| `grouped_ggwithinstats` | same name | 0.2 | Planned |
| `theme_ggstatsplot` | `theme_ggstatsplot` | 0.1 | Planned |

## qqplotr

| Export | Python surface | Target | Status |
|---|---|---:|---|
| `stat_qq_point` | `stat_qq_point` / `qq_points` | 0.1 | Blocked by ADR-010 and method spec |
| `stat_qq_line` | `stat_qq_line` / `qq_line` | 0.1 | Blocked by ADR-010 and method spec |
| `stat_qq_band` | `stat_qq_band` / `qq_band` | 0.1–0.4 | Blocked by ADR-010 and method spec |
| `stat_pp_point` | `stat_pp_point` / `pp_points` | 0.1 | Blocked by ADR-010 and method spec |
| `stat_pp_line` | `stat_pp_line` / `pp_line` | 0.1 | Blocked by ADR-010 and method spec |
| `stat_pp_band` | `stat_pp_band` / `pp_band` | 0.1–0.4 | Blocked by ADR-010 and method spec |
| `geom_qq_band` | `BandSpec` and renderer | 0.1 | Adapted; blocked by ADR-010 |
| `GeomQqBand` | internal renderer protocol | 0.1 | Adapted; no `ggproto` emulation |
| `StatQqPoint` | internal calculation protocol | 0.1 | Adapted; no `ggproto` emulation |
| `StatQqLine` | internal calculation protocol | 0.1 | Adapted; no `ggproto` emulation |
| `StatQqBand` | internal calculation protocol | 0.1–0.4 | Adapted; no `ggproto` emulation |
| `StatPpPoint` | internal calculation protocol | 0.1 | Adapted; no `ggproto` emulation |
| `StatPpLine` | internal calculation protocol | 0.1 | Adapted; no `ggproto` emulation |
| `StatPpBand` | internal calculation protocol | 0.1–0.4 | Adapted; no `ggproto` emulation |
| `runShinyExample` | notebook/widget gallery | Post-1.0 | Deferred |

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
