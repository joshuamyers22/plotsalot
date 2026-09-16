# User guide

Plotsalot combines statistical analysis, structured results, and Matplotlib
rendering. Select a workflow by the question and data design, not by the desired
appearance of the final plot.

## Choose a workflow

| Task | Primary entry points | Important boundary |
|---|---|---|
| Compare one numeric sample with a reference | `gghistostats`, `ggdotplotstats` | One-sample assumptions and finite, non-degenerate data |
| Measure numeric association | `ggscatterstats`, `ggcorrmat` | Pair construction, multiplicity, and correlation assumptions |
| Compare independent groups | `ggbetweenstats` | Explicit group definition and approved contrast family |
| Compare repeated conditions | `ggwithinstats` | Explicit subject identity and complete analyzed blocks |
| Analyze categorical counts | `ggbarstats`, `ggpiestats` | Design selection and expected-count adequacy |
| Plot coefficients or combine studies | `ggcoefstats` | Declared scale, provenance, and model/profile restrictions |
| Repeat an analysis by an outer group | `grouped_*` functions | Atomic execution and per-group correction families |
| Combine existing plots | `combine_plots` | Results are retained while panels are rasterized |

For exact supported modes and deliberate adaptations, use the
[compatibility matrix](compatibility.md). Source signatures and docstrings remain
the authority for parameters and defaults.

## Separate analysis from rendering

Every main workflow has an analysis layer and a rendering layer. Use the combined
function for ordinary work:

```python
plot = gghistostats(data, "value", test_value=0.0)
```

Use separate calls when you want to render the same analysis more than once:

```python
analysis = analyze_gghistostats(data, "value", test_value=0.0)
first = render_gghistostats(analysis, title="Primary figure")
second = render_gghistostats(analysis, title="Alternate figure")
```

Rendered annotations are derived from typed result fields. Editing a Matplotlib
artist does not mutate the retained analysis.

## Correlation and grouped analysis

```python
from plotsalot import ggcorrmat, ggscatterstats, grouped_ggscatterstats

scatter = ggscatterstats(data, "x", "y")
matrix = ggcorrmat(data, ("x", "y", "z"))
by_cohort = grouped_ggscatterstats(data, "x", "y", "cohort")

print(scatter.result.estimate)
print(matrix.result.to_dict())
for group_plot in by_cohort.plots:
    group_plot.figure.savefig(f"group-{group_plot.title}.svg")
```

Classical matrices use pairwise-complete Pearson correlations and retain the
complete correction family. Robust association uses marginal 20% Winsorization
and explicit seeded percentile bootstrap intervals; it is not a high-breakdown
defense against arbitrary bivariate leverage.

## Independent and repeated comparisons

```python
from plotsalot import ggbetweenstats, ggwithinstats

between = ggbetweenstats(data, "treatment", "score")
within = ggwithinstats(
    repeated_data,
    "condition",
    "score",
    subject_id="participant",
    pairwise_display="all",
)

print(between.result.omnibus)
print(within.result.correction)
```

Independent classical comparisons use Welch-family methods. Repeated analyses
require explicit subject identifiers and use complete analyzed blocks. Display
filters do not change the retained pairwise family.

## Categorical analysis

Categorical workflows accept raw observations or aggregate nonnegative integer
frequencies:

```python
import polars as pl

from plotsalot import analyze_categorical, ggbarstats, ggpiestats

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
```

Both renderers consume the same categorical result contract. Pearson paths fail
their documented expected-count adequacy gate instead of silently switching to
an exact or simulated method.

## Coefficients and meta-analysis

Coefficient tables must declare their scale and conform to one supported
profile. Here is an interval profile:

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

The fitted-model adapter accepts only its documented Statsmodels OLS result
forms. The aggregate meta-analysis path accepts independent study summaries on
one declared comparable scale; it does not derive effects from raw outcomes or
silently change estimators.

Fixed-Student-t4 robust aggregate meta-analysis
(`meta_analytic_effect=True, type="robust"`) is experimental for 1.0. It remains
available with strict coded failure and no estimator fallback, but its dedicated
types and serialized variant are not stable 1.x contracts. Pin plotsalot and
retain provenance when using it. Classical and Bayesian aggregate modes are
separate methods rather than fallback replacements.

## Robust and Bayesian modes

Robust modes use the approved fixed-20%-trim/Winsorization contracts. Bayesian
modes use approved proper priors and bounded exact, quadrature, or randomized
quasi-Monte Carlo calculations. Supported mode coverage differs by workflow.

Stochastic requests require explicit reproducibility inputs where documented.
Work limits are checked before expensive computation, and an invalid stochastic
result never falls back to a classical result. See the
[M6 robust](M6_STATISTICAL_METHODS.md),
[Bayesian](M6B_STATISTICAL_METHODS.md), and
[coefficient/meta](M6C_STATISTICAL_METHODS.md) specifications.

## Group and compose plots

Grouped functions validate the whole request before returning output. If one
group is invalid, the operation raises and returns no partial group collection.

`combine_plots` retains each typed source result and source identity while
rasterizing its visual panel into the composed Matplotlib figure. Composition is
therefore result-preserving but not an editable merge of source artists.

## Resource limits and errors

Public workflows enforce explicit ceilings on rows, groups, matrix dimensions,
labels, hypotheses, rendered observations, panels, bootstrap work, and numerical
integration work as applicable. Limits are serialized with results where the
contract defines them.

Raise or lower a configurable ceiling only after considering memory, rendering,
and inferential consequences. Inputs are never silently sampled, groups are
never silently dropped, and unsupported keyword arguments fail rather than being
ignored.
