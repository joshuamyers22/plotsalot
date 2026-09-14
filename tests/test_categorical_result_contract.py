from __future__ import annotations

import unittest
from dataclasses import replace
from typing import cast

import polars as pl

from plotsalot import analyze_categorical
from plotsalot.categorical_result import (
    CategoricalCellResult,
    CategoricalEffectResult,
    CategoricalFollowupResult,
    CategoricalSampleAudit,
)
from plotsalot.result import IntervalResult


def _independent_result():
    return analyze_categorical(
        pl.DataFrame(
            {
                "x": ["a", "a", "b", "b", "c", "c"],
                "y": ["u", "v", "u", "v", "u", "v"],
                "n": [30, 10, 15, 25, 10, 30],
            }
        ),
        "x",
        "y",
        counts="n",
    ).result


class CategoricalRecordContractTests(unittest.TestCase):
    def test_sample_and_cell_records_reject_invalid_states(self) -> None:
        sample_operations = (
            lambda: CategoricalSampleAudit(-1, 1, 1, 0, 0, 0),
            lambda: CategoricalSampleAudit(cast(int, 1.5), 1, 1, 0, 0, 0),
            lambda: CategoricalSampleAudit(2, 1, 1, 0, 0, 0),
            lambda: CategoricalSampleAudit(1, 0, 1, 1, 0, 0),
            lambda: CategoricalSampleAudit(1, 1, 0, 0, 0, 0),
        )
        for operation in sample_operations:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

        valid = CategoricalCellResult("a", None, 2, 2.0, 1.0, 1.0, 0.0, 0.0)
        cell_operations = (
            lambda: replace(valid, observed=-1),
            lambda: replace(valid, observed=cast(int, True)),
            lambda: replace(valid, displayed_proportion=1.1),
            lambda: replace(valid, joint_proportion=float("nan")),
            lambda: replace(valid, expected=float("inf")),
            lambda: replace(valid, expected=0.0),
            lambda: replace(valid, contribution=-1.0),
        )
        for operation in cell_operations:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

    def test_test_effect_and_adequacy_records_reject_invalid_states(self) -> None:
        result = _independent_result()
        test = result.omnibus
        effect = result.effect
        adequacy = result.adequacy
        if adequacy is None:
            self.fail("independent result must retain adequacy")
        operations = (
            lambda: replace(test, name="unsupported"),
            lambda: replace(test, statistic=-1.0),
            lambda: replace(test, statistic=float("nan")),
            lambda: replace(test, df=-1.0),
            lambda: replace(test, p_value=1.1),
            lambda: replace(effect, name="unsupported"),
            lambda: replace(effect, value=float("nan")),
            lambda: replace(effect, value=-0.1),
            lambda: CategoricalEffectResult(
                "cohen_g", 0.6, IntervalResult("cohen_g", "exact", 0.95, 0.5, 0.7)
            ),
            lambda: replace(effect, interval=replace(effect.interval, low=1.0)),
            lambda: replace(adequacy, minimum=0.9),
            lambda: replace(adequacy, cells_below_five=-1),
            lambda: replace(adequacy, cells_below_five=7),
            lambda: replace(adequacy, total_cells=0),
            lambda: replace(adequacy, rule="unsupported"),
        )
        for operation in operations:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

    def test_followup_records_reject_invalid_states(self) -> None:
        pairwise = _independent_result().pairwise[0]
        operations = (
            lambda: replace(pairwise, family=cast(object, "other")),
            lambda: replace(pairwise, right=None),
            lambda: replace(pairwise, observed=()),
            lambda: replace(pairwise, observed=(-1,) * len(pairwise.observed)),
            lambda: replace(pairwise, shape=(1, len(pairwise.observed))),
            lambda: replace(pairwise, shape=(2, 0)),
            lambda: replace(pairwise, adjusted_p_value=-0.1),
            lambda: CategoricalFollowupResult(
                "stratum",
                "u",
                "v",
                pairwise.observed,
                pairwise.shape,
                pairwise.test,
                pairwise.effect,
                pairwise.adjusted_p_value,
                pairwise.significant,
                pairwise.adequacy,
            ),
            lambda: replace(
                pairwise,
                family="stratum",
                right=None,
                shape=(1, len(pairwise.observed)),
            ),
        )
        for operation in operations:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

    def test_categorical_result_rejects_cross_field_contradictions(self) -> None:
        result = _independent_result()
        cell = result.cells[0]
        invalid = (
            lambda: replace(result, schema_version=2),
            lambda: replace(result, x=""),
            lambda: replace(result, y=result.x),
            lambda: replace(result, counts=result.x),
            lambda: replace(result, design="one_way"),
            lambda: replace(result, y_levels=("u",)),
            lambda: replace(result, x_levels=("a",)),
            lambda: replace(result, y_levels=("u", "u")),
            lambda: replace(
                result, cells=(replace(cell, y_level="v"), *result.cells[1:])
            ),
            lambda: replace(
                result,
                cells=(
                    replace(
                        cell,
                        displayed_proportion=cell.displayed_proportion + 0.01,
                    ),
                    *result.cells[1:],
                ),
            ),
            lambda: replace(result, row_totals=result.row_totals[:-1]),
            lambda: replace(result, row_totals=(41, 39, 40)),
            lambda: replace(result, column_totals=(54, 66)),
            lambda: replace(result, ratio=(0.5, 0.5)),
            lambda: replace(result, ratio=(0.4, 0.3, float("nan"))),
            lambda: replace(result, p_adjust="unsupported"),
            lambda: replace(result, alpha=0.0),
            lambda: replace(result, conf_level=1.0),
            lambda: replace(result, pairwise_display=cast(object, "unsupported")),
            lambda: replace(
                result,
                pairwise=(
                    replace(result.pairwise[0], significant=False),
                    *result.pairwise[1:],
                ),
            ),
            lambda: replace(result, adequacy=None),
            lambda: replace(result, pairwise=()),
            lambda: replace(
                result,
                pairwise=(
                    replace(
                        result.pairwise[0],
                        observed=(
                            result.pairwise[0].observed[0] + 1,
                            *result.pairwise[0].observed[1:],
                        ),
                    ),
                    *result.pairwise[1:],
                ),
            ),
            lambda: replace(
                result,
                pairwise=(
                    replace(result.pairwise[0], left="b"),
                    *result.pairwise[1:],
                ),
            ),
            lambda: replace(result, strata=()),
            lambda: replace(
                result,
                strata=(
                    replace(result.strata[0], left="v"),
                    *result.strata[1:],
                ),
            ),
            lambda: replace(result, warnings=("",)),
            lambda: replace(
                result,
                effect=replace(
                    result.effect,
                    interval=replace(result.effect.interval, level=0.9),
                ),
            ),
        )
        for operation in invalid:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

        one_way = analyze_categorical(
            pl.DataFrame({"x": ["a", "b"], "n": [10, 10]}), "x", counts="n"
        ).result
        paired = analyze_categorical(
            pl.DataFrame(
                {
                    "x": ["a", "a", "b", "b"],
                    "y": ["a", "b", "a", "b"],
                    "n": [10, 5, 10, 10],
                }
            ),
            "x",
            "y",
            counts="n",
            paired=True,
            proportion_test=False,
        ).result
        with self.assertRaises(ValueError):
            replace(one_way, column_totals=(20,))
        with self.assertRaises(ValueError):
            replace(paired, proportion_test=True)


if __name__ == "__main__":
    unittest.main()
