#!/usr/bin/env python3
"""Generate the retained M7C serialized-result corpus from public workflows."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path
from typing import Any

import polars as pl

from plotsalot import (
    analyze_categorical,
    analyze_ggbetweenstats,
    analyze_ggcoefstats,
    analyze_ggcorrmat,
    analyze_ggdotplotstats,
    analyze_gghistostats,
    analyze_ggscatterstats,
    analyze_ggwithinstats,
    analyze_grouped_ggbarstats,
    analyze_grouped_ggbetweenstats,
    analyze_grouped_ggcorrmat,
    analyze_grouped_ggdotplotstats,
    analyze_grouped_gghistostats,
    analyze_grouped_ggscatterstats,
    analyze_grouped_ggwithinstats,
    combine_plots,
    gghistostats,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "m7" / "golden-results.json"


@dataclass(frozen=True)
class _Golden:
    identifier: str
    schema: str
    result: Any


def _association_frame(*, grouped: bool = False) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for outer_index, outer in enumerate(("first", "second") if grouped else ("all",)):
        for index in range(10):
            x = float(index + 1)
            rows.append(
                {
                    "outer": outer,
                    "x": x,
                    "y": 0.7 * x + float((index % 3) - 1) + outer_index * 0.2,
                    "z": 11.0 - x + float(index % 2) * 0.3,
                }
            )
    return pl.DataFrame(rows)


def _dot_frame(*, grouped: bool = False) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for outer_index, outer in enumerate(("first", "second") if grouped else ("all",)):
        for label_index, label in enumerate(("low", "high")):
            for index in range(6):
                rows.append(
                    {
                        "outer": outer,
                        "label": label,
                        "value": float(index + 1 + label_index * 2) + outer_index * 0.1,
                    }
                )
    return pl.DataFrame(rows)


def _between_frame(*, grouped: bool = False) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for outer_index, outer in enumerate(("first", "second") if grouped else ("all",)):
        for group_index, group in enumerate(("a", "b", "c")):
            for index in range(6):
                rows.append(
                    {
                        "outer": outer,
                        "group": group,
                        "value": float(index + group_index * 1.5)
                        + float(index % 2) * 0.2
                        + outer_index * 0.1,
                    }
                )
    return pl.DataFrame(rows)


def _within_frame(*, grouped: bool = False) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for outer_index, outer in enumerate(("first", "second") if grouped else ("all",)):
        for subject in range(8):
            for condition_index, condition in enumerate(("a", "b", "c")):
                rows.append(
                    {
                        "outer": outer,
                        "subject": subject + outer_index * 100,
                        "condition": condition,
                        "value": float(subject + condition_index)
                        + float((subject % 3) * condition_index) * 0.2,
                    }
                )
    return pl.DataFrame(rows)


def _categorical_frame(*, grouped: bool = False) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for outer_index, outer in enumerate(("first", "second") if grouped else ("all",)):
        for group_index, group in enumerate(("a", "b")):
            for answer_index, answer in enumerate(("yes", "no")):
                rows.append(
                    {
                        "outer": outer,
                        "group": group,
                        "answer": answer,
                        "count": 5 + outer_index + group_index * 2 + answer_index,
                    }
                )
    return pl.DataFrame(rows)


def _coefficient_table() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "term": ["constant", "dose", "age"],
            "estimate": [1.0, 0.5, -0.25],
            "conf_low": [0.5, 0.1, -0.6],
            "conf_high": [1.5, 0.9, 0.1],
            "standard_error": [0.25, 0.2, 0.18],
            "statistic_kind": ["z", "z", "z"],
            "statistic": [4.0, 2.5, -1.39],
            "p_value": [0.0001, 0.012, 0.164],
            "is_intercept": [True, False, False],
        }
    )


def _robust_coefficient_table() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "term": ["constant", "dose", "age"],
            "estimate": [1.0, 0.5, -0.25],
            "conf_low": [0.4, 0.1, -0.7],
            "conf_high": [1.6, 0.9, 0.2],
            "is_intercept": [True, False, False],
        }
    )


def _posterior_coefficient_table() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "term": ["constant", "dose", "age"],
            "posterior_median": [1.0, 0.5, -0.25],
            "credible_low": [0.4, 0.1, -0.7],
            "credible_high": [1.6, 0.9, 0.2],
            "probability_above_null": [0.99, 0.98, 0.2],
            "probability_below_null": [0.01, 0.02, 0.8],
            "probability_at_null": [0.0, 0.0, 0.0],
            "is_intercept": [True, False, False],
        }
    )


def _meta_frame(count: int) -> pl.DataFrame:
    estimates = [0.1, 0.3, 0.2, 0.5, 0.4, 0.0, 0.6, 0.35, 0.25, 3.0]
    errors = [0.2, 0.25, 0.2, 0.3, 0.22, 0.18, 0.28, 0.2, 0.24, 0.3]
    return pl.DataFrame(
        {
            "term": [f"study-{index + 1}" for index in range(count)],
            "estimate": estimates[:count],
            "standard_error": errors[:count],
        }
    )


def _declarations() -> dict[str, object]:
    return {
        "estimate_label": "coefficient",
        "effect_scale": "additive",
        "effect_direction": "positive is higher",
        "effect_units": "points",
    }


def _meta_declarations() -> dict[str, object]:
    return {
        "meta_analytic_effect": True,
        "estimand": "population treatment effect",
        "effect_scale": "mean difference",
        "effect_direction": "positive favors treatment",
        "effect_units": "points",
    }


def _direct_results() -> list[_Golden]:
    records: list[_Golden] = []

    histogram = analyze_gghistostats(
        pl.DataFrame({"value": [1.0, 2.0, 3.0, 4.0, 5.0]}), "value"
    ).result
    dot = analyze_ggdotplotstats(_dot_frame(), "value", "label").result
    records.extend(
        (
            _Golden("analysis-histogram-v1", "analysis-result.schema.json", histogram),
            _Golden(
                "analysis-dot-one-sample-v1",
                "analysis-result.schema.json",
                dot.one_sample,
            ),
            _Golden("dotplot-v1", "dotplot-result.schema.json", dot),
        )
    )

    robust_histogram = analyze_gghistostats(
        _association_frame(), "x", type="robust"
    ).result
    robust_dot = analyze_ggdotplotstats(
        _dot_frame(), "value", "label", type="robust"
    ).result
    bayesian_histogram = analyze_gghistostats(
        pl.DataFrame({"value": [1.0, 2.0, 3.0, 4.0, 5.0]}),
        "value",
        type="bayes",
        prior_scale=2.0,
    ).result
    bayesian_dot = analyze_ggdotplotstats(
        _dot_frame(), "value", "label", type="bayes", prior_scale=2.0
    ).result
    records.extend(
        (
            _Golden(
                "robust-histogram-v2", "robust-result.schema.json", robust_histogram
            ),
            _Golden(
                "robust-dot-one-sample-v2",
                "robust-result.schema.json",
                robust_dot.one_sample,
            ),
            _Golden("robust-dotplot-v2", "robust-result.schema.json", robust_dot),
            _Golden(
                "bayesian-histogram-v3",
                "bayesian-result.schema.json",
                bayesian_histogram,
            ),
            _Golden(
                "bayesian-dot-one-sample-v3",
                "bayesian-result.schema.json",
                bayesian_dot.one_sample,
            ),
            _Golden("bayesian-dotplot-v3", "bayesian-result.schema.json", bayesian_dot),
        )
    )

    for mode in ("parametric", "robust", "bayes"):
        options: dict[str, object] = {"type": mode}
        if mode == "robust":
            options.update(random_seed=17, bootstrap_resamples=999)
        scatter = analyze_ggscatterstats(
            _association_frame(), "x", "y", **options
        ).result
        matrix = analyze_ggcorrmat(
            _association_frame(), ("x", "y", "z"), p_adjust="none", **options
        ).result
        schema = {
            "parametric": (
                "correlation-result.schema.json",
                "correlation-matrix-result.schema.json",
            ),
            "robust": ("robust-result.schema.json", "robust-result.schema.json"),
            "bayes": ("bayesian-result.schema.json", "bayesian-result.schema.json"),
        }[mode]
        records.extend(
            (
                _Golden(f"{mode}-correlation", schema[0], scatter),
                _Golden(f"{mode}-correlation-matrix", schema[1], matrix),
            )
        )

    for mode in ("parametric", "robust", "bayes"):
        options = {"type": mode}
        if mode == "bayes":
            options.update(
                p_adjust="none",
                pairwise_display="all",
                prior_location=0.0,
                prior_scale=2.0,
                random_seed=23,
            )
        between = analyze_ggbetweenstats(
            _between_frame(), "group", "value", **options
        ).result
        within = analyze_ggwithinstats(
            _within_frame(),
            "condition",
            "value",
            subject_id="subject",
            **options,
        ).result
        schema = {
            "parametric": "comparison-result.schema.json",
            "robust": "robust-result.schema.json",
            "bayes": "bayesian-result.schema.json",
        }[mode]
        records.extend(
            (
                _Golden(f"{mode}-between", schema, between),
                _Golden(f"{mode}-within", schema, within),
            )
        )

    categorical = _categorical_frame()
    records.append(
        _Golden(
            "categorical-classical-v1",
            "categorical-result.schema.json",
            analyze_categorical(categorical, "group", "answer", counts="count").result,
        )
    )
    records.extend(
        (
            _Golden(
                "categorical-bayesian-fixed-total-v3",
                "bayesian-result.schema.json",
                analyze_categorical(
                    categorical.group_by("answer", maintain_order=True).agg(
                        pl.col("count").sum()
                    ),
                    "answer",
                    counts="count",
                    type="bayes",
                    p_adjust="none",
                    pairwise_display="all",
                ).result,
            ),
            _Golden(
                "categorical-bayesian-fixed-rows-v3",
                "bayesian-result.schema.json",
                analyze_categorical(
                    categorical,
                    "group",
                    "answer",
                    counts="count",
                    type="bayes",
                    p_adjust="none",
                    pairwise_display="all",
                    random_seed=29,
                ).result,
            ),
        )
    )

    coefficient = analyze_ggcoefstats(_coefficient_table(), **_declarations()).result
    robust_coefficient = analyze_ggcoefstats(
        _robust_coefficient_table(),
        type="robust",
        robust_method="Huber M-estimator",
        robust_tuning="c=1.345",
        interval_method="sandwich Wald",
        **_declarations(),
    ).result
    posterior_coefficient = analyze_ggcoefstats(
        _posterior_coefficient_table(),
        type="bayes",
        posterior_model="normal linear model",
        likelihood="Gaussian likelihood",
        prior_description="proper weakly informative normal priors",
        computation_method="deterministic quadrature",
        **_declarations(),
    ).result
    meta = analyze_ggcoefstats(_meta_frame(5), **_meta_declarations()).result
    robust_meta = analyze_ggcoefstats(
        _meta_frame(10), type="robust", **_meta_declarations()
    ).result
    bayesian_meta = analyze_ggcoefstats(
        _meta_frame(3),
        type="bayes",
        prior_mean_scale=1.0,
        prior_tau_scale=0.5,
        **_meta_declarations(),
    ).result
    for identifier, result in (
        ("coefficient-classical-v1", coefficient),
        ("coefficient-robust-v2", robust_coefficient),
        ("coefficient-bayesian-v3", posterior_coefficient),
        ("meta-classical-v1", meta),
        ("meta-robust-experimental-v2", robust_meta),
        ("meta-bayesian-v3", bayesian_meta),
    ):
        records.append(_Golden(identifier, "coefficient-result.schema.json", result))

    plot = gghistostats(pl.DataFrame({"value": [1.0, 2.0, 3.0, 4.0, 5.0]}), "value")
    composed = combine_plots((plot,), columns=1)
    records.append(
        _Golden("composition-v1", "composition-result.schema.json", composed.result)
    )
    composed.figure.clear()
    plot.figure.clear()
    return records


def _grouped_results() -> list[_Golden]:
    records: list[_Golden] = []
    histogram = _association_frame(grouped=True)
    dot = _dot_frame(grouped=True)
    association = _association_frame(grouped=True)
    between = _between_frame(grouped=True)
    within = _within_frame(grouped=True)
    categorical = _categorical_frame(grouped=True)

    for mode in ("parametric", "robust", "bayes"):
        common: dict[str, object] = {"type": mode}
        if mode == "bayes":
            common["prior_scale"] = 2.0
        association_options = dict(common)
        association_options.pop("prior_scale", None)
        if mode == "robust":
            association_options.update(random_seed=31, bootstrap_resamples=999)
        comparison_options = dict(common)
        if mode == "bayes":
            comparison_options.update(
                p_adjust="none",
                pairwise_display="all",
                prior_location=0.0,
                prior_scale=2.0,
                random_seed=37,
            )
        calls = (
            analyze_grouped_gghistostats(histogram, "x", "outer", **common),
            analyze_grouped_ggdotplotstats(dot, "value", "label", "outer", **common),
            analyze_grouped_ggscatterstats(
                association, "x", "y", "outer", **association_options
            ),
            analyze_grouped_ggcorrmat(
                association,
                ("x", "y", "z"),
                "outer",
                p_adjust="none",
                **association_options,
            ),
            analyze_grouped_ggbetweenstats(
                between, "group", "value", "outer", **comparison_options
            ),
            analyze_grouped_ggwithinstats(
                within,
                "condition",
                "value",
                "outer",
                subject_id="subject",
                **comparison_options,
            ),
        )
        for analysis in calls:
            records.append(
                _Golden(
                    analysis.result.analysis,
                    "grouped-result.schema.json",
                    analysis.result,
                )
            )

    for mode in ("parametric", "bayes"):
        records.append(
            _Golden(
                f"grouped-categorical-{mode}",
                "grouped-result.schema.json",
                analyze_grouped_ggbarstats(
                    categorical,
                    "answer",
                    "outer",
                    counts="count",
                    type=mode,
                    p_adjust="none",
                    pairwise_display="all",
                ).result,
            )
        )
    return records


def build_catalog() -> dict[str, Any]:
    entries = []
    for item in (*_direct_results(), *_grouped_results()):
        payload = item.result.to_dict()
        entries.append(
            {
                "id": item.identifier,
                "schema": f"schemas/{item.schema}",
                "result_type": type(item.result).__name__,
                "stability": (
                    "experimental"
                    if type(item.result).__name__ == "RobustMetaResult"
                    else "stable"
                ),
                "schema_version": payload["schema_version"],
                "analysis": payload["analysis"],
                "payload": payload,
            }
        )
    entries.sort(key=lambda entry: entry["id"])
    return {
        "catalog_version": 1,
        "distribution": "plotsalot",
        "generated_with_version": version("plotsalot"),
        "purpose": "M7C retained serialized-result compatibility corpus",
        "entries": entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    rendered = json.dumps(build_catalog(), indent=2, sort_keys=True) + "\n"
    if arguments.write:
        OUTPUT.write_text(rendered, encoding="utf-8")
        return 0
    if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != rendered:
        raise SystemExit("M7C golden result corpus is stale; run with --write")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
