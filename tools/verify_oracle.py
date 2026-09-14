"""Verify retained R-oracle fixtures against the Python analysis contract."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import polars as pl

from plotsalot import analyze_gghistostats

ROOT = Path(__file__).resolve().parents[1]
ORACLE = ROOT / "oracle"
INPUT = ORACLE / "fixtures" / "input"
OUTPUT = ORACLE / "fixtures" / "r-output"
MANIFEST = ORACLE / "fixtures" / "manifest.json"
NORMAL_FIXTURES = ("normal", "null-containing", "small-sample")
BOUNDARY_FIXTURES = ("non-finite", "degenerate")
FLOAT_FIELDS = {
    "test_value": lambda result: result.test.null_value,
    "conf_level": lambda result: result.interval.level,
    "mean": lambda result: result.estimate.value,
    "standard_deviation": lambda result: result.estimate.standard_deviation,
    "statistic": lambda result: result.test.statistic,
    "df": lambda result: result.test.df,
    "p_value": lambda result: result.test.p_value,
    "interval_low": lambda result: result.interval.low,
    "interval_high": lambda result: result.interval.high,
    "cohen_d": lambda result: result.effect_size.value,
}


def _read_inputs(name: str) -> tuple[pl.DataFrame, float, float]:
    with (INPUT / f"{name}.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    values = [None if row["value"] == "NA" else float(row["value"]) for row in rows]
    return (
        pl.DataFrame({"value": values}),
        float(rows[0]["test_value"]),
        float(rows[0]["conf_level"]),
    )


def _verify_results() -> None:
    normalized_path = OUTPUT / "normalized-results.csv"
    with normalized_path.open(newline="") as handle:
        expected_by_name = {row["fixture"]: row for row in csv.DictReader(handle)}

    if set(expected_by_name) != set(NORMAL_FIXTURES):
        raise AssertionError("normalized oracle fixture identities do not match")

    for name in NORMAL_FIXTURES:
        raw_path = OUTPUT / f"{name}-ggstatsplot.R"
        if raw_path.stat().st_size == 0:
            raise AssertionError(f"empty raw ggstatsplot result: {raw_path}")
        data, test_value, conf_level = _read_inputs(name)
        result = analyze_gghistostats(
            data,
            "value",
            test_value=test_value,
            conf_level=conf_level,
        ).result
        expected = expected_by_name[name]
        if expected["upstream_effect_name"] != "Hedges' g":
            raise AssertionError(f"{name}: unexpected upstream effect-size method")
        if expected["upstream_effect_interval_method"] != "ncp":
            raise AssertionError(f"{name}: unexpected upstream effect-size interval")
        for field in (
            "upstream_effect_estimate",
            "upstream_effect_interval_low",
            "upstream_effect_interval_high",
        ):
            if not math.isfinite(float(expected[field])):
                raise AssertionError(f"{name}.{field}: expected a finite value")
        integer_fields = {
            "input_rows": result.sample.input_rows,
            "analyzed_rows": result.sample.analyzed_rows,
            "dropped_null_rows": result.sample.dropped_null_rows,
        }
        for field, actual in integer_fields.items():
            if actual != int(expected[field]):
                raise AssertionError(
                    f"{name}.{field}: Python={actual}, R={expected[field]}"
                )
        for field, accessor in FLOAT_FIELDS.items():
            actual = accessor(result)
            reference = float(expected[field])
            if not math.isclose(actual, reference, rel_tol=1e-12, abs_tol=1e-12):
                raise AssertionError(
                    f"{name}.{field}: Python={actual:.17g}, R={reference:.17g}"
                )

    with (OUTPUT / "boundary-results.csv").open(newline="") as handle:
        boundary_rows = {row["fixture"]: row for row in csv.DictReader(handle)}
    if set(boundary_rows) != set(BOUNDARY_FIXTURES):
        raise AssertionError("boundary oracle fixture identities do not match")

    for name in BOUNDARY_FIXTURES:
        if boundary_rows[name]["status"] != "accepted":
            raise AssertionError(f"upstream boundary behavior drifted for {name}")
        data, test_value, conf_level = _read_inputs(name)
        try:
            analyze_gghistostats(
                data,
                "value",
                test_value=test_value,
                conf_level=conf_level,
            )
        except ValueError:
            continue
        raise AssertionError(f"Python unexpectedly accepted boundary fixture {name}")


def _artifact_paths() -> list[Path]:
    paths = [ORACLE / "Dockerfile", ORACLE / "DESCRIPTION", ORACLE / "generate.R"]
    paths.extend(sorted(INPUT.glob("*.csv")))
    paths.extend(sorted(OUTPUT.glob("*")))
    lockfile = ORACLE / "renv.lock"
    if lockfile.exists():
        paths.append(lockfile)
    return [path for path in paths if path.is_file()]


def _hashes() -> dict[str, str]:
    return {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in _artifact_paths()
    }


def _manifest_payload() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "ggstatsplot_revision": "7a724cd0ab55668b9d0b2e84b12c711c5be68ac8",
        "normal_fixtures": list(NORMAL_FIXTURES),
        "boundary_fixtures": list(BOUNDARY_FIXTURES),
        "sha256": _hashes(),
    }


def verify_oracle() -> None:
    """Verify semantic parity and all retained oracle artifact hashes."""

    _verify_results()
    retained = json.loads(MANIFEST.read_text())
    if retained != _manifest_payload():
        raise AssertionError("oracle artifact hashes differ from manifest")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()
    if args.write_manifest:
        _verify_results()
        payload = _manifest_payload()
        MANIFEST.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    else:
        verify_oracle()
    print("oracle fixtures verified")


if __name__ == "__main__":
    main()
