# Getting started

This tutorial creates a small one-sample analysis, inspects its structured
result, and customizes the rendered figure. It uses deterministic synthetic data
and requires no network access.

## Install and import

Plotsalot supports Python 3.11 and newer. After the first PyPI release:

```sh
python -m pip install plotsalot
```

Import Polars and the one-sample histogram workflow:

```python
import polars as pl

from plotsalot import gghistostats
```

## Prepare the data

Each row is one observed numeric value. The selected sample must contain enough
finite, non-degenerate observations for the requested analysis.

```python
data = pl.DataFrame(
    {
        "value": [1.2, 1.8, 2.1, 2.4, 2.9, 3.2, 3.7, 4.1],
    }
)
```

Plotsalot uses Polars at tabular boundaries, then copies selected numeric values
into an owned NumPy boundary. It does not align inputs through a hidden pandas
index.

## Analyze and render

Test the sample against a reference value and render its distribution:

```python
plot = gghistostats(
    data,
    "value",
    test_value=2.0,
    title="Observed values",
)
```

`plot` is a `StatsPlot`. Its main public components are:

- `plot.figure`: the owned Matplotlib figure;
- `plot.axes`: validated named axes;
- `plot.annotations`: title, subtitle, and caption data; and
- `plot.result`: the immutable structured statistical result.

## Inspect the result

Use structured fields or `to_dict()` rather than parsing plot labels:

```python
result = plot.result

print(result.estimate)
print(result.interval)
print(result.test)
print(result.to_dict())
```

The classical one-sample result describes the implemented Student-test workflow
and its pointwise confidence interval. It does not establish causality, practical
importance, representativeness, or adequacy of the data-generating assumptions.

## Customize and save the figure

The returned Matplotlib objects remain caller-owned:

```python
plot.axes["main"].grid(axis="y", alpha=0.2)
plot.figure.savefig("observed-values.svg")
```

To change presentation without recomputing the statistical result, separate the
analysis and rendering steps:

```python
from plotsalot import analyze_gghistostats, render_gghistostats

analysis = analyze_gghistostats(data, "value", test_value=2.0)
rerendered = render_gghistostats(analysis, title="A second presentation")

assert rerendered.result is analysis.result
```

## Choose another workflow

The same Polars-first boundary applies to multivariate workflows:

```python
from plotsalot import ggscatterstats

paired = pl.DataFrame(
    {
        "x": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        "y": [1.3, 1.9, 3.4, 3.8, 5.2, 5.7, 7.3, 7.8],
    }
)

scatter = ggscatterstats(paired, "x", "y")
print(scatter.result.estimate)
```

Supported families expose only their approved modes. Robust association
intervals additionally require an explicit seed and bounded bootstrap work; see
the [user guide](USER_GUIDE.md) and method specification before selecting them.

Invalid samples, unsupported modes, and requests beyond resource ceilings raise
an error rather than silently changing the estimator or returning a partial
grouped result.

## Next steps

- Use the [user guide](USER_GUIDE.md) to select a workflow family.
- Read [interpretation and limitations](INTERPRETATION_AND_LIMITATIONS.md) before
  relying on inferential output.
- Consult [contracts](CONTRACTS.md) for ownership, serialization, and rendering
  behavior.
- Check the [compatibility matrix](compatibility.md) for deliberate adaptations
  and deferred upstream features.
