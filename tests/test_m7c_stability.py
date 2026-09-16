from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from typing import Any, Literal, cast

import polars as pl
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from plotsalot import (
    M6CMetaError,
    StructuredResult,
    analyze_ggcoefstats,
    analyze_gghistostats,
    analyze_grouped_gghistostats,
    combine_plots,
    gghistostats,
    ggpiestats,
    grouped_gghistostats,
)
from tools.public_contract import coded_error_values

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "docs" / "m7" / "golden-results.json"
MANIFEST_PATH = ROOT / "docs" / "m7" / "public-contract.json"
SCHEMA_ROOT = ROOT / "schemas"


def _load_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _schemas() -> dict[str, dict[str, Any]]:
    return {path.name: _load_json(path) for path in SCHEMA_ROOT.glob("*.json")}


def _registry(schemas: dict[str, dict[str, Any]]) -> Registry[Any]:
    registry: Registry[Any] = Registry()
    for name, schema in schemas.items():
        resource = Resource.from_contents(schema)
        for uri in (
            cast(str, schema["$id"]),
            f"https://plotsalot.dev/schemas/{name}",
            f"https://plotsalot.invalid/schemas/{name}",
        ):
            registry = registry.with_resource(uri, resource)
    return registry


def _entry_by_id(catalog: dict[str, Any], identifier: str) -> dict[str, Any]:
    entries = cast(list[dict[str, Any]], catalog["entries"])
    return next(entry for entry in entries if entry["id"] == identifier)


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


def _meta_result(
    count: int,
    *,
    mode: Literal["parametric", "robust", "bayes"] = "parametric",
    maximum_work: int = 100_000_000,
) -> StructuredResult:
    analysis = analyze_ggcoefstats(
        _meta_frame(count),
        meta_analytic_effect=True,
        type=mode,
        estimand="population treatment effect",
        effect_scale="mean difference",
        effect_direction="positive favors treatment",
        effect_units="points",
        prior_mean_scale=1.0 if mode == "bayes" else None,
        prior_tau_scale=0.5 if mode == "bayes" else None,
        maximum_work=maximum_work,
    )
    return cast(StructuredResult, analysis.result)


def _coefficient_result() -> StructuredResult:
    analysis = analyze_ggcoefstats(
        pl.DataFrame(
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
        ),
        estimate_label="coefficient",
        effect_scale="additive",
        effect_direction="positive is higher",
        effect_units="points",
    )
    return cast(StructuredResult, analysis.result)


class M7CGoldenSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = _load_json(CATALOG_PATH)
        cls.manifest = _load_json(MANIFEST_PATH)
        cls.schemas = _schemas()
        cls.registry = _registry(cls.schemas)

    def _validator(self, entry: dict[str, Any]) -> Draft202012Validator:
        schema_name = Path(cast(str, entry["schema"])).name
        return Draft202012Validator(self.schemas[schema_name], registry=self.registry)

    def test_all_schemas_are_valid_draft_2020_12_documents(self) -> None:
        self.assertEqual(len(self.schemas), 12)
        for name, schema in self.schemas.items():
            with self.subTest(schema=name):
                Draft202012Validator.check_schema(schema)

    def test_golden_corpus_covers_every_result_type_and_discriminator(self) -> None:
        entries = cast(list[dict[str, Any]], self.catalog["entries"])
        self.assertEqual(self.catalog["catalog_version"], 1)
        self.assertEqual(self.catalog["generated_with_version"], "1.0.0")
        self.assertEqual(len(entries), 51)
        self.assertEqual(len({cast(str, entry["id"]) for entry in entries}), 51)
        self.assertEqual(
            {cast(str, entry["result_type"]) for entry in entries},
            set(cast(list[str], self.manifest["serialized_result_types"])),
        )

        golden_variants = {
            (
                cast(str, entry["schema"]),
                cast(int, entry["schema_version"]),
                cast(str, entry["analysis"]),
            )
            for entry in entries
        }
        manifest_variants = {
            (
                cast(str, schema["path"]),
                cast(int, variant["schema_version"]),
                cast(str, variant["analysis"]),
            )
            for schema in cast(list[dict[str, Any]], self.manifest["schemas"])
            if schema["role"] == "serialized_result"
            for variant in cast(list[dict[str, Any]], schema["variants"])
        }
        self.assertEqual(golden_variants, manifest_variants)
        self.assertEqual(
            [entry["id"] for entry in entries if entry["stability"] == "experimental"],
            ["meta-robust-experimental-v2"],
        )

    def test_every_golden_payload_validates_and_round_trips_as_strict_json(
        self,
    ) -> None:
        entries = cast(list[dict[str, Any]], self.catalog["entries"])
        for entry in entries:
            payload = cast(dict[str, Any], entry["payload"])
            with self.subTest(entry=entry["id"]):
                self._validator(entry).validate(  # pyright: ignore[reportUnknownMemberType]
                    payload
                )
                rendered = json.dumps(payload, allow_nan=False, sort_keys=True)
                self.assertEqual(json.loads(rendered), payload)

    def test_field_type_version_discriminator_and_unknown_mutations_fail(self) -> None:
        entries = cast(list[dict[str, Any]], self.catalog["entries"])
        for entry in entries:
            payload = cast(dict[str, Any], entry["payload"])
            mutations: dict[str, dict[str, Any]] = {}

            missing = copy.deepcopy(payload)
            del missing["warnings"]
            mutations["missing_field"] = missing

            wrong_type = copy.deepcopy(payload)
            wrong_type["schema_version"] = []
            mutations["wrong_type"] = wrong_type

            wrong_version = copy.deepcopy(payload)
            wrong_version["schema_version"] = 999
            mutations["wrong_version"] = wrong_version

            wrong_discriminator = copy.deepcopy(payload)
            wrong_discriminator["analysis"] = "m7c_invalid_discriminator"
            mutations["wrong_discriminator"] = wrong_discriminator

            unknown = copy.deepcopy(payload)
            unknown["m7c_unknown_property"] = True
            mutations["unknown_property"] = unknown

            validator = self._validator(entry)
            for mutation_name, mutation in mutations.items():
                with self.subTest(entry=entry["id"], mutation=mutation_name):
                    self.assertFalse(
                        validator.is_valid(  # pyright: ignore[reportUnknownMemberType]
                            mutation
                        )
                    )

    def test_0_1_1_calls_replay_retained_top_level_shapes(self) -> None:
        frame = pl.DataFrame({"value": [1.0, 2.0, 3.0, 4.0, 5.0]})
        replayed: dict[str, StructuredResult] = {
            "analysis-histogram-v1": analyze_gghistostats(frame, "value").result,
            "robust-histogram-v2": analyze_gghistostats(
                frame, "value", type="robust"
            ).result,
            "bayesian-histogram-v3": analyze_gghistostats(
                frame, "value", type="bayes", prior_scale=2.0
            ).result,
            "meta-classical-v1": _meta_result(5),
            "meta-robust-experimental-v2": _meta_result(10, mode="robust"),
            "meta-bayesian-v3": _meta_result(3, mode="bayes"),
            "coefficient-classical-v1": _coefficient_result(),
            "grouped_gghistostats_one_sample_parametric": cast(
                StructuredResult,
                analyze_grouped_gghistostats(
                    pl.DataFrame(
                        {
                            "value": [1.0, 2.0, 3.0, 2.0, 3.0, 5.0],
                            "group": ["a", "a", "a", "b", "b", "b"],
                        }
                    ),
                    "value",
                    "group",
                ).result,
            ),
        }
        for identifier, result in replayed.items():
            entry = _entry_by_id(self.catalog, identifier)
            payload = cast(
                dict[str, Any],
                json.loads(json.dumps(result.to_dict(), allow_nan=False)),
            )
            retained = cast(dict[str, Any], entry["payload"])
            with self.subTest(entry=identifier):
                self.assertEqual(type(result).__name__, entry["result_type"])
                self.assertEqual(payload["schema_version"], entry["schema_version"])
                self.assertEqual(payload["analysis"], entry["analysis"])
                self.assertEqual(set(payload), set(retained))
                self._validator(entry).validate(  # pyright: ignore[reportUnknownMemberType]
                    payload
                )


class M7CErrorAndSemanticContractTests(unittest.TestCase):
    def test_stable_coded_error_inventory_matches_literal_implementation(self) -> None:
        manifest = _load_json(MANIFEST_PATH)
        errors = cast(list[dict[str, Any]], manifest["stable_errors"])
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["name"], "M6CMetaError")
        self.assertEqual(errors[0]["stable_attributes"], ["code"])
        self.assertEqual(
            set(cast(list[str], errors[0]["codes"])),
            set(coded_error_values()["M6CMetaError"]),
        )

    def test_invalid_degenerate_resource_and_group_faults_are_atomic(self) -> None:
        with self.assertRaises(M6CMetaError) as too_few:
            _meta_result(5, mode="robust")
        self.assertEqual(
            too_few.exception.code, "robust_meta_requires_at_least_10_studies"
        )

        with self.assertRaises(M6CMetaError) as invalid_limit:
            _meta_result(10, mode="robust", maximum_work=0)
        self.assertEqual(invalid_limit.exception.code, "m6c_meta_invalid_maximum_work")

        with self.assertRaises(ValueError):
            analyze_gghistostats(pl.DataFrame({"value": [1.0, 1.0, 1.0]}), "value")
        with self.assertRaises(ValueError):
            analyze_gghistostats(
                pl.DataFrame({"value": [1.0, 2.0, 3.0]}),
                "value",
                maximum_rows=2,
            )
        with self.assertRaises(ValueError):
            analyze_grouped_gghistostats(
                pl.DataFrame(
                    {
                        "value": [1.0, 2.0, 3.0, 8.0, 8.0],
                        "group": ["valid", "valid", "valid", "invalid", "invalid"],
                    }
                ),
                "value",
                "group",
            )

    def test_semantic_axis_contract_matches_rendered_containers(self) -> None:
        manifest = _load_json(MANIFEST_PATH)
        semantic_axes = cast(list[dict[str, Any]], manifest["semantic_axes"])
        self.assertEqual(len(semantic_axes), 4)

        frame = pl.DataFrame({"value": [1.0, 2.0, 3.0, 4.0, 5.0]})
        plot = gghistostats(frame, "value")
        composed = combine_plots((plot,), columns=1)
        grouped = grouped_gghistostats(
            pl.DataFrame(
                {
                    "value": [1.0, 2.0, 3.0, 2.0, 3.0, 5.0],
                    "group": ["a", "a", "a", "b", "b", "b"],
                }
            ),
            "value",
            "group",
        )
        pie = ggpiestats(
            pl.DataFrame(
                {
                    "x": ["a", "a", "b", "b"],
                    "y": ["u", "v", "u", "v"],
                    "count": [8, 8, 7, 7],
                }
            ),
            "x",
            "y",
            counts="count",
        )
        self.addCleanup(plot.figure.clear)
        self.addCleanup(composed.figure.clear)
        self.addCleanup(pie.figure.clear)
        for item in grouped.plots:
            self.addCleanup(item.figure.clear)

        self.assertEqual(tuple(plot.axes), ("main",))
        self.assertEqual(tuple(composed.axes), ("panel_1",))
        self.assertTrue(all(tuple(item.axes) == ("main",) for item in grouped.plots))
        self.assertEqual(tuple(pie.axes), ("facet_1", "facet_2"))


if __name__ == "__main__":
    unittest.main()
