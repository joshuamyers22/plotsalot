"""Exercise the installed public package without importing the source tree."""

# ruff: noqa: E402

from __future__ import annotations

import argparse
import json
from importlib.metadata import distribution, entry_points, version
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import polars as pl

import plotsalot
from plotsalot import (
    BayesianOneSampleResult,
    RobustOneSampleResult,
    combine_plots,
    gghistostats,
    grouped_gghistostats,
)

EXPECTED_SCRIPTS = {
    "plotsalot",
    "plotsalot-dataset",
    "plotsalot-regression",
    "plotsalot-validate",
}


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description=__doc__)
    command.add_argument("--expected-version", required=True)
    return command


def main() -> int:
    args = parser().parse_args()
    installed_version = version("plotsalot")
    if installed_version != args.expected_version:
        raise ValueError(
            f"installed version {installed_version!r} != {args.expected_version!r}"
        )
    package_root = Path(plotsalot.__file__).resolve().parent
    if "site-packages" not in package_root.parts:
        raise ValueError(
            f"plotsalot was not imported from an installed environment: {package_root}"
        )
    if len(plotsalot.__all__) != 144:
        raise ValueError("installed root export count does not match the 1.0 contract")
    for public_name in plotsalot.__all__:
        getattr(plotsalot, public_name)

    scripts = {
        entry.name
        for entry in entry_points(group="console_scripts")
        if entry.dist is not None and entry.dist.name == "plotsalot"
    }
    if scripts != EXPECTED_SCRIPTS:
        raise ValueError(f"installed console scripts differ: {sorted(scripts)}")
    metadata = distribution("plotsalot").metadata
    if (
        metadata["Requires-Python"] != ">=3.11"
        or metadata["License-Expression"] != "MIT"
    ):
        raise ValueError("installed metadata differs from the 1.0 release contract")

    data = pl.DataFrame(
        {
            "value": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            "cohort": ["a"] * 5 + ["b"] * 5,
        }
    )
    classical = gghistostats(data, "value", test_value=0.0, title="classical")
    robust = gghistostats(data, "value", type="robust", title="robust")
    bayesian = gghistostats(
        data,
        "value",
        type="bayes",
        prior_scale=2.0,
        title="bayesian",
    )
    if not isinstance(robust.result, RobustOneSampleResult):
        raise TypeError("robust installed smoke returned the wrong result type")
    if not isinstance(bayesian.result, BayesianOneSampleResult):
        raise TypeError("Bayesian installed smoke returned the wrong result type")
    grouped = grouped_gghistostats(data, "value", "cohort")
    composed = combine_plots([classical, robust, bayesian, grouped], columns=2)
    payloads = [
        classical.result.to_dict(),
        robust.result.to_dict(),
        bayesian.result.to_dict(),
        grouped.result.to_dict(),
        composed.result.to_dict(),
    ]
    json.dumps(payloads, allow_nan=False)
    if len(composed.result.panels) != 5:
        raise ValueError("installed composition did not retain every source result")
    for figure in (
        classical.figure,
        robust.figure,
        bayesian.figure,
        *(plot.figure for plot in grouped.plots),
        composed.figure,
    ):
        figure.canvas.draw()
        figure.clear()
    print(
        f"plotsalot {installed_version} installed smoke passed from {package_root} "
        f"with {len(plotsalot.__all__)} exports"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
