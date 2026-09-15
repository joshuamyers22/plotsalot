# plotsalot

`plotsalot` is a planned Python implementation of the statistical-visualization
workflows in [`ggstatsplot`](https://github.com/IndrajeetPatil/ggstatsplot).

M0 through M5 are complete, including the accepted `0.3` product gate. The
M6 robust/Bayesian work is active. The M6A robust continuous-analysis track is
implemented, independently reviewed, and accepted. M6B Bayesian data analysis
is also implemented, independently reviewed, and accepted. The detailed
R4/B5 M6C coefficient/meta method contract is approved; pass 1 is technically
verified and pass 2 passed under a provisional, boundary-only calibration
disposition that must be revisited in M7. Pass 3 and M6C candidate acceptance
remain open. The project remains pre-release and is not yet ready for
production analytical use.

## Development

```sh
make setup
make check
make build
```

The development-only R oracle and retained performance baseline are reproduced
separately:

```sh
make oracle
make benchmark
```

`make oracle` requires Docker and rebuilds the exact R 4.5.1/ggstatsplot
environment from `oracle/renv.lock`. Neither R nor Docker is a package runtime
dependency. `make check` verifies the checked-in oracle hashes and benchmark
shape without invoking Docker, R, or the network.

The package is Polars-first at tabular boundaries, uses explicit NumPy numerical
boundaries, and returns structured results alongside Matplotlib figures. R is
used only to create frozen development-time parity evidence; released artifacts
will not require R or network access.

## Current API

```python
import polars as pl

from plotsalot import gghistostats

plot = gghistostats(
    pl.DataFrame({"value": [1.0, 2.0, 3.0, 4.0, 5.0]}),
    "value",
    test_value=0.0,
)
plot.figure.savefig("histogram.svg")
print(plot.result.to_dict())
```

Analysis and rendering can also be separated so visual changes do not recompute
statistics:

```python
from plotsalot import analyze_gghistostats, render_gghistostats

analysis = analyze_gghistostats(data, "value", test_value=0.0)
plot = render_gghistostats(analysis, title="Observed values")
plot.axes["main"].grid(axis="y", alpha=0.2)
```

M6A adds explicit fixed-20%-trim robust modes to histograms, labeled dots,
scatter plots, correlation matrices, between-group comparisons, repeated
comparisons, and their existing grouped variants. Association intervals own
their RNG and require a seed:

```python
from plotsalot import ggbetweenstats, ggscatterstats

robust_scatter = ggscatterstats(
    data,
    "x",
    "y",
    type="robust",
    random_seed=20260914,
    bootstrap_resamples=1999,
)
robust_groups = ggbetweenstats(
    data,
    "treatment",
    "score",
    type="robust",
    pairwise_display="all",
)

print(robust_scatter.result.resampling)
print(robust_groups.result.pairwise)
```

Robust mode uses 20% trimmed locations, marginal 20% Winsorized Pearson
association, Yuen/Welch–Yuen independent comparisons, and trimmed
subject-difference/Winsorized repeated comparisons. It reports raw differences,
not a standardized robust effect. Correlation intervals are paired type-7
percentile bootstraps using PCG64DXSM; `bootstrap_resamples` must be an odd value
from 999 through 9,999 and total sampled-pair work is checked before any draw.
Marginal Winsorization is not a high-breakdown defense against arbitrary
bivariate leverage. Degenerate scale, inadequate effective sample, invalid
bootstrap yield, or resource exhaustion fails atomically and never falls back
to a classical method. See `docs/M6_STATISTICAL_METHODS.md` for exact formulas
and adaptation boundaries.

M2 also provides labeled means, Pearson scatter/correlation matrices, and atomic
grouped operations:

```python
from plotsalot import (
    ggcorrmat,
    ggdotplotstats,
    ggscatterstats,
    grouped_ggscatterstats,
)

dot = ggdotplotstats(data, "value", "label")
scatter = ggscatterstats(data, "x", "y")
matrix = ggcorrmat(data, ("x", "y", "z"))
grouped = grouped_ggscatterstats(data, "x", "y", "cohort")

print(scatter.result.estimate)
print(matrix.result.to_dict())
for group_plot in grouped.plots:
    group_plot.figure.savefig(f"group-{group_plot.title}.svg")
```

M3 adds Welch independent-group comparisons, explicit-subject repeated
comparisons, grouped variants, local theming, and result-preserving composition:

```python
from plotsalot import (
    combine_plots,
    ggbetweenstats,
    ggwithinstats,
    grouped_ggbetweenstats,
    theme_ggstatsplot,
)

between = ggbetweenstats(data, "treatment", "score")
within = ggwithinstats(
    repeated_data,
    "condition",
    "score",
    subject_id="participant",
    pairwise_display="all",
)
by_site = grouped_ggbetweenstats(data, "treatment", "score", "site")
combined = combine_plots(
    [between, within, by_site],
    columns=2,
    title="Comparison summary",
    panel_tags="A",
)

print(between.result.omnibus)
print(within.result.correction)
print(combined.result.panels[0].result is between.result)

custom_theme = theme_ggstatsplot()
```

M4 adds categorical bars and pies over one shared result contract. Inputs can be
raw observations or aggregate integer frequencies; independent, paired binary,
and grouped variants are explicit:

```python
from plotsalot import (
    analyze_categorical,
    ggbarstats,
    ggpiestats,
    grouped_ggbarstats,
)

frequencies = pl.DataFrame(
    {
        "response": ["no", "no", "yes", "yes"],
        "cohort": ["control", "treated", "control", "treated"],
        "count": [30, 10, 15, 25],
    }
)
analysis = analyze_categorical(
    frequencies,
    "response",
    "cohort",
    counts="count",
    pairwise_display="all",
)
bars = ggbarstats(frequencies, "response", "cohort", counts="count")
pies = ggpiestats(frequencies, "response", "cohort", counts="count")
site_data = pl.concat(
    [
        frequencies.with_columns(pl.lit("east").alias("site")),
        frequencies.with_columns(pl.lit("west").alias("site")),
    ]
)
by_site = grouped_ggbarstats(site_data, "response", "site", counts="count")

print(analysis.result.omnibus)
print(analysis.result.cells)
```

M5 adds strict coefficient plots and an explicit frequentist random-effects
meta-analysis. A coefficient table declares its scale and uses exactly one
estimate-only, interval, full-t, or full-z profile:

```python
from plotsalot import ggcoefstats

coefficients = pl.DataFrame(
    {
        "term": ["intercept", "dose", "age"],
        "estimate": [0.25, -0.40, 0.08],
        "conf_low": [-0.15, -0.75, 0.01],
        "conf_high": [0.65, -0.05, 0.15],
        "is_intercept": [True, False, False],
    }
)
coefficient_plot = ggcoefstats(
    coefficients,
    estimate_label="regression coefficient",
    effect_scale="linear predictor",
    effect_direction="positive is higher",
    effect_units="outcome units",
    stats_labels=False,
    exclude_intercept=True,
)
```

The fitted-model path accepts only an exact fitted Statsmodels OLS wrapper with
nonrobust or HC3 covariance. It snapshots the fitted result without refitting.
The meta-analysis path accepts independent aggregate study estimates:

```python
from plotsalot import ggcoefstats

studies = pl.DataFrame(
    {
        "term": ["Study A", "Study B", "Study C", "Study D", "Study E"],
        "estimate": [0.10, 0.32, 0.25, -0.05, 0.41],
        "standard_error": [0.08, 0.12, 0.10, 0.15, 0.09],
    }
)
forest = ggcoefstats(
    studies,
    meta_analytic_effect=True,
    estimand="mean treatment effect",
    effect_scale="mean difference",
    effect_direction="positive favors treatment",
    effect_units="points",
)

print(forest.result.meta_analysis.pooled)
print(forest.result.meta_analysis.heterogeneity)
```

This path uses the approved intercept-only REML estimator and modified
Hartung–Knapp inference. It requires explicit comparable-scale and independence
declarations, never derives effects from raw outcomes, never switches to a
fixed-effect or fallback estimator, and provides prediction intervals only for
five or more studies. Coefficient significance labels are available only for
complete t/z profiles, use reported/model-derived unadjusted p-values, and never
filter plotted coefficient rows.

One-way calls omit `y` and may supply an exact level-keyed `ratio`. Paired calls
require the same two levels on `x` and `y`, `paired=True`, and
`proportion_test=False`; they use the approved exact binomial test over
discordant counts. Pearson paths fail on inadequate expected counts rather than
switching methods. Pairwise and per-`y` stratum Holm families are retained
separately, and `pairwise_display` changes annotations only.

The approved classical, M6A robust-continuous, and M6B Bayesian data-analysis
modes are supported. Classical mode includes one-sample Student tests,
per-label mean intervals, two-sided Pearson correlations with Fisher intervals,
Welch independent comparisons, paired tests, and Greenhouse–Geisser-corrected
repeated-measures ANOVA, categorical Pearson tests, and exact binary paired
inference. Holm is the default pairwise/matrix adjustment. M3
requires an explicit subject identifier and analyzes/renders complete repeated
blocks only. Inputs are limited by default to 1,000,000 rows, 200 dot labels,
50 matrix variables, 20 groups or comparison levels, 1,000,000 rendered
observations, 10,000 subject paths, 20 composed panels, 20 categorical levels
per axis, 400 categorical cells/labels, 190 categorical pairwise hypotheses,
and a weighted categorical total of 1,000,000,000. Robust association adds a
default 100,000,000 and hard 500,000,000 resample-work ceiling. Bayesian paths
use approved proper priors and bounded exact, quadrature, or RQMC calculations;
see `docs/M6B_STATISTICAL_METHODS.md` for their family-specific contracts.
Unsupported upstream arguments, nonparametric modes, and robust categorical
analysis remain deferred. M6C exposes renderer-independent analysis for
strict caller-reported robust confidence and posterior credible coefficient
summaries plus pass-2 robust Student-t4 and proper-prior Bayesian normal-normal
aggregate meta-analysis engines. Rendering remains assigned to pass 3; the
pass-2 statistical gate passed under the provisional boundary-only calibration
disposition that must be revisited in M7. See
[`docs/MILESTONE_0.md`](docs/MILESTONE_0.md),
[`docs/MILESTONE_1.md`](docs/MILESTONE_1.md),
[`docs/MILESTONE_2.md`](docs/MILESTONE_2.md),
[`docs/MILESTONE_3.md`](docs/MILESTONE_3.md),
[`docs/MILESTONE_4.md`](docs/MILESTONE_4.md),
[`docs/MILESTONE_5.md`](docs/MILESTONE_5.md),
[`docs/MILESTONE_6.md`](docs/MILESTONE_6.md),
[`docs/M6_STATISTICAL_METHODS.md`](docs/M6_STATISTICAL_METHODS.md),
[`docs/M6B_STATISTICAL_METHODS.md`](docs/M6B_STATISTICAL_METHODS.md),
[`docs/M6C_STATISTICAL_METHODS.md`](docs/M6C_STATISTICAL_METHODS.md),
[`docs/CONTRACTS.md`](docs/CONTRACTS.md),
[`docs/compatibility.md`](docs/compatibility.md), and
[`STATISTICAL_ANALYSIS_PLAN.md`](STATISTICAL_ANALYSIS_PLAN.md) for scope and
evidence gates.

Custom ceilings are explicit keyword arguments on the applicable M2/M3/M4 surfaces
and are serialized in `result.limits`. Invalid data, unsupported methods, and
an invalid member of a grouped operation raise an error; grouped calls never
return a partial result.

The implementation is intentionally adapted rather than statistically identical to
upstream: it rejects non-finite and zero-variance samples and reports Cohen's d;
the pinned ggstatsplot oracle accepts those boundary fixtures and reports
Hedges' g. The retained fixtures make that distinction testable.

## License

Plotsalot is MIT licensed. See
[ADR-010](docs/adr/ADR-010-license-posture.md) for the accepted distribution and
upstream-notice rules.
