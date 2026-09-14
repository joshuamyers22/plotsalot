# plotsalot

`plotsalot` is a planned Python implementation of the statistical-visualization
workflows in [`ggstatsplot`](https://github.com/IndrajeetPatil/ggstatsplot).

M0, M1, and M2 are complete. The approved frequentist univariate and correlation
surfaces have passed their technical and statistical gates. The project remains
pre-release and is not yet ready for production analytical use.

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

Only the approved classical modes are supported: one-sample Student tests,
per-label mean intervals, two-sided Pearson correlations with Fisher intervals,
and per-matrix Holm adjustment. Inputs are limited by default to 1,000,000 rows,
200 dot labels, 50 matrix variables, and 20 groups. Unsupported upstream
arguments and nonparametric, robust, and Bayesian modes remain deferred. See
[`docs/MILESTONE_0.md`](docs/MILESTONE_0.md),
[`docs/MILESTONE_1.md`](docs/MILESTONE_1.md),
[`docs/MILESTONE_2.md`](docs/MILESTONE_2.md),
[`docs/CONTRACTS.md`](docs/CONTRACTS.md),
[`docs/compatibility.md`](docs/compatibility.md), and
[`STATISTICAL_ANALYSIS_PLAN.md`](STATISTICAL_ANALYSIS_PLAN.md) for scope and
evidence gates.

Custom ceilings are explicit keyword arguments on the applicable M2 surfaces
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
