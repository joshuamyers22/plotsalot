# plotsalot

`plotsalot` is a planned Python implementation of the statistical-visualization
workflows in [`ggstatsplot`](https://github.com/IndrajeetPatil/ggstatsplot).

M0 and M1 are complete. The project remains an early one-method prototype and
is not ready for analytical or production use.

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

## Current prototype

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

Only the parametric one-sample prototype is implemented. See
[`docs/MILESTONE_0.md`](docs/MILESTONE_0.md),
[`docs/MILESTONE_1.md`](docs/MILESTONE_1.md),
[`docs/CONTRACTS.md`](docs/CONTRACTS.md),
[`docs/compatibility.md`](docs/compatibility.md), and
[`STATISTICAL_ANALYSIS_PLAN.md`](STATISTICAL_ANALYSIS_PLAN.md) for scope and
evidence gates.

The prototype is intentionally adapted rather than statistically identical to
upstream: it rejects non-finite and zero-variance samples and reports Cohen's d;
the pinned ggstatsplot oracle accepts those boundary fixtures and reports
Hedges' g. The retained fixtures make that distinction testable.

## License

Plotsalot is MIT licensed. See
[ADR-010](docs/adr/ADR-010-license-posture.md) for the accepted distribution and
upstream-notice rules.
