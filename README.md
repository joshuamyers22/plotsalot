# plotsalot

`plotsalot` is a planned Python implementation of the statistical-visualization
workflows in [`ggstatsplot`](https://github.com/IndrajeetPatil/ggstatsplot) and
the Q–Q/P–P diagnostics in [`qqplotr`](https://github.com/aloy/qqplotr).

The project is in milestone M0: source baselining, compatibility design,
statistical specification, licensing review, and a small `gghistostats` walking
skeleton. It is not ready for analytical or production use.

## Development

```sh
make setup
make check
make build
```

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

Only the parametric one-sample prototype is implemented. See
[`docs/MILESTONE_0.md`](docs/MILESTONE_0.md),
[`docs/compatibility.md`](docs/compatibility.md), and
[`STATISTICAL_ANALYSIS_PLAN.md`](STATISTICAL_ANALYSIS_PLAN.md) for scope and
evidence gates.

## Licensing boundary

`ggstatsplot` is MIT licensed and `qqplotr` is GPL-3. No `qqplotr` source may be
copied or translated into this repository until ADR-010 is resolved through
qualified review. Current Q–Q/P–P planning is based on public API behavior and
published statistical methods only.

Public repository visibility does not itself grant an open-source license to
Plotsalot. See [ADR-010](docs/adr/ADR-010-license-posture.md) for the licensing
decision that must be resolved before `qqplotr`-derived work begins.
