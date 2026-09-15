"""Verify retained R-oracle fixtures against the Python analysis contract."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from importlib import import_module
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from plotsalot import (
    CategoricalResult,
    ComparisonResult,
    analyze_categorical,
    analyze_ggbetweenstats,
    analyze_ggcoefstats,
    analyze_ggcorrmat,
    analyze_ggdotplotstats,
    analyze_gghistostats,
    analyze_ggscatterstats,
    analyze_ggwithinstats,
    analyze_grouped_ggbarstats,
)
from plotsalot.categorical_result import (
    CategoricalEffectResult,
    CategoricalTestResult,
)

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
M3_INPUT_FIXTURES = ("m3-between", "m3-within")
M3_RAW_FIXTURES = ("m3-between-ggstatsplot.R", "m3-within-ggstatsplot.R")
M4_INPUT_FIXTURES = (
    "m4-one-way",
    "m4-independent",
    "m4-paired",
    "m4-raw",
    "m4-grouped",
)
M4_RAW_FIXTURES = tuple(
    f"{fixture}-{renderer}-ggstatsplot.R"
    for fixture in ("m4-one-way", "m4-independent", "m4-paired", "m4-raw", "m4-grouped")
    for renderer in ("bar", "pie")
)
M5B_INPUT_FIXTURES = ("m5b-meta",)
M5B_RAW_FIXTURES = ("m5b-meta-ggstatsplot.R",)
M6A_INPUT_FIXTURES = (
    "m6a-hist",
    "m6a-correlation",
    "m6a-between",
    "m6a-within",
)
M6A_RAW_FIXTURES = (
    "m6a-hist-ggstatsplot.R",
    "m6a-scatter-ggstatsplot.R",
    "m6a-between-ggstatsplot.R",
    "m6a-within-ggstatsplot.R",
)
M5A_INPUT_FIXTURES = ("m5a-coefficients", "m5a-ols")
M5A_RAW_FIXTURES = (
    "m5a-coefficients-ggstatsplot.R",
    "m5a-ols-ggstatsplot.R",
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


def _verify_pairwise_rows(
    rows: list[dict[str, str]],
    result: ComparisonResult,
    fixture: str,
) -> None:
    pairwise = result.pairwise
    expected_pairs = [row for row in rows if row["record"] == "pairwise"]
    if len(pairwise) != len(expected_pairs):
        raise AssertionError(f"{fixture}: pairwise family size differs")
    for actual, expected in zip(pairwise, expected_pairs, strict=True):
        if (actual.left, actual.right) != (expected["left"], expected["right"]):
            raise AssertionError(f"{fixture}: pairwise identity differs")
        for field, value in {
            "statistic": actual.test.statistic,
            "df2": actual.test.df2,
            "p_value": actual.test.p_value,
            "estimate": actual.estimate,
            "interval_low": actual.interval.low,
            "interval_high": actual.interval.high,
            "adjusted_p_value": actual.adjusted_p_value,
        }.items():
            _close(
                value,
                expected[field],
                f"{fixture}.{actual.left}.{actual.right}.{field}",
            )


def _verify_m3_results() -> None:
    for filename in M3_RAW_FIXTURES:
        path = OUTPUT / filename
        if not path.is_file() or path.stat().st_size == 0:
            raise AssertionError(f"missing raw ggstatsplot M3 result: {path}")

    between_raw = (OUTPUT / "m3-between-ggstatsplot.R").read_text()
    if "Games-Howell" not in between_raw:
        raise AssertionError("M3 between oracle lost the upstream pairwise adaptation")
    between_data = pl.read_csv(INPUT / "m3-between.csv")
    between_result = analyze_ggbetweenstats(between_data, "group", "value").result
    with (OUTPUT / "m3-between-results.csv").open(newline="") as handle:
        between_rows = list(csv.DictReader(handle))
    between_omnibus = next(row for row in between_rows if row["record"] == "omnibus")
    for field, value in {
        "statistic": between_result.omnibus.statistic,
        "df1": between_result.omnibus.df1,
        "df2": between_result.omnibus.df2,
        "p_value": between_result.omnibus.p_value,
    }.items():
        if value is None:
            raise AssertionError(f"m3-between.{field} is absent")
        _close(float(value), between_omnibus[field], f"m3-between.{field}")
    _verify_pairwise_rows(between_rows, between_result, "m3-between")

    within_data = pl.read_csv(INPUT / "m3-within.csv")
    within_result = analyze_ggwithinstats(
        within_data, "condition", "value", subject_id="subject"
    ).result
    with (OUTPUT / "m3-within-results.csv").open(newline="") as handle:
        within_rows = list(csv.DictReader(handle))
    within_omnibus = next(row for row in within_rows if row["record"] == "omnibus")
    correction = within_result.correction
    if correction is None:
        raise AssertionError("m3-within correction is absent")
    for field, value in {
        "statistic": within_result.omnibus.statistic,
        "df1": within_result.omnibus.df1,
        "df2": within_result.omnibus.df2,
        "p_value": within_result.omnibus.p_value,
        "epsilon": correction.epsilon,
        "uncorrected_p_value": correction.uncorrected_p_value,
    }.items():
        if value is None:
            raise AssertionError(f"m3-within.{field} is absent")
        _close(float(value), within_omnibus[field], f"m3-within.{field}")
    _verify_pairwise_rows(within_rows, within_result, "m3-within")


def _verify_categorical_values(
    test: CategoricalTestResult,
    effect: CategoricalEffectResult,
    adjusted_p_value: float | None,
    expected: dict[str, str],
    label: str,
) -> None:
    for field, value in {
        "statistic": test.statistic,
        "df": test.df,
        "p_value": test.p_value,
        "effect": effect.value,
    }.items():
        _close(float(value), expected[field], f"{label}.{field}")
    for field, value in {
        "interval_low": effect.interval.low,
        "interval_high": effect.interval.high,
    }.items():
        reference = float(expected[field])
        if not math.isclose(value, reference, rel_tol=1e-10, abs_tol=1e-12):
            raise AssertionError(
                f"{label}.{field}: Python={value:.17g}, R={reference:.17g}"
            )
    adjusted = expected["adjusted_p_value"]
    if adjusted != "NA":
        if adjusted_p_value is None:
            raise AssertionError(f"{label}.adjusted_p_value is absent")
        _close(
            adjusted_p_value,
            adjusted,
            f"{label}.adjusted_p_value",
        )


def _verify_m4_results() -> None:
    for filename in M4_RAW_FIXTURES:
        path = OUTPUT / filename
        if not path.is_file() or path.stat().st_size == 0:
            raise AssertionError(f"missing raw ggstatsplot M4 result: {path}")
    independent_raw = (OUTPUT / "m4-independent-bar-ggstatsplot.R").read_text()
    paired_raw = (OUTPUT / "m4-paired-bar-ggstatsplot.R").read_text()
    one_way_raw = (OUTPUT / "m4-one-way-bar-ggstatsplot.R").read_text()
    if "Fisher's exact test" not in independent_raw:
        raise AssertionError("M4 oracle lost the upstream pairwise adaptation")
    if "McNemar's Chi-squared test" not in paired_raw:
        raise AssertionError("M4 oracle lost the upstream paired adaptation")
    if "Pearson's C" not in one_way_raw:
        raise AssertionError("M4 oracle lost the upstream effect adaptation")

    with (OUTPUT / "m4-categorical-results.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))

    one_way = analyze_categorical(
        pl.read_csv(INPUT / "m4-one-way.csv"), "x", counts="n"
    ).result
    independent = analyze_categorical(
        pl.read_csv(INPUT / "m4-independent.csv"), "x", "y", counts="n"
    ).result
    paired = analyze_categorical(
        pl.read_csv(INPUT / "m4-paired.csv"),
        "x",
        "y",
        counts="n",
        paired=True,
        proportion_test=False,
    ).result
    results: dict[str, CategoricalResult] = {
        "m4-one-way": one_way,
        "m4-independent": independent,
        "m4-paired": paired,
    }
    raw = pl.read_csv(INPUT / "m4-raw.csv")
    raw_result = analyze_categorical(raw, "x", "y").result
    aggregate_result = analyze_categorical(
        pl.DataFrame(
            {
                "x": ["a", "a", "b", "b"],
                "y": ["u", "v", "u", "v"],
                "n": [10, 10, 10, 10],
            }
        ),
        "x",
        "y",
        counts="n",
    ).result
    if (
        raw_result.omnibus != aggregate_result.omnibus
        or raw_result.effect != aggregate_result.effect
        or raw_result.pairwise != aggregate_result.pairwise
        or raw_result.strata != aggregate_result.strata
    ):
        raise AssertionError("M4 raw and aggregate oracle inputs are not equivalent")
    grouped = analyze_grouped_ggbarstats(
        pl.read_csv(INPUT / "m4-grouped.csv"),
        "x",
        "group",
        "y",
        counts="n",
    )
    if len(grouped.groups) != 2:
        raise AssertionError("M4 grouped oracle fixture did not retain both groups")
    for fixture, result in results.items():
        expected = [row for row in rows if row["fixture"] == fixture]
        omnibus = next(row for row in expected if row["family"] == "omnibus")
        _verify_categorical_values(
            result.omnibus, result.effect, None, omnibus, f"{fixture}.omnibus"
        )
        pairwise_rows = [row for row in expected if row["family"] == "pairwise"]
        if len(pairwise_rows) != len(result.pairwise):
            raise AssertionError(f"{fixture}: pairwise family size differs")
        for actual, row in zip(result.pairwise, pairwise_rows, strict=True):
            if (str(actual.left), str(actual.right)) != (row["left"], row["right"]):
                raise AssertionError(f"{fixture}: pairwise identity differs")
            _verify_categorical_values(
                actual.test,
                actual.effect,
                actual.adjusted_p_value,
                row,
                f"{fixture}.pairwise.{actual.left}.{actual.right}",
            )
        stratum_rows = [row for row in expected if row["family"] == "stratum"]
        if len(stratum_rows) != len(result.strata):
            raise AssertionError(f"{fixture}: stratum family size differs")
        for actual, row in zip(result.strata, stratum_rows, strict=True):
            if str(actual.left) != row["left"]:
                raise AssertionError(f"{fixture}: stratum identity differs")
            _verify_categorical_values(
                actual.test,
                actual.effect,
                actual.adjusted_p_value,
                row,
                f"{fixture}.stratum.{actual.left}",
            )


def _close_m5b(actual: float, expected: str, label: str) -> None:
    reference = float(expected)
    if not math.isclose(actual, reference, rel_tol=1e-10, abs_tol=1e-12):
        raise AssertionError(f"{label}: Python={actual:.17g}, R={reference:.17g}")


def _verify_m5a_results() -> None:
    for filename in M5A_RAW_FIXTURES:
        path = OUTPUT / filename
        if not path.is_file() or path.stat().st_size == 0:
            raise AssertionError(f"missing raw ggstatsplot M5A result: {path}")

    reported = pl.read_csv(INPUT / "m5a-coefficients.csv")
    table_result = analyze_ggcoefstats(
        reported,
        estimate_label="regression coefficient",
        effect_scale="linear predictor",
        effect_direction="positive is higher",
        effect_units="outcome units",
    ).result
    if (
        table_result.inference_profile != "full_t"
        or table_result.source_kind != "table"
    ):
        raise AssertionError("M5A reported-table profile identity differs")
    for term, row in zip(
        table_result.terms, reported.iter_rows(named=True), strict=True
    ):
        inference = term.inference
        if inference is None or inference.interval is None:
            raise AssertionError("M5A reported table lost inference")
        if (
            term.identity.term != row["term"]
            or term.identity.response != row["response"]
        ):
            raise AssertionError("M5A reported table identity differs")
        for actual, field in (
            (term.estimate, "estimate"),
            (inference.standard_error, "standard_error"),
            (inference.statistic, "statistic"),
            (inference.df, "df"),
            (inference.p_value, "p_value"),
            (inference.interval.low, "conf_low"),
            (inference.interval.high, "conf_high"),
        ):
            if actual is None or not math.isclose(
                actual, float(row[field]), rel_tol=0, abs_tol=0
            ):
                raise AssertionError(f"M5A reported table field differs: {field}")

    ols_data = pl.read_csv(INPUT / "m5a-ols.csv")
    statsmodels = import_module("statsmodels.api")
    x = np.column_stack((np.ones(ols_data.height), ols_data.get_column("x").to_numpy()))
    fitted = statsmodels.OLS(ols_data.get_column("y").to_numpy(), x).fit()
    model_result = analyze_ggcoefstats(
        fitted,
        estimate_label="regression coefficient",
        effect_scale="linear predictor",
        effect_direction="positive is higher",
        effect_units="outcome units",
    ).result
    with (OUTPUT / "m5a-ols-results.csv").open(newline="") as handle:
        expected_terms = list(csv.DictReader(handle))
    for term, expected in zip(model_result.terms, expected_terms, strict=True):
        inference = term.inference
        if inference is None or inference.interval is None:
            raise AssertionError("M5A fitted OLS lost inference")
        if term.identity.term != expected["term"]:
            raise AssertionError("M5A fitted OLS term identity differs")
        for actual, field in (
            (term.estimate, "estimate"),
            (inference.standard_error, "standard_error"),
            (inference.statistic, "statistic"),
            (inference.df, "df"),
            (inference.p_value, "p_value"),
            (inference.interval.low, "interval_low"),
            (inference.interval.high, "interval_high"),
        ):
            if actual is None:
                raise AssertionError(f"M5A fitted OLS field missing: {field}")
            _close_m5b(actual, expected[field], f"m5a-ols.{term.identity.term}.{field}")
    with (OUTPUT / "m5a-ols-summary.csv").open(newline="") as handle:
        summary = next(csv.DictReader(handle))
    model = model_result.model_summary
    if model is None:
        raise AssertionError("M5A fitted OLS model summary is missing")
    for actual, field in (
        (model.nobs, "nobs"),
        (model.df_model, "df_model"),
        (model.df_resid, "df_resid"),
        (model.rank, "rank"),
    ):
        _close_m5b(float(actual), summary[field], f"m5a-ols.summary.{field}")


def _close_m5b_metafor(actual: float, expected: str, label: str) -> None:
    """Compare with metafor at the accuracy of its iterative tau estimator."""
    reference = float(expected)
    if not math.isclose(actual, reference, rel_tol=1e-6, abs_tol=1e-8):
        raise AssertionError(f"{label}: Python={actual:.17g}, R={reference:.17g}")


def _verify_m5b_results() -> None:
    for filename in M5B_RAW_FIXTURES:
        path = OUTPUT / filename
        if not path.is_file() or path.stat().st_size == 0:
            raise AssertionError(f"missing raw ggstatsplot M5B result: {path}")

    data = pl.read_csv(INPUT / "m5b-meta.csv")
    result = analyze_ggcoefstats(
        data,
        meta_analytic_effect=True,
        estimand="mean treatment effect",
        effect_scale="mean difference",
        effect_direction="positive favors treatment",
        effect_units="points",
    ).result
    with (OUTPUT / "m5b-meta-results.csv").open(newline="") as handle:
        expected = next(csv.DictReader(handle))
    meta = result.meta_analysis
    prediction = meta.prediction.interval
    if prediction is None:
        raise AssertionError("M5B oracle requires its five-study prediction interval")
    if result.retained_rows != int(expected["studies"]):
        raise AssertionError("M5B oracle study count differs")
    summary_values = {
        "tau_squared": meta.heterogeneity.tau_squared,
        "tau": meta.heterogeneity.tau,
        "pooled_estimate": meta.pooled.estimate,
        "conventional_variance": meta.pooled.conventional_variance,
        "q_hk": meta.pooled.q_hk,
        "q_star": meta.pooled.q_star,
        "adjusted_variance": meta.pooled.adjusted_variance,
        "pooled_standard_error": meta.pooled.standard_error,
        "pooled_statistic": meta.pooled.statistic,
        "pooled_df": float(meta.pooled.df),
        "pooled_p_value": meta.pooled.p_value,
        "pooled_interval_low": meta.pooled.interval.low,
        "pooled_interval_high": meta.pooled.interval.high,
        "prediction_interval_low": prediction.low,
        "prediction_interval_high": prediction.high,
        "q": meta.heterogeneity.q,
        "q_df": float(meta.heterogeneity.df),
        "q_p_value": meta.heterogeneity.p_value,
        "q_reference_mean": meta.heterogeneity.reference_mean,
        "i_squared": meta.heterogeneity.i_squared,
    }
    for field, actual in summary_values.items():
        _close_m5b(actual, expected[field], f"m5b-meta.{field}")
    for approved, field in (
        (meta.heterogeneity.tau_squared, "metafor_tau_squared"),
        (meta.pooled.estimate, "metafor_adhoc_estimate"),
        (meta.pooled.standard_error, "metafor_adhoc_standard_error"),
        (meta.pooled.statistic, "metafor_adhoc_statistic"),
        (float(meta.pooled.df), "metafor_adhoc_df"),
        (meta.pooled.p_value, "metafor_adhoc_p_value"),
        (meta.pooled.interval.low, "metafor_adhoc_interval_low"),
        (meta.pooled.interval.high, "metafor_adhoc_interval_high"),
    ):
        _close_m5b_metafor(approved, expected[field], f"m5b-meta.{field}")

    upstream_se = float(expected["upstream_standard_error"])
    if math.isclose(
        meta.pooled.standard_error, upstream_se, rel_tol=1e-10, abs_tol=1e-12
    ):
        raise AssertionError("M5B oracle lost the upstream normal/HK adaptation")
    if expected["upstream_test"] != "z":
        raise AssertionError("M5B upstream reference no longer uses normal inference")

    with (OUTPUT / "m5b-meta-study-results.csv").open(newline="") as handle:
        study_rows = list(csv.DictReader(handle))
    if len(study_rows) != len(result.terms):
        raise AssertionError("M5B oracle study family size differs")
    for term, row in zip(result.terms, study_rows, strict=True):
        if term.term != row["term"]:
            raise AssertionError("M5B oracle study identity differs")
        for field, actual in {
            "estimate": term.estimate,
            "standard_error": term.inference.standard_error,
            "statistic": term.inference.statistic,
            "p_value": term.inference.p_value,
            "interval_low": term.inference.interval.low,
            "interval_high": term.inference.interval.high,
            "sampling_variance": term.sampling_variance,
            "random_effects_weight": term.random_effects_weight,
            "normalized_weight": term.normalized_weight,
            "weighted_contribution": term.weighted_contribution,
        }.items():
            _close_m5b(actual, row[field], f"m5b-meta.{term.term}.{field}")


def _close_m6a(actual: float, expected: str, label: str) -> None:
    reference = float(expected)
    if not math.isclose(actual, reference, rel_tol=1e-10, abs_tol=1e-12):
        raise AssertionError(f"{label}: Python={actual:.17g}, R={reference:.17g}")


def _verify_m6a_results() -> None:
    """Verify approved M6A formulas against independent base-R calculations."""

    for filename in M6A_RAW_FIXTURES:
        path = OUTPUT / filename
        if not path.is_file() or path.stat().st_size == 0:
            raise AssertionError(f"missing raw ggstatsplot M6A result: {path}")

    hist_data = pl.read_csv(INPUT / "m6a-hist.csv")
    hist = analyze_gghistostats(
        hist_data,
        "value",
        type="robust",
        test_value=3.0,
    ).result
    with (OUTPUT / "m6a-hist-results.csv").open(newline="") as handle:
        hist_reference = next(csv.DictReader(handle))
    hist_integer = {
        "n": hist.estimate.kernel.n,
        "g": hist.estimate.kernel.g,
        "h": hist.estimate.kernel.h,
    }
    for field, actual in hist_integer.items():
        if actual != int(hist_reference[field]):
            raise AssertionError(f"m6a-hist.{field} differs from base R")
    for field, actual in {
        "lower_bound": hist.estimate.kernel.lower_bound,
        "upper_bound": hist.estimate.kernel.upper_bound,
        "trimmed_mean": hist.estimate.value,
        "winsorized_variance": hist.estimate.kernel.winsorized_variance,
        "q": hist.estimate.kernel.q,
        "statistic": hist.test.statistic,
        "df": hist.test.df,
        "p_value": hist.test.p_value,
        "interval_low": hist.interval.low,
        "interval_high": hist.interval.high,
        "raw_effect": hist.effect_size.value,
    }.items():
        if actual is None:
            raise AssertionError(f"m6a-hist.{field} is absent")
        _close_m6a(float(actual), hist_reference[field], f"m6a-hist.{field}")

    correlation_data = pl.read_csv(INPUT / "m6a-correlation.csv")
    correlation = analyze_ggscatterstats(
        correlation_data,
        "x",
        "y",
        type="robust",
        random_seed=2026,
        bootstrap_resamples=999,
    ).result
    with (OUTPUT / "m6a-correlation-results.csv").open(newline="") as handle:
        correlation_reference = next(csv.DictReader(handle))
    for field, actual in {
        "n": correlation.x_kernel.n,
        "g": correlation.x_kernel.g,
        "h": correlation.x_kernel.h,
    }.items():
        if actual != int(correlation_reference[field]):
            raise AssertionError(f"m6a-correlation.{field} differs from base R")
    for field, actual in {
        "x_lower_bound": correlation.x_kernel.lower_bound,
        "x_upper_bound": correlation.x_kernel.upper_bound,
        "y_lower_bound": correlation.y_kernel.lower_bound,
        "y_upper_bound": correlation.y_kernel.upper_bound,
        "x_winsorized_variance": correlation.x_kernel.winsorized_variance,
        "y_winsorized_variance": correlation.y_kernel.winsorized_variance,
        "winsorized_covariance": correlation.winsorized_covariance,
        "estimate": correlation.estimate,
        "statistic": correlation.test.statistic,
        "df": correlation.test.df,
        "p_value": correlation.test.p_value,
    }.items():
        if actual is None:
            raise AssertionError(f"m6a-correlation.{field} is absent")
        _close_m6a(
            float(actual),
            correlation_reference[field],
            f"m6a-correlation.{field}",
        )
    if correlation.test.df != correlation.x_kernel.h - 2:
        raise AssertionError("M6A correlation lost its approved WRS2-style df")

    between_data = pl.read_csv(INPUT / "m6a-between.csv")
    between = analyze_ggbetweenstats(
        between_data,
        "group",
        "value",
        type="robust",
        pairwise_display="all",
    ).result
    with (OUTPUT / "m6a-between-results.csv").open(newline="") as handle:
        between_reference = list(csv.DictReader(handle))
    omnibus_reference = next(
        row for row in between_reference if row["record"] == "omnibus"
    )
    for field, actual in {
        "statistic": between.omnibus.statistic,
        "df": between.omnibus.df2,
        "p_value": between.omnibus.p_value,
    }.items():
        if actual is None:
            raise AssertionError(f"m6a-between.{field} is absent")
        _close_m6a(float(actual), omnibus_reference[field], f"m6a-between.{field}")
    between_pairs = {
        (str(item.left), str(item.right)): item for item in between.pairwise
    }
    for row in (item for item in between_reference if item["record"] == "pairwise"):
        identity = (row["left"], row["right"])
        pair = between_pairs[identity]
        for field, actual in {
            "estimate": pair.estimate,
            "standard_error": pair.standard_error,
            "statistic": pair.test.statistic,
            "df": pair.test.df,
            "p_value": pair.test.p_value,
            "interval_low": pair.interval.low,
            "interval_high": pair.interval.high,
            "adjusted_p_value": pair.adjusted_p_value,
        }.items():
            if actual is None:
                raise AssertionError(f"m6a-between.{identity}.{field} is absent")
            _close_m6a(float(actual), row[field], f"m6a-between.{identity}.{field}")

    within_data = pl.read_csv(INPUT / "m6a-within.csv")
    within = analyze_ggwithinstats(
        within_data,
        "condition",
        "value",
        subject_id="subject",
        type="robust",
        pairwise_display="all",
    ).result
    with (OUTPUT / "m6a-within-results.csv").open(newline="") as handle:
        within_reference = list(csv.DictReader(handle))
    within_omnibus = next(row for row in within_reference if row["record"] == "omnibus")
    if within.correction is None:
        raise AssertionError("m6a-within correction is absent")
    for field, actual in {
        "statistic": within.omnibus.statistic,
        "df1": within.omnibus.df1,
        "df2": within.omnibus.df2,
        "p_value": within.omnibus.p_value,
        "epsilon": within.correction.epsilon,
        "epsilon_hat": within.correction.epsilon_hat,
        "epsilon_raw": within.correction.epsilon_raw,
        "covariance_a": within.correction.covariance_a,
        "covariance_b": within.correction.covariance_b,
        "qc": within.correction.qc,
        "qe": within.correction.qe,
    }.items():
        if actual is None:
            raise AssertionError(f"m6a-within.{field} is absent")
        _close_m6a(float(actual), within_omnibus[field], f"m6a-within.{field}")
    within_pairs = {(str(item.left), str(item.right)): item for item in within.pairwise}
    for row in (item for item in within_reference if item["record"] == "pairwise"):
        identity = (row["left"], row["right"])
        pair = within_pairs[identity]
        for field, actual in {
            "estimate": pair.estimate,
            "standard_error": pair.standard_error,
            "statistic": pair.test.statistic,
            "df2": pair.test.df,
            "p_value": pair.test.p_value,
            "interval_low": pair.interval.low,
            "interval_high": pair.interval.high,
            "adjusted_p_value": pair.adjusted_p_value,
        }.items():
            if actual is None:
                raise AssertionError(f"m6a-within.{identity}.{field} is absent")
            _close_m6a(float(actual), row[field], f"m6a-within.{identity}.{field}")


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
        "m3_input_fixtures": list(M3_INPUT_FIXTURES),
        "m3_raw_fixtures": list(M3_RAW_FIXTURES),
        "m4_input_fixtures": list(M4_INPUT_FIXTURES),
        "m4_raw_fixtures": list(M4_RAW_FIXTURES),
        "m5a_input_fixtures": list(M5A_INPUT_FIXTURES),
        "m5a_raw_fixtures": list(M5A_RAW_FIXTURES),
        "m5b_input_fixtures": list(M5B_INPUT_FIXTURES),
        "m5b_raw_fixtures": list(M5B_RAW_FIXTURES),
        "m6a_input_fixtures": list(M6A_INPUT_FIXTURES),
        "m6a_raw_fixtures": list(M6A_RAW_FIXTURES),
        "sha256": _hashes(),
    }


def verify_oracle() -> None:
    """Verify semantic parity and all retained oracle artifact hashes."""

    _verify_results()
    _verify_m2_results()
    _verify_m3_results()
    _verify_m4_results()
    _verify_m5a_results()
    _verify_m5b_results()
    _verify_m6a_results()
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
        _verify_m3_results()
        _verify_m4_results()
        _verify_m5a_results()
        _verify_m5b_results()
        _verify_m6a_results()
        payload = _manifest_payload()
        MANIFEST.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    else:
        verify_oracle()
    print("oracle fixtures verified")


if __name__ == "__main__":
    main()
