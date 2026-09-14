from __future__ import annotations

import json
import unittest
from dataclasses import replace
from pathlib import Path
from typing import cast

import numpy as np
import polars as pl

from plotsalot import (
    DotPlotAnalysis,
    ResourceLimits,
    analyze_ggcorrmat,
    analyze_ggdotplotstats,
    analyze_ggscatterstats,
)
from plotsalot.correlation_analysis import CorrelationAnalysis
from plotsalot.data import PairedNumericSample


class M2ResultContractTests(unittest.TestCase):
    def _assert_schema_keys(self, filename: str, payload: dict[str, object]) -> None:
        schema = json.loads(
            (Path(__file__).resolve().parents[1] / "schemas" / filename).read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(set(payload), set(schema["required"]))

    def test_resource_limits_reject_nonpositive_configuration(self) -> None:
        operations = (
            lambda: ResourceLimits(maximum_rows=0),
            lambda: ResourceLimits(maximum_rows=10, maximum_groups=0),
            lambda: ResourceLimits(maximum_rows=10, maximum_variables=-1),
            lambda: ResourceLimits(maximum_rows=10, maximum_labels=0),
            lambda: ResourceLimits(maximum_rows=True),
            lambda: ResourceLimits(maximum_rows=cast(int, 1.5)),
        )
        for operation in operations:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

    def test_dot_records_reject_incoherent_states(self) -> None:
        analysis = analyze_ggdotplotstats(
            pl.DataFrame(
                {"value": [1.0, 2.0, 4.0, 5.0], "label": ["a", "a", "b", "b"]}
            ),
            "value",
            "label",
        )
        result = analysis.result
        self.assertEqual(result.limits.maximum_labels, 200)
        self._assert_schema_keys("dotplot-result.schema.json", result.to_dict())
        estimate = result.estimates[0]
        interval = estimate.interval
        if interval is None:
            self.fail("ordinary labeled estimate should have an interval")

        invalid_estimates = (
            lambda: replace(estimate, label=""),
            lambda: replace(estimate, value=float("nan")),
            lambda: replace(estimate, standard_deviation=0.0),
            lambda: replace(estimate, interval=None),
            lambda: replace(
                estimate,
                interval=replace(interval, target="sample_mean"),
            ),
            lambda: replace(
                estimate,
                interval=replace(
                    interval,
                    low=estimate.value + 1.0,
                    high=estimate.value + 2.0,
                ),
            ),
            lambda: replace(estimate, warnings=("",)),
        )
        for operation in invalid_estimates:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

        mismatched_sample = replace(
            result.sample,
            input_rows=result.sample.input_rows + 1,
            dropped_null_rows=result.sample.dropped_null_rows + 1,
        )
        invalid_results = (
            lambda: replace(result, schema_version=2),
            lambda: replace(result, analysis="unsupported"),
            lambda: replace(result, x=""),
            lambda: replace(result, label_column=result.x),
            lambda: replace(result, sample=mismatched_sample),
            lambda: replace(
                result,
                one_sample=replace(result.one_sample, column="other"),
            ),
            lambda: replace(result, estimates=()),
            lambda: replace(result, estimates=(estimate, estimate)),
            lambda: replace(result, estimates=(estimate,)),
            lambda: replace(result, warnings=("",)),
        )
        for operation in invalid_results:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

        with self.assertRaises(ValueError):
            DotPlotAnalysis(
                sample=replace(analysis.sample, column="other"),
                result=result,
            )
        with self.assertRaises(ValueError):
            DotPlotAnalysis(
                sample=replace(analysis.sample, audit=mismatched_sample),
                result=result,
            )

    def test_correlation_records_reject_incoherent_states(self) -> None:
        analysis = analyze_ggscatterstats(
            pl.DataFrame({"x": [1.0, 2.0, 3.0, 4.0], "y": [1.0, 3.0, 2.0, 4.0]}),
            "x",
            "y",
        )
        result = analysis.result
        self._assert_schema_keys("correlation-result.schema.json", result.to_dict())

        invalid_tests = (
            lambda: replace(result.test, name="spearman"),
            lambda: replace(result.test, alternative="greater"),
            lambda: replace(result.test, statistic=float("nan")),
            lambda: replace(result.test, df=1),
            lambda: replace(result.test, p_value=2.0),
        )
        for operation in invalid_tests:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

        invalid_results = (
            lambda: replace(result, schema_version=2),
            lambda: replace(result, analysis="unsupported"),
            lambda: replace(result, y=result.x),
            lambda: replace(result, estimate=2.0),
            lambda: replace(result, test=replace(result.test, df=3)),
            lambda: replace(
                result,
                interval=replace(result.interval, target="sample_correlation"),
            ),
            lambda: replace(
                result,
                interval=replace(result.interval, low=-2.0),
            ),
            lambda: replace(
                result,
                interval=replace(result.interval, low=result.estimate + 0.01),
            ),
            lambda: replace(result, test=replace(result.test, statistic=None)),
            lambda: replace(result, warnings=("",)),
        )
        for operation in invalid_results:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

        with self.assertRaises(ValueError):
            CorrelationAnalysis(
                sample=replace(analysis.sample, y="other"), result=result
            )
        altered_audit = replace(
            analysis.sample.audit,
            input_rows=analysis.sample.audit.input_rows + 1,
            dropped_null_rows=analysis.sample.audit.dropped_null_rows + 1,
        )
        with self.assertRaises(ValueError):
            CorrelationAnalysis(
                sample=replace(analysis.sample, audit=altered_audit), result=result
            )

    def test_matrix_records_reject_incoherent_states(self) -> None:
        result = analyze_ggcorrmat(
            pl.DataFrame(
                {
                    "a": [1.0, 2.0, 3.0, 4.0],
                    "b": [4.0, 2.0, 3.0, 1.0],
                }
            ),
            ("a", "b"),
        ).result
        self._assert_schema_keys(
            "correlation-matrix-result.schema.json", result.to_dict()
        )
        diagonal = next(cell for cell in result.cells if cell.x == cell.y)
        off_diagonal = next(cell for cell in result.cells if cell.x != cell.y)

        invalid_cells = (
            lambda: replace(diagonal, x=""),
            lambda: replace(diagonal, estimate=2.0),
            lambda: replace(diagonal, statistic=0.0),
            lambda: replace(diagonal, interval=result.cells[1].interval),
            lambda: replace(off_diagonal, interval=None),
            lambda: replace(off_diagonal, df=99),
            lambda: replace(off_diagonal, p_value=2.0),
            lambda: replace(off_diagonal, adjusted_p_value=-1.0),
        )
        for operation in invalid_cells:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

        duplicate_identity = replace(result.cells[-1], x="a", y="a")
        asymmetric = tuple(
            replace(cell, significant=not cell.significant)
            if cell.x == "a" and cell.y == "b"
            else cell
            for cell in result.cells
        )
        invalid_results = (
            lambda: replace(result, schema_version=2),
            lambda: replace(result, analysis="unsupported"),
            lambda: replace(result, columns=("a",)),
            lambda: replace(result, p_adjust="fdr"),
            lambda: replace(result, sig_level=1.0),
            lambda: replace(result, cells=result.cells[:-1]),
            lambda: replace(
                result,
                cells=result.cells[:-1] + (duplicate_identity,),
            ),
            lambda: replace(result, cells=asymmetric),
            lambda: replace(result, warnings=("",)),
        )
        for operation in invalid_results:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

    def test_paired_sample_owns_data_and_rejects_invalid_shapes(self) -> None:
        sample = analyze_ggscatterstats(
            pl.DataFrame({"x": [1.0, 2.0, 3.0, 4.0], "y": [4.0, 1.0, 3.0, 2.0]}),
            "x",
            "y",
        ).sample
        self.assertFalse(sample.x_values.flags.writeable)
        self.assertFalse(sample.y_values.flags.writeable)

        invalid_samples = (
            lambda: replace(sample, y=sample.x),
            lambda: replace(sample, x_values=np.array([[1.0, 2.0]])),
            lambda: replace(sample, y_values=np.array([1.0, 2.0])),
            lambda: replace(
                sample,
                audit=replace(
                    sample.audit,
                    input_rows=5,
                    analyzed_rows=5,
                    dropped_null_rows=0,
                ),
            ),
            lambda: replace(
                sample,
                x_values=np.array([1.0, 2.0, 3.0, float("inf")]),
            ),
        )
        for operation in invalid_samples:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

        copied = PairedNumericSample(
            x=sample.x,
            y=sample.y,
            x_values=sample.x_values,
            y_values=sample.y_values,
            audit=sample.audit,
        )
        self.assertIsNot(copied.x_values, sample.x_values)


class M2AnalysisFailureTests(unittest.TestCase):
    def test_dot_analysis_rejects_method_boundary_errors(self) -> None:
        valid = pl.DataFrame({"x": [1.0, 2.0], "label": ["a", "b"]})
        operations = (
            lambda: analyze_ggdotplotstats(valid, "x", "label", conf_level=1.0),
            lambda: analyze_ggdotplotstats(
                valid,
                "x",
                "label",
                alternative="unsupported",  # type: ignore[arg-type]
            ),
            lambda: analyze_ggdotplotstats(
                valid, "x", "label", test_value=float("nan")
            ),
            lambda: analyze_ggdotplotstats(valid, "x", "label", maximum_rows=1),
            lambda: analyze_ggdotplotstats(valid, "x", "label", maximum_labels=0),
            lambda: analyze_ggdotplotstats(valid, "x", "label", maximum_labels=1),
            lambda: analyze_ggdotplotstats(
                pl.DataFrame({"x": [1.0, None], "label": ["a", "a"]}),
                "x",
                "label",
            ),
            lambda: analyze_ggdotplotstats(
                pl.DataFrame({"x": [1.0, 2.0], "label": ["", ""]}),
                "x",
                "label",
            ),
        )
        for operation in operations:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

    def test_correlation_analysis_rejects_boundary_errors(self) -> None:
        valid = pl.DataFrame({"x": [1.0, 2.0, 3.0, 4.0], "y": [4.0, 1.0, 3.0, 2.0]})
        near_constant = pl.DataFrame(
            {
                "x": [1e14, 1e14 + 1.0, 1e14 + 2.0, 1e14 + 3.0],
                "y": [1.0, 2.0, 3.0, 4.0],
            }
        )
        operations = (
            lambda: analyze_ggscatterstats(valid, "x", "y", conf_level=0.0),
            lambda: analyze_ggscatterstats(near_constant, "x", "y"),
            lambda: analyze_ggcorrmat(object(), ("x", "y")),
            lambda: analyze_ggcorrmat(valid, ("x", "y"), maximum_rows=3),
            lambda: analyze_ggcorrmat(valid, ("x", "missing")),
            lambda: analyze_ggcorrmat(
                pl.DataFrame({"x": [1, 2, 3, 4], "y": ["a", "b", "c", "d"]}),
                ("x", "y"),
            ),
            lambda: analyze_ggcorrmat(
                pl.DataFrame({"x": [1.0, 2.0, 3.0, 4.0], "y": [1.0, 2.0, 3.0, np.inf]}),
                ("x", "y"),
            ),
            lambda: analyze_ggcorrmat(
                pl.DataFrame({"x": [1.0, 2.0, 3.0], "y": [3.0, 2.0, 1.0]}),
                ("x", "y"),
            ),
        )
        for operation in operations:
            with (
                self.subTest(operation=operation),
                self.assertRaises((TypeError, ValueError)),
            ):
                operation()


if __name__ == "__main__":
    unittest.main()
