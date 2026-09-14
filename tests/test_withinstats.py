from __future__ import annotations

import json
import math
import unittest

import numpy as np
import polars as pl

from plotsalot import (
    RepeatedSampleAudit,
    analyze_ggwithinstats,
    extract_stats,
    ggwithinstats,
    render_ggwithinstats,
)


class WithinStatsTests(unittest.TestCase):
    def _two_condition_data(self) -> pl.DataFrame:
        return pl.DataFrame(
            {
                "subject": [4, 1, 3, 2, 2, 4, 1, 3],
                "condition": ["b", "a", "b", "a", "b", "a", "b", "a"],
                "value": [6.0, 1.0, 3.0, 2.0, 5.0, 3.0, 2.0, 4.0],
            }
        )

    def test_paired_result_uses_explicit_subject_aligned_differences(self) -> None:
        result = analyze_ggwithinstats(
            self._two_condition_data(),
            "condition",
            "value",
            subject_id="subject",
        ).result
        differences = np.array([-1.0, -3.0, 1.0, -3.0])
        mean = float(differences.mean())
        deviation = float(differences.std(ddof=1))
        standard_error = deviation / math.sqrt(differences.size)
        correction_df = differences.size - 1
        correction = math.gamma(correction_df / 2) / (
            math.sqrt(correction_df / 2) * math.gamma((correction_df - 1) / 2)
        )

        self.assertEqual(tuple(level.level for level in result.levels), ("a", "b"))
        self.assertEqual(result.omnibus.name, "paired_t")
        self.assertAlmostEqual(result.estimate or 0.0, mean)
        self.assertAlmostEqual(result.omnibus.statistic, mean / standard_error)
        self.assertAlmostEqual(result.omnibus.df2, 3.0)
        self.assertAlmostEqual(result.effect_size.value, mean / deviation * correction)
        self.assertEqual(result.pairwise, ())
        self.assertIsNone(result.correction)
        json.dumps(result.to_dict(), allow_nan=False)

    def test_repeated_anova_reports_both_greenhouse_geisser_paths(self) -> None:
        data = pl.DataFrame(
            {
                "subject": [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4],
                "condition": ["a", "b", "c"] * 4,
                "value": [1.0, 2.0, 4.0, 2.0, 5.0, 6.0, 4.0, 3.0, 8.0, 3.0, 6.0, 10.0],
            }
        )
        result = analyze_ggwithinstats(
            data,
            "condition",
            "value",
            subject_id="subject",
            pairwise_display="none",
        ).result

        self.assertEqual(result.omnibus.name, "repeated_measures_anova")
        self.assertAlmostEqual(result.omnibus.statistic, 12.6)
        correction = result.correction
        if correction is None:
            self.fail("repeated ANOVA must retain its correction")
        self.assertAlmostEqual(correction.uncorrected_df1, 2.0)
        self.assertAlmostEqual(correction.uncorrected_df2, 6.0)
        self.assertAlmostEqual(correction.epsilon, 0.986842105263158)
        self.assertEqual(result.omnibus.df1, correction.corrected_df1)
        self.assertEqual(result.omnibus.df2, correction.corrected_df2)
        self.assertEqual(result.omnibus.p_value, correction.corrected_p_value)
        self.assertEqual(len(result.pairwise), 3)
        self.assertTrue(all(item.test.df2 == 3.0 for item in result.pairwise))
        self.assertTrue(all(level.n_obs == 4 for level in result.levels))

    def test_reordering_rows_does_not_change_pairing_or_inference(self) -> None:
        data = self._two_condition_data()
        first = analyze_ggwithinstats(
            data, "condition", "value", subject_id="subject"
        ).result
        second = analyze_ggwithinstats(
            data.reverse(), "condition", "value", subject_id="subject"
        ).result

        self.assertEqual(first.to_dict(), second.to_dict())

    def test_complete_block_exclusions_are_visible_in_result_and_plot(self) -> None:
        data = pl.DataFrame(
            {
                "subject": [1, 1, 2, 2, 3, 3, 4, 5, 5],
                "condition": ["a", "b", "a", "b", "a", "b", "a", "a", "b"],
                "value": [1.0, 2.0, 2.0, 5.0, 4.0, 3.0, 9.0, 5.0, None],
            }
        )
        analysis = analyze_ggwithinstats(
            data, "condition", "value", subject_id="subject"
        )
        sample = analysis.result.sample
        if not isinstance(sample, RepeatedSampleAudit):
            self.fail("within result must use a repeated sample audit")
        self.assertEqual(sample.analyzed_subjects, 3)
        self.assertEqual(sample.excluded_incomplete_subjects, 2)

        plot = render_ggwithinstats(analysis, title="Repeated comparison")
        self.addCleanup(plot.figure.clear)
        self.assertIs(extract_stats(plot), analysis.result)
        self.assertIn("3 complete subject(s)", plot.caption)
        self.assertIn("paired_t", plot.subtitle)
        self.assertEqual(plot.title, "Repeated comparison")

    def test_repeated_surface_rejects_ambiguous_and_degenerate_pairing(self) -> None:
        valid = self._two_condition_data()
        duplicate = pl.concat([valid, valid.slice(0, 1)])
        constant_differences = pl.DataFrame(
            {
                "subject": [1, 1, 2, 2, 3, 3],
                "condition": ["a", "b"] * 3,
                "value": [1.0, 2.0, 2.0, 3.0, 4.0, 5.0],
            }
        )
        operations = (
            lambda: analyze_ggwithinstats(
                duplicate, "condition", "value", subject_id="subject"
            ),
            lambda: analyze_ggwithinstats(
                constant_differences, "condition", "value", subject_id="subject"
            ),
            lambda: analyze_ggwithinstats(
                valid,
                "condition",
                "value",
                subject_id="subject",
                maximum_subject_paths=0,
            ),
        )
        for operation in operations:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

    def test_subject_path_limit_is_a_render_only_explicit_gate(self) -> None:
        analysis = analyze_ggwithinstats(
            self._two_condition_data(),
            "condition",
            "value",
            subject_id="subject",
            maximum_subject_paths=3,
        )
        with self.assertRaisesRegex(ValueError, "maximum_subject_paths=3"):
            render_ggwithinstats(analysis)

        plot = render_ggwithinstats(analysis, show_subject_paths=False)
        self.addCleanup(plot.figure.clear)
        self.assertIs(plot.result, analysis.result)

    def test_public_surface_requires_subject_id_and_supports_quiet_subtitle(
        self,
    ) -> None:
        plot = ggwithinstats(
            self._two_condition_data(),
            "condition",
            "value",
            subject_id="subject",
            results_subtitle=False,
        )
        self.addCleanup(plot.figure.clear)
        self.assertIn("paired_t", plot.subtitle)


if __name__ == "__main__":
    unittest.main()
