from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import date
from typing import cast

import numpy as np
import polars as pl
from matplotlib.figure import Figure

from plotsalot import (
    RepeatedSampleAudit,
    analyze_ggbetweenstats,
    analyze_ggwithinstats,
    combine_plots,
    ggbetweenstats,
)
from plotsalot.comparison_data import (
    ComparisonSample,
    RepeatedSample,
    select_comparison_sample,
    select_repeated_sample,
)
from plotsalot.comparison_result import (
    ComparisonDesign,
    ComparisonTestResult,
    PairwiseDisplay,
    RepeatedCorrectionResult,
)
from plotsalot.composition import ComposedStatsPlot
from plotsalot.result import SampleAudit


class M3ContractGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.between = analyze_ggbetweenstats(
            pl.DataFrame(
                {
                    "g": ["a"] * 3 + ["b"] * 3 + ["c"] * 3,
                    "y": [1.0, 2.0, 4.0, 2.0, 5.0, 7.0, 8.0, 10.0, 11.0],
                }
            ),
            "g",
            "y",
        )
        self.within = analyze_ggwithinstats(
            pl.DataFrame(
                {
                    "id": [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4],
                    "c": ["a", "b", "c"] * 4,
                    "y": [1.0, 2.0, 4.0, 2.0, 5.0, 6.0, 4.0, 3.0, 8.0, 3.0, 6.0, 10.0],
                }
            ),
            "c",
            "y",
            subject_id="id",
        )

    def test_repeated_audit_guards_every_reconciliation_boundary(self) -> None:
        audit = cast(RepeatedSampleAudit, self.within.result.sample)
        operations = (
            lambda: replace(audit, input_rows=-1),
            lambda: replace(audit, input_rows=audit.input_rows + 1),
            lambda: replace(audit, analyzed_subjects=0),
            lambda: replace(audit, dropped_null_value_rows=cast(int, 1.5)),
        )
        for operation in operations:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

    def test_level_and_test_records_reject_incoherent_states(self) -> None:
        level = self.between.result.levels[0]
        level_operations = (
            lambda: replace(level, level=""),
            lambda: replace(level, level=float("nan")),
            lambda: replace(level, n_obs=1),
            lambda: replace(level, mean=float("nan")),
            lambda: replace(level, standard_deviation=-1.0),
            lambda: replace(
                level,
                interval=replace(level.interval, target="population_difference"),
            ),
            lambda: replace(
                level,
                interval=replace(
                    level.interval, low=level.mean + 1.0, high=level.mean + 2.0
                ),
            ),
        )
        for operation in level_operations:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

        test = self.between.result.omnibus
        test_operations = (
            lambda: replace(test, name="unsupported"),
            lambda: replace(test, statistic=float("nan")),
            lambda: replace(test, statistic=-1.0),
            lambda: replace(test, df1=None),
            lambda: replace(test, df1=0.0),
            lambda: replace(test, df2=0.0),
            lambda: replace(test, p_value=2.0),
            lambda: ComparisonTestResult(
                name="welch_t", statistic=1.0, df1=1.0, df2=3.0, p_value=0.2
            ),
        )
        for operation in test_operations:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

    def test_pairwise_records_reject_incoherent_states(self) -> None:
        item = self.between.result.pairwise[0]
        operations = (
            lambda: replace(item, left=""),
            lambda: replace(item, right=item.left),
            lambda: replace(item, estimate=float("nan")),
            lambda: replace(item, standard_error=0.0),
            lambda: replace(
                item,
                test=replace(
                    item.test,
                    name="welch_anova",
                    statistic=1.0,
                    df1=1.0,
                ),
            ),
            lambda: replace(
                item,
                interval=replace(item.interval, target="population_mean"),
            ),
            lambda: replace(
                item,
                interval=replace(
                    item.interval,
                    low=item.estimate + 1.0,
                    high=item.estimate + 2.0,
                ),
            ),
            lambda: replace(item, adjusted_p_value=-1.0),
        )
        for operation in operations:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

    def test_correction_record_rejects_invalid_states(self) -> None:
        correction = self.within.result.correction
        if correction is None:
            self.fail("fixture must produce a correction")
        operations = (
            lambda: replace(correction, name="hf"),
            lambda: replace(correction, epsilon=float("nan")),
            lambda: replace(correction, epsilon=0.0),
            lambda: replace(correction, corrected_df1=0.0),
            lambda: replace(correction, corrected_p_value=2.0),
        )
        for operation in operations:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

    def test_comparison_result_rejects_cross_field_mismatches(self) -> None:
        result = self.between.result
        first_pair = result.pairwise[0]
        sample = cast(SampleAudit, result.sample)
        mismatched_sample = replace(
            sample,
            input_rows=sample.input_rows + 1,
            analyzed_rows=sample.analyzed_rows + 1,
        )
        operations = (
            lambda: replace(result, schema_version=2),
            lambda: replace(result, design=cast(ComparisonDesign, "within")),
            lambda: replace(result, x=result.y),
            lambda: replace(result, subject_id="id"),
            lambda: replace(result, levels=result.levels[:1]),
            lambda: replace(result, levels=(result.levels[0],) * 3),
            lambda: replace(result, sample=mismatched_sample),
            lambda: replace(result, estimate=1.0, interval=None),
            lambda: replace(
                result, omnibus=replace(result.omnibus, name="paired_t", df1=None)
            ),
            lambda: replace(result, pairwise=result.pairwise[:1]),
            lambda: replace(
                result,
                pairwise=(
                    replace(first_pair, left=first_pair.right, right=first_pair.left),
                    *result.pairwise[1:],
                ),
            ),
            lambda: replace(result, p_adjust="fdr"),
            lambda: replace(result, pairwise_alpha=1.0),
            lambda: replace(
                result, pairwise_display=cast(PairwiseDisplay, "sometimes")
            ),
            lambda: replace(
                result,
                pairwise=(
                    replace(first_pair, significant=not first_pair.significant),
                    *result.pairwise[1:],
                ),
            ),
            lambda: replace(
                result,
                correction=cast(
                    RepeatedCorrectionResult, self.within.result.correction
                ),
            ),
            lambda: replace(result, warnings=("",)),
        )
        for operation in operations:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

    def test_repeated_result_rejects_subject_and_correction_mismatches(self) -> None:
        result = self.within.result
        sample = cast(RepeatedSampleAudit, result.sample)
        correction = cast(RepeatedCorrectionResult, result.correction)
        operations = (
            lambda: replace(result, subject_id=None),
            lambda: replace(result, subject_id=result.x),
            lambda: replace(
                result,
                sample=replace(sample, analyzed_subjects=sample.analyzed_subjects + 1),
            ),
            lambda: replace(
                result,
                levels=(replace(result.levels[0], n_obs=3), *result.levels[1:]),
            ),
            lambda: replace(
                result,
                correction=replace(correction, corrected_p_value=0.5),
            ),
            lambda: replace(
                result,
                correction=replace(correction, corrected_df1=0.5),
            ),
            lambda: replace(
                result,
                correction=replace(correction, corrected_df2=0.5),
            ),
        )
        for operation in operations:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

    def test_data_records_reject_additional_invalid_states(self) -> None:
        between = self.between.sample
        if not isinstance(between, ComparisonSample):
            self.fail("fixture must be independent")
        between_operations = (
            lambda: replace(between, x=""),
            lambda: replace(between, levels=("a", "a", "c")),
            lambda: replace(
                between,
                values=(np.array([[1.0, 2.0]]), *between.values[1:]),
            ),
            lambda: replace(
                between,
                values=(np.array([1.0, float("inf")]), *between.values[1:]),
            ),
            lambda: replace(
                between,
                audit=replace(
                    between.audit,
                    input_rows=between.audit.input_rows + 1,
                    analyzed_rows=between.audit.analyzed_rows + 1,
                ),
            ),
        )
        for operation in between_operations:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

        repeated = self.within.sample
        if not isinstance(repeated, RepeatedSample):
            self.fail("fixture must be repeated")
        repeated_operations = (
            lambda: replace(repeated, subject_id=repeated.x),
            lambda: replace(repeated, conditions=("a",)),
            lambda: replace(repeated, subjects=(1,) * len(repeated.subjects)),
            lambda: replace(repeated, values=repeated.values.ravel()),
            lambda: replace(repeated, values=np.full(repeated.values.shape, np.inf)),
        )
        for operation in repeated_operations:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

    def test_data_boundaries_reject_identity_and_empty_cases(self) -> None:
        operations = (
            lambda: select_comparison_sample(
                pl.DataFrame(
                    {
                        "g": [date(2026, 1, 1)] * 2 + [date(2026, 1, 2)] * 2,
                        "y": [1.0, 2.0, 3.0, 4.0],
                    }
                ),
                "g",
                "y",
            ),
            lambda: select_comparison_sample(
                pl.DataFrame({"g": ["", "", "b", "b"], "y": [1.0, 2.0, 3.0, 4.0]}),
                "g",
                "y",
            ),
            lambda: select_comparison_sample(
                pl.DataFrame({"g": [None, None], "y": [1.0, 2.0]}),
                "g",
                "y",
            ),
            lambda: select_comparison_sample(
                pl.DataFrame({"g": ["a", "a"], "y": [1.0, 2.0]}),
                "g",
                "y",
            ),
            lambda: select_repeated_sample(
                pl.DataFrame({"id": [None, None], "c": [None, None], "y": [1.0, 2.0]}),
                "c",
                "y",
                "id",
            ),
            lambda: select_repeated_sample(
                pl.DataFrame(
                    {
                        "id": [1, 2, 3],
                        "c": ["a", "a", "a"],
                        "y": [1.0, 2.0, 3.0],
                    }
                ),
                "c",
                "y",
                "id",
            ),
        )
        for operation in operations:
            with (
                self.subTest(operation=operation),
                self.assertRaises((TypeError, ValueError)),
            ):
                operation()

        bool_sample = select_comparison_sample(
            pl.DataFrame({"g": [True, True, False, False], "y": [1.0, 3.0, 2.0, 5.0]}),
            "g",
            "y",
        )
        self.assertEqual(bool_sample.levels, (False, True))
        float_sample = select_comparison_sample(
            pl.DataFrame({"g": [2.0, 2.0, 1.0, 1.0], "y": [1.0, 3.0, 2.0, 5.0]}),
            "g",
            "y",
        )
        self.assertEqual(float_sample.levels, (1.0, 2.0))

    def test_composition_records_reject_incoherent_states(self) -> None:
        plot = ggbetweenstats(
            pl.DataFrame({"g": ["a", "a", "b", "b"], "y": [1.0, 3.0, 2.0, 5.0]}),
            "g",
            "y",
        )
        self.addCleanup(plot.figure.clear)
        composed = combine_plots([plot])
        self.addCleanup(composed.figure.clear)
        panel = composed.result.panels[0]
        panel_operations = (
            lambda: replace(panel, panel=""),
            lambda: replace(panel, source_index=-1),
            lambda: replace(panel, group=""),
            lambda: replace(panel, group=float("nan")),
            lambda: replace(panel, tag=""),
        )
        for operation in panel_operations:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

        result = composed.result
        result_operations = (
            lambda: replace(result, schema_version=2),
            lambda: replace(result, rows=0),
            lambda: replace(result, rows=1, columns=1, panels=(panel, panel)),
            lambda: replace(result, guides="collect"),
            lambda: replace(result, x_label=""),
            lambda: replace(result, y_label=""),
            lambda: replace(result, panel_tags="roman"),
            lambda: replace(result, panel_tags="A"),
            lambda: replace(result, panels=(panel, replace(panel, source_index=1))),
            lambda: replace(result, warnings=("",)),
        )
        for operation in result_operations:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

        other = Figure()
        self.addCleanup(other.clear)
        with self.assertRaises(ValueError):
            ComposedStatsPlot(
                figure=composed.figure,
                axes={"wrong": composed.figure.subplots()},
                result=result,
                annotations=composed.annotations,
            )
        with self.assertRaises(ValueError):
            ComposedStatsPlot(
                figure=composed.figure,
                axes={"panel_1": other.subplots()},
                result=result,
                annotations=composed.annotations,
            )
        self.assertEqual(composed.subtitle, "")
        self.assertEqual(composed.caption, "")


if __name__ == "__main__":
    unittest.main()
