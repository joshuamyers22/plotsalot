# plotsalot

`plotsalot` is an independent Python library for statistical visualizations with
structured, extractable results. It provides Polars-first analysis workflows and
Matplotlib figures inspired by the public behavior of
[`ggstatsplot`](https://github.com/IndrajeetPatil/ggstatsplot).

The project is pre-1.0 alpha software. Its classical, robust, Bayesian,
categorical, coefficient, and meta-analysis families have passed their recorded
M0–M6 gates, and M7A–M7C compatibility hardening is complete; M7D release
closeout remains. Fixed-
Student-t4 robust aggregate meta-analysis is retained as experimental for 1.0
after its locked M7 calibration; other supported modes follow their documented
stability classifications. Do not treat a successful computation or plot as
automatic validation of a statistical model or a substantive conclusion.

## Install

Plotsalot supports Python 3.11 and newer on Linux and macOS. Install the current
release from PyPI:

```sh
python -m pip install plotsalot
```

For development from a checkout:

```sh
make setup
```

R and Docker are development-only oracle tools. They are not package runtime
dependencies.

## Quick start

```python
import polars as pl

from plotsalot import gghistostats

data = pl.DataFrame({"value": [1.0, 2.0, 3.0, 4.0, 5.0]})
plot = gghistostats(data, "value", test_value=0.0)

print(plot.result.to_dict())
plot.figure.savefig("histogram.svg")
```

Each plotting function returns a typed container with a Matplotlib figure, named
axes, annotations, and a structured result. Analysis and rendering can also be
separated so visual changes do not recompute statistics:

```python
from plotsalot import analyze_gghistostats, render_gghistostats

analysis = analyze_gghistostats(data, "value", test_value=0.0)
plot = render_gghistostats(analysis, title="Observed values")
plot.axes["main"].grid(axis="y", alpha=0.2)
```

## Find the right documentation

| Need | Go to |
|---|---|
| Complete a first analysis | [Getting started](docs/GETTING_STARTED.md) |
| Choose a plot or analysis family | [User guide](docs/USER_GUIDE.md) |
| Interpret results and failure boundaries | [Interpretation and limitations](docs/INTERPRETATION_AND_LIMITATIONS.md) |
| Understand result and rendering contracts | [Contracts](docs/CONTRACTS.md) |
| Compare behavior with `ggstatsplot` | [Compatibility matrix](docs/compatibility.md) |
| Review statistical definitions | [Statistical methods index](docs/README.md#statistical-methods) |
| Reproduce tests, oracles, and benchmarks | [Reproducibility](REPRODUCIBILITY.md) |
| Contribute a change | [Contributing](CONTRIBUTING.md) |

## Supported workflow families

- one-sample histograms and labeled dot plots;
- scatter plots and correlation matrices;
- independent- and repeated-group comparisons;
- categorical bar and pie analyses;
- coefficient and aggregate meta-analysis plots;
- atomic grouped variants, plot composition, and local themes; and
- explicit classical, fixed-trim robust, and approved Bayesian modes where
  listed in the [compatibility matrix](docs/compatibility.md).

The implementation is adapted rather than a drop-in port. It uses explicit
column names, typed Python results, owned NumPy boundaries, and Matplotlib
rendering. Unsupported modes fail explicitly; grouped operations do not return
partial results.

## Development

```sh
make setup
make check
make audit
make build
```

The default quality gate runs formatting, linting, strict type checking, the test
suite, coverage enforcement, and documentation-link checks. Frozen R-oracle and
benchmark evidence are verified by the normal tests; regenerating them is an
explicit operation:

```sh
make oracle
make benchmark
```

See [the documentation index](docs/README.md) for project plans, decisions,
method specifications, and retained verification evidence.

## Project identity and license

Plotsalot is an independent project and is not endorsed by or affiliated with
the `ggstatsplot` maintainers. The upstream project is used as a pinned behavioral
reference under the adaptation rules recorded in the repository.

Plotsalot is MIT licensed. See [LICENSE](LICENSE) and
[ADR-010](docs/adr/ADR-010-license-posture.md) for the accepted distribution and
upstream-notice rules. Report security concerns according to
[SECURITY.md](SECURITY.md).
