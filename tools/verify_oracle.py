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

from plotsalot import analyze_ggcorrmat, analyze_ggdotplotstats, analyze_gghistostats

ROOT = Path(__file__).resolve().parents[1]
ORACLE = ROOT / "oracle"
INPUT = ORACLE / "fixtures" / "input"
OUTPUT = ORACLE / "fixtures" / "r-output"
MANIFEST = ORACLE / "fixtures" / "manifest.json"
NORMAL_FIXTURES = ("normal", "null-containing", "small-sample")
BOUNDARY_FIXTURES = ("non-finite", "degenerate")
M2_INPUT_FIXTURES = ("m2-dot", "m2-correlation")
M2_RAW_FIXTURES = (
    "m2-dot-ggstatsplot.R",
    "m2-scatter-ggstatsplot.R",
    "m2-corrmat-ggstatsplot.R",
)
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


def _close(actual: float, expected: str, label: str) -> None:
    reference = float(expected)
    if not math.isclose(actual, reference, rel_tol=1e-12, abs_tol=1e-12):
        raise AssertionError(f"{label}: Python={actual:.17g}, R={reference:.17g}")


def _verify_m2_results() -> None:
    for filename in M2_RAW_FIXTURES:
        path = OUTPUT / filename
        if not path.is_file() or path.stat().st_size == 0:
            raise AssertionError(f"missing raw ggstatsplot M2 result: {path}")

    dot_data = pl.read_csv(INPUT / "m2-dot.csv", null_values="NA")
    dot_result = analyze_ggdotplotstats(dot_data, "value", "label").result
    with (OUTPUT / "m2-dot-results.csv").open(newline="") as handle:
        dot_rows = list(csv.DictReader(handle))
    overall = next(row for row in dot_rows if row["record"] == "overall")
    dot_integer_fields = {
        "input_rows": dot_result.sample.input_rows,
        "analyzed_rows": dot_result.sample.analyzed_rows,
        "dropped_null_rows": dot_result.sample.dropped_null_rows,
    }
    for field, actual in dot_integer_fields.items():
        if actual != int(overall[field]):
            raise AssertionError(
                f"m2-dot.overall.{field}: Python={actual}, R={overall[field]}"
            )
    one_sample = dot_result.one_sample
    for field, actual in {
        "mean": one_sample.estimate.value,
        "standard_deviation": one_sample.estimate.standard_deviation,
        "statistic": one_sample.test.statistic,
        "df": one_sample.test.df,
        "p_value": one_sample.test.p_value,
        "interval_low": one_sample.interval.low,
        "interval_high": one_sample.interval.high,
    }.items():
        _close(actual, overall[field], f"m2-dot.overall.{field}")

    labels = {estimate.label: estimate for estimate in dot_result.estimates}
    expected_labels = {
        row["label"]: row for row in dot_rows if row["record"] == "label"
    }
    if set(labels) != set(expected_labels):
        raise AssertionError("m2-dot label identities differ")
    for label, estimate in labels.items():
        expected = expected_labels[label]
        if estimate.interval is None or estimate.standard_deviation is None:
            raise AssertionError(f"m2-dot.{label}: expected an interval")
        for field, actual in {
            "mean": estimate.value,
            "standard_deviation": estimate.standard_deviation,
            "interval_low": estimate.interval.low,
            "interval_high": estimate.interval.high,
        }.items():
            _close(actual, expected[field], f"m2-dot.{label}.{field}")

    correlation_data = pl.read_csv(INPUT / "m2-correlation.csv", null_values="NA")
    matrix_result = analyze_ggcorrmat(
        correlation_data, ("x", "y", "z"), p_adjust="holm"
    ).result
    cells = {(cell.x, cell.y): cell for cell in matrix_result.cells}
    with (OUTPUT / "m2-correlation-results.csv").open(newline="") as handle:
        correlation_rows = list(csv.DictReader(handle))
    for expected in correlation_rows:
        identity = (expected["x"], expected["y"])
        cell = cells[identity]
        if cell.n_obs != int(expected["n_obs"]):
            raise AssertionError(
                f"m2-correlation.{identity}.n_obs: "
                f"Python={cell.n_obs}, R={expected['n_obs']}"
            )
        numeric = {
            "estimate": cell.estimate,
            "df": cell.df,
            "p_value": cell.p_value,
            "interval_low": None if cell.interval is None else cell.interval.low,
            "interval_high": None if cell.interval is None else cell.interval.high,
            "adjusted_p_value": cell.adjusted_p_value,
        }
        if abs(cell.estimate) < 1.0:
            numeric["statistic"] = cell.statistic
        elif cell.statistic is not None:
            raise AssertionError(
                f"m2-correlation.{identity}: perfect result has a statistic"
            )
        for field, actual in numeric.items():
            if actual is None:
                raise AssertionError(f"m2-correlation.{identity}.{field} is absent")
            _close(float(actual), expected[field], f"m2-correlation.{identity}.{field}")


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
        "m2_input_fixtures": list(M2_INPUT_FIXTURES),
        "m2_raw_fixtures": list(M2_RAW_FIXTURES),
        "sha256": _hashes(),
    }


def verify_oracle() -> None:
    """Verify semantic parity and all retained oracle artifact hashes."""

    _verify_results()
    _verify_m2_results()
    retained = json.loads(MANIFEST.read_text())
    if retained != _manifest_payload():
        raise AssertionError("oracle artifact hashes differ from manifest")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()
    if args.write_manifest:
        _verify_results()
        _verify_m2_results()
        payload = _manifest_payload()
        MANIFEST.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    else:
        verify_oracle()
    print("oracle fixtures verified")


if __name__ == "__main__":
    main()
