"""Generate and verify the retained M7 public-contract inventory."""

from __future__ import annotations

import argparse
import ast
import dataclasses
import difflib
import hashlib
import importlib
import inspect
import json
import sys
import tomllib
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
MANIFEST = ROOT / "docs" / "m7" / "public-contract.json"
REFERENCE = ROOT / "docs" / "PUBLIC_API_REFERENCE.md"
GOLDEN_RESULTS = ROOT / "docs" / "m7" / "golden-results.json"
EXPERIMENTAL_DISPOSITION = "experimental"
CONTRACT_CATEGORIES: dict[str, dict[str, object]] = {
    "upstream_workflow_surface": {
        "reason": "Approved Python surface for one of the 22 pinned upstream exports.",
        "documentation": [
            "docs/compatibility.md",
            "docs/USER_GUIDE.md",
            "docs/CONTRACTS.md",
        ],
    },
    "shared_analysis_function": {
        "reason": "Shared explicit analysis entry point used by supported renderers.",
        "documentation": ["docs/CONTRACTS.md", "docs/M4_STATISTICAL_METHODS.md"],
    },
    "selector_function": {
        "reason": "Owned validation and data-selection boundary for public workflows.",
        "documentation": ["docs/CONTRACTS.md"],
    },
    "serialized_result": {
        "reason": "Top-level typed result with a versioned JSON-safe representation.",
        "documentation": ["docs/CONTRACTS.md", "schemas/"],
    },
    "result_component": {
        "reason": "Typed field record exposed by a supported public result contract.",
        "documentation": ["docs/CONTRACTS.md", "docs/README.md"],
    },
    "analysis_container": {
        "reason": (
            "Typed analysis/render handoff preserving exact data-result identity."
        ),
        "documentation": ["docs/CONTRACTS.md"],
    },
    "selected_data": {
        "reason": (
            "Typed owned data boundary returned by a public selector or analysis."
        ),
        "documentation": ["docs/CONTRACTS.md"],
    },
    "plot_contract": {
        "reason": "Typed figure, annotations, or local-theme contract for rendering.",
        "documentation": ["docs/CONTRACTS.md", "docs/USER_GUIDE.md"],
    },
    "result_protocol": {
        "reason": "Minimum public structural protocol accepted by plot containers.",
        "documentation": ["docs/CONTRACTS.md"],
    },
    "coded_exception": {
        "reason": "Public exception with machine-readable failure codes.",
        "documentation": [
            "docs/API_STABILITY.md",
            "docs/M6C_STATISTICAL_METHODS.md",
        ],
    },
}
CATEGORY_MEMBERS: dict[str, set[str]] = {
    "shared_analysis_function": {"analyze_categorical"},
    "selector_function": {
        "select_categorical_table",
        "select_coefficients",
        "select_numeric_pair",
        "select_numeric_sample",
        "select_posterior_coefficient_summaries",
        "select_robust_coefficient_summaries",
        "select_study_effects",
    },
    "serialized_result": {
        "AnalysisResult",
        "BayesianCategoricalResult",
        "BayesianComparisonResult",
        "BayesianCorrelationMatrixResult",
        "BayesianCorrelationResult",
        "BayesianDotPlotResult",
        "BayesianMetaResult",
        "BayesianOneSampleResult",
        "CategoricalResult",
        "CoefficientResult",
        "CoefficientTableResult",
        "ComparisonResult",
        "CompositionResult",
        "CorrelationMatrixResult",
        "CorrelationResult",
        "DotPlotResult",
        "GroupedResult",
        "PosteriorCoefficientTableResult",
        "RobustCoefficientTableResult",
        "RobustComparisonResult",
        "RobustCorrelationMatrixResult",
        "RobustCorrelationResult",
        "RobustDotPlotResult",
        "RobustMetaResult",
        "RobustOneSampleResult",
    },
    "result_component": {
        "BayesianEvidenceResult",
        "BayesianMetaEvidenceResult",
        "BayesianMetaFitResult",
        "BayesianMetaPriorResult",
        "BayesianMetaQuadratureResult",
        "BayesianMetaStudyResult",
        "BayesianPosteriorSummary",
        "CategoricalSampleAudit",
        "M6CMetaResourceLimits",
        "M6CWorkResult",
        "MetaAnalysisResult",
        "MetaStudyIdentityResult",
        "PairwiseComparisonResult",
        "PosteriorCoefficientProvenanceResult",
        "PosteriorCoefficientSummaryResult",
        "PosteriorCoefficientTermResult",
        "RepeatedSampleAudit",
        "ResamplingResult",
        "ResourceLimits",
        "RobustCoefficientProvenanceResult",
        "RobustCoefficientTermResult",
        "RobustMetaAnalysisResult",
        "RobustMetaConvergenceResult",
        "RobustMetaPooledResult",
        "RobustMetaStartResult",
        "RobustMetaStudyResult",
        "TrimmedKernelResult",
    },
    "analysis_container": {
        "BayesianMetaAnalysis",
        "CategoricalAnalysis",
        "CoefficientAnalysis",
        "ComparisonAnalysis",
        "CorrelationAnalysis",
        "CorrelationMatrixAnalysis",
        "DotPlotAnalysis",
        "GroupedAnalysis",
        "HistogramAnalysis",
        "ReportedCoefficientAnalysis",
        "RobustMetaAnalysis",
        "TableCoefficientAnalysis",
    },
    "selected_data": {
        "CategoricalTable",
        "CoefficientTable",
        "ComparisonSample",
        "NumericSample",
        "PairedNumericSample",
        "PosteriorCoefficientSummaryTable",
        "RepeatedSample",
        "RobustCoefficientSummaryTable",
        "StudyEffectTable",
    },
    "plot_contract": {
        "ComposedStatsPlot",
        "GroupedStatsPlot",
        "PlotAnnotations",
        "StatsPlot",
        "StatsTheme",
    },
    "result_protocol": {"StructuredResult"},
    "coded_exception": {"M6CMetaError"},
}
CLI_ARTIFACTS: dict[tuple[str, ...], list[dict[str, str]]] = {
    ("plotsalot-regression",): [
        {
            "argument": "--output",
            "format": "json",
            "schema": "quant-regression-evidence/v1",
            "contract": "docs/REGRESSION_EVIDENCE.md",
        }
    ],
    ("plotsalot-validate",): [
        {
            "argument": "--output",
            "format": "json",
            "schema": "quant-time-validation-evidence/v1",
            "contract": "docs/REGRESSION_EVIDENCE.md",
        }
    ],
    ("plotsalot-dataset", "publish"): [
        {
            "argument": "root/dataset-version",
            "format": "partitioned_parquet_with_json_manifest",
            "schema": "quant-parquet-dataset-manifest/v1",
            "contract": "docs/PARQUET_DATASETS.md",
        }
    ],
}

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _qualified_name(value: object) -> str:
    module = getattr(value, "__module__", None)
    name = getattr(value, "__qualname__", getattr(value, "__name__", None))
    if module and name:
        return f"{module}.{name}"
    return type(value).__name__


def _json_default(value: object) -> object:
    if value is argparse.SUPPRESS:
        return "SUPPRESS"
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"unsupported public CLI default: {value!r}")


def _argument_contract(action: argparse.Action) -> dict[str, Any]:
    option_strings = list(action.option_strings)
    positional = not option_strings
    required = bool(action.required)
    if positional and action.nargs not in ("?", "*"):
        required = True
    contract: dict[str, Any] = {
        "name": action.dest,
        "kind": "positional" if positional else "option",
        "spellings": option_strings,
        "required": required,
        "nargs": "one" if action.nargs is None else action.nargs,
        "value_type": "text" if action.type is None else _qualified_name(action.type),
    }
    if action.choices is not None:
        contract["choices"] = sorted(action.choices, key=str)
    if not required:
        contract["default"] = _json_default(action.default)
    return contract


def _parser_commands(
    parser: argparse.ArgumentParser, path: tuple[str, ...]
) -> list[dict[str, Any]]:
    arguments: list[dict[str, Any]] = []
    children: list[tuple[str, argparse.ArgumentParser]] = []
    for action in parser._actions:
        if isinstance(action, argparse._HelpAction):
            continue
        if isinstance(action, argparse._SubParsersAction):
            arguments.append(_argument_contract(action))
            children.extend(sorted(action.choices.items()))
            continue
        arguments.append(_argument_contract(action))

    commands = [
        {
            "path": list(path),
            "arguments": arguments,
            "exit_status": {
                "success": 0,
                "usage_error": 2,
                "operation_error": "nonzero",
            },
            "stdout": "human_readable_text",
            "artifacts": CLI_ARTIFACTS.get(path, []),
        }
    ]
    for name, child in children:
        commands.extend(_parser_commands(child, (*path, name)))
    return commands


def _console_scripts(project: Mapping[str, Any]) -> list[dict[str, Any]]:
    scripts = project.get("scripts", {})
    if not isinstance(scripts, dict):
        raise ValueError("[project.scripts] must be a table")
    contracts: list[dict[str, Any]] = []
    for name, target in sorted(scripts.items()):
        if not isinstance(target, str) or ":" not in target:
            raise ValueError(f"invalid console-script target for {name!r}")
        module_name, attribute_name = target.split(":", 1)
        module = importlib.import_module(module_name)
        entrypoint = getattr(module, attribute_name, None)
        if not callable(entrypoint):
            raise ValueError(f"console-script target {target!r} is not callable")
        builder = getattr(module, "_build_parser", None)
        if builder is None:
            raise ValueError(
                f"console-script module {module_name!r} has no _build_parser"
            )
        parser = builder()
        if not isinstance(parser, argparse.ArgumentParser):
            raise TypeError(f"{module_name}._build_parser did not return a parser")
        if parser.prog != name:
            raise ValueError(
                f"console script {name!r} uses parser prog {parser.prog!r}"
            )
        contracts.append(
            {
                "name": name,
                "target": target,
                "entrypoint_signature": str(inspect.signature(entrypoint)),
                "commands": _parser_commands(parser, (name,)),
            }
        )
    return contracts


def _public_symbols() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    package = importlib.import_module("plotsalot")
    exported = list(package.__all__)
    if len(exported) != len(set(exported)):
        raise ValueError("plotsalot.__all__ contains duplicate names")

    symbols: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    error_codes = coded_error_values()
    for name in sorted(exported):
        value = getattr(package, name)
        if inspect.isclass(value) and issubclass(value, BaseException):
            kind = "exception"
        elif inspect.isclass(value) and getattr(value, "_is_protocol", False):
            kind = "protocol"
        elif inspect.isclass(value):
            kind = "class"
        elif inspect.isfunction(value):
            kind = "function"
        else:
            kind = "value"
        symbol: dict[str, Any] = {
            "name": name,
            "kind": kind,
            "defined_in": value.__module__,
        }
        if callable(value):
            symbol["signature"] = str(inspect.signature(value))
        if inspect.isclass(value) and dataclasses.is_dataclass(value):
            symbol["dataclass_fields"] = [
                field.name for field in dataclasses.fields(value)
            ]
        if inspect.isclass(value):
            symbol["has_to_dict"] = callable(getattr(value, "to_dict", None))
        symbols.append(symbol)

        if kind == "exception":
            annotations = getattr(value, "__annotations__", {})
            error: dict[str, Any] = {
                "name": name,
                "base": _qualified_name(value.__base__),
                "stable_attributes": sorted(annotations),
            }
            if name in error_codes:
                error["codes"] = error_codes[name]
            errors.append(error)
    return symbols, errors


def _upstream_workflow_surfaces() -> set[str]:
    ledger_path = ROOT / "docs" / "m7" / "compatibility-disposition.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    return {
        surface for item in ledger["exports"] for surface in item["python_surfaces"]
    }


def _experimental_features() -> list[dict[str, Any]]:
    ledger_path = ROOT / "docs" / "m7" / "compatibility-disposition.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    features = ledger.get("one_zero_feature_exceptions")
    if not isinstance(features, list) or not features:
        raise ValueError("compatibility ledger requires feature exceptions")
    if any(
        not isinstance(feature, dict)
        or feature.get("disposition") != EXPERIMENTAL_DISPOSITION
        for feature in features
    ):
        raise ValueError("unsupported 1.x feature exception disposition")
    return features


def _experimental_public_names() -> set[str]:
    names = [
        name
        for feature in _experimental_features()
        for name in feature.get("dedicated_public_types", [])
    ]
    if len(names) != len(set(names)):
        raise ValueError("experimental public names must be unique")
    return set(names)


def _contract_category(symbol: Mapping[str, Any], workflow: set[str]) -> str:
    name = symbol["name"]
    if name in workflow:
        return "upstream_workflow_surface"
    matches = [
        category for category, members in CATEGORY_MEMBERS.items() if name in members
    ]
    if len(matches) != 1:
        raise ValueError(
            f"public symbol {name!r} requires exactly one explicit 1.x category; "
            f"found {matches}"
        )
    return matches[0]


def _classify_symbols(
    symbols: list[dict[str, Any]],
) -> tuple[dict[str, int], dict[str, int]]:
    workflow = _upstream_workflow_surfaces()
    public_names = {symbol["name"] for symbol in symbols}
    if missing := workflow - public_names:
        raise ValueError(
            f"compatibility ledger has non-public surfaces: {sorted(missing)}"
        )
    declared = set().union(*CATEGORY_MEMBERS.values())
    if overlap := workflow & declared:
        raise ValueError(
            f"workflow surfaces have duplicate categories: {sorted(overlap)}"
        )
    if missing := declared - public_names:
        raise ValueError(f"classified names are not public: {sorted(missing)}")
    experimental = _experimental_public_names()
    if missing := experimental - public_names:
        raise ValueError(f"experimental names are not public: {sorted(missing)}")
    expected_categories = set(CONTRACT_CATEGORIES) - {"upstream_workflow_surface"}
    if set(CATEGORY_MEMBERS) != expected_categories:
        raise ValueError("explicit category membership tables are incomplete")
    counts: Counter[str] = Counter()
    disposition_counts: Counter[str] = Counter()
    for symbol in symbols:
        category = _contract_category(symbol, workflow)
        disposition = (
            EXPERIMENTAL_DISPOSITION if symbol["name"] in experimental else "stabilize"
        )
        symbol["one_x_disposition"] = disposition
        symbol["contract_category"] = category
        counts[category] += 1
        disposition_counts[disposition] += 1
    if set(counts) != set(CONTRACT_CATEGORIES):
        missing = sorted(set(CONTRACT_CATEGORIES) - set(counts))
        extra = sorted(set(counts) - set(CONTRACT_CATEGORIES))
        raise ValueError(
            f"contract category mismatch: missing={missing}, extra={extra}"
        )
    return dict(sorted(counts.items())), dict(sorted(disposition_counts.items()))


def coded_error_values() -> dict[str, list[str]]:
    values: dict[str, set[str]] = {}
    for path in sorted((SRC / "plotsalot").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not node.args:
                continue
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr
            else:
                continue
            first = node.args[0]
            if (
                name.endswith("Error")
                and isinstance(first, ast.Constant)
                and isinstance(first.value, str)
                and "_" in first.value
            ):
                values.setdefault(name, set()).add(first.value)
    return {name: sorted(codes) for name, codes in sorted(values.items())}


def _walk_json(value: object) -> Iterable[Mapping[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_json(child)


def _schema_variants(schema: Mapping[str, Any]) -> list[dict[str, Any]]:
    variants: set[tuple[int | str, str]] = set()
    for node in _walk_json(schema):
        properties = node.get("properties")
        if not isinstance(properties, dict):
            continue
        version_node = properties.get("schema_version")
        analysis_node = properties.get("analysis")
        if not isinstance(version_node, dict) or not isinstance(analysis_node, dict):
            continue
        version = version_node.get("const")
        analyses: Sequence[object]
        if "const" in analysis_node:
            analyses = (analysis_node["const"],)
        else:
            enum = analysis_node.get("enum", ())
            analyses = enum if isinstance(enum, list) else ()
        if not isinstance(version, (int, str)):
            continue
        for analysis in analyses:
            if isinstance(analysis, str):
                variants.add((version, analysis))
    return [
        {"schema_version": version, "analysis": analysis}
        for version, analysis in sorted(
            variants, key=lambda item: (str(item[0]), item[1])
        )
    ]


def _schemas() -> list[dict[str, Any]]:
    contracts: list[dict[str, Any]] = []
    for path in sorted((ROOT / "schemas").glob("*.json")):
        raw = path.read_bytes()
        schema = json.loads(raw)
        contracts.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "role": "serialized_result"
                if "-result." in path.name
                else "operational",
                "id": schema.get("$id"),
                "title": schema.get("title"),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "variants": _schema_variants(schema),
            }
        )
    return contracts


def _golden_results() -> dict[str, Any]:
    raw = GOLDEN_RESULTS.read_bytes()
    catalog = json.loads(raw)
    entries = catalog.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ValueError("M7C golden corpus requires retained entries")
    identifiers = [entry.get("id") for entry in entries if isinstance(entry, dict)]
    if len(identifiers) != len(entries) or len(set(identifiers)) != len(entries):
        raise ValueError("M7C golden entry identifiers must be complete and unique")
    discriminators = {
        (entry["schema"], entry["schema_version"], entry["analysis"])
        for entry in entries
    }
    stability_counts = Counter(entry["stability"] for entry in entries)
    return {
        "path": GOLDEN_RESULTS.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "entry_count": len(entries),
        "result_type_count": len({entry["result_type"] for entry in entries}),
        "discriminator_count": len(discriminators),
        "stability_counts": dict(sorted(stability_counts.items())),
    }


def build_manifest() -> dict[str, Any]:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = pyproject["project"]
    symbols, errors = _public_symbols()
    category_counts, disposition_counts = _classify_symbols(symbols)
    serializable = [
        symbol["name"]
        for symbol in symbols
        if symbol.get("has_to_dict") is True and symbol["kind"] != "protocol"
    ]
    return {
        "manifest_version": 1,
        "status": "m7c_hardening_complete",
        "generated_from": {
            "package": "src/plotsalot/__init__.py",
            "metadata": "pyproject.toml",
            "schemas": "schemas/*.json",
            "cli_parsers": "src/plotsalot/*_cli.py and src/plotsalot/cli.py",
            "compatibility_scope": "docs/m7/compatibility-disposition.json",
            "golden_results": "docs/m7/golden-results.json",
        },
        "distribution": {
            "name": project["name"],
            "version": project["version"],
            "requires_python": project["requires-python"],
        },
        "public_api": {
            "export_count": len(symbols),
            "one_x_candidate": "retain_all_root_exports_with_experimental_robust_meta",
            "breaking_changes_from_0_1_1": [],
            "category_counts": category_counts,
            "disposition_counts": disposition_counts,
            "categories": CONTRACT_CATEGORIES,
            "symbols": symbols,
        },
        "experimental_features": _experimental_features(),
        "serialized_result_types": serializable,
        "stable_serialized_result_types": [
            name for name in serializable if name not in _experimental_public_names()
        ],
        "experimental_serialized_result_types": [
            name for name in serializable if name in _experimental_public_names()
        ],
        "golden_results": _golden_results(),
        "schemas": _schemas(),
        "console_scripts": _console_scripts(project),
        "semantic_axes": [
            {
                "container": "StatsPlot",
                "key": "main",
                "cardinality": "exactly_one_for_non_faceted_renderers",
            },
            {
                "container": "StatsPlot",
                "key_pattern": "facet_{one_based_index}",
                "cardinality": "one_per_categorical_pie_facet",
            },
            {
                "container": "ComposedStatsPlot",
                "key_pattern": "panel_{one_based_index}",
                "cardinality": "one_per_source_plot",
            },
            {
                "container": "GroupedStatsPlot",
                "key_contract": "each_member_plot_uses_its_renderer_contract",
            },
        ],
        "stable_errors": errors,
    }


def render_manifest() -> str:
    return json.dumps(build_manifest(), indent=2, ensure_ascii=False) + "\n"


def render_reference(manifest: Mapping[str, Any]) -> str:
    public_api = manifest["public_api"]
    symbols = public_api["symbols"]
    grouped = {
        category: [
            symbol for symbol in symbols if symbol["contract_category"] == category
        ]
        for category in CONTRACT_CATEGORIES
    }
    lines = [
        "# Public API Reference",
        "",
        "- Status: M7C API/schema hardening complete on 2026-09-15",
        "- Machine source: [`m7/public-contract.json`](m7/public-contract.json)",
        "- Stability policy: [`API_STABILITY.md`](API_STABILITY.md)",
        "",
        "This reference classifies every name exported through `plotsalot.__all__`.",
        "The 1.x candidate retains all 144 names already shipped in `0.1.1`; M7A",
        "found no accidental wildcard, leading-underscore, test, benchmark, or oracle",
        "export. Exact signatures and dataclass fields are retained in the machine",
        "manifest and checked by `make public-contract`.",
        "",
        "Internal defining modules are review metadata, not alternate supported import",
        "paths. The stable import form is `from plotsalot import <name>`. Human-",
        "readable error prose, undocumented object internals, and exact rendered",
        "pixels remain outside the compatibility promise.",
        "",
        "## Classification summary",
        "",
        "| Category | Count | Rationale |",
        "|---|---:|---|",
    ]
    for category, details in CONTRACT_CATEGORIES.items():
        lines.append(
            f"| `{category}` | {len(grouped[category])} | {details['reason']} |"
        )
    lines.extend(["", "## Classified names", ""])
    for category, details in CONTRACT_CATEGORIES.items():
        lines.extend(
            [
                f"### `{category}`",
                "",
                str(details["reason"]),
                "",
                "Normative documentation: "
                + ", ".join(f"`{path}`" for path in details["documentation"])
                + ".",
                "",
                ", ".join(
                    f"`{symbol['name']}`"
                    + (
                        " *(experimental)*"
                        if symbol["one_x_disposition"] == EXPERIMENTAL_DISPOSITION
                        else ""
                    )
                    for symbol in grouped[category]
                )
                + ".",
                "",
            ]
        )
    lines.extend(
        [
            "## Experimental 1.0 exception",
            "",
            "The fixed-Student-t4 robust aggregate meta-analysis selected with",
            '`meta_analytic_effect=True, type="robust"` remains available but is',
            "experimental for 1.0. Its seven dedicated `RobustMeta*` names are",
            "marked above. The containing `ggcoefstats`, `analyze_ggcoefstats`, and",
            "`render_ggcoefstats` callables remain stable for their supported",
            "non-experimental modes; the robust-meta method meaning and serialized",
            "variant are excluded from the 1.x compatibility promise.",
            "",
            "## Review and migration rule",
            "",
            "The retained manifest marks 137 names `stabilize` and seven dedicated",
            "robust-meta names `experimental`. All 144 `0.1.1` names remain importable",
            "and no removal or rename is introduced. This classification does not",
            "independently approve the final 1.0 candidate. M7C retains 51 golden",
            "examples across all 25 result types and 49 schema/discriminator triples,",
            "with mutation, refusal, migration-replay, and semantic-axis tests.",
            "M7D platform/package gates and final owner acceptance remain required.",
            "",
        ]
    )
    return "\n".join(lines)


def _check_retained(path: Path, rendered: str, label: str) -> bool:
    if not path.is_file():
        print(f"missing {path.relative_to(ROOT)}", file=sys.stderr)
        return False
    retained = path.read_text(encoding="utf-8")
    if retained == rendered:
        return True
    diff = difflib.unified_diff(
        retained.splitlines(),
        rendered.splitlines(),
        fromfile=str(path.relative_to(ROOT)),
        tofile=label,
        lineterm="",
    )
    print("\n".join(diff), file=sys.stderr)
    return False


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    manifest = build_manifest()
    rendered = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    reference = render_reference(manifest)
    if args.write:
        MANIFEST.write_text(rendered, encoding="utf-8")
        REFERENCE.write_text(reference, encoding="utf-8")
        print(f"wrote {MANIFEST.relative_to(ROOT)}")
        print(f"wrote {REFERENCE.relative_to(ROOT)}")
        return 0
    manifest_current = _check_retained(MANIFEST, rendered, "generated public contract")
    reference_current = _check_retained(
        REFERENCE, reference, "generated public API reference"
    )
    if manifest_current and reference_current:
        print("Public contract manifest is current")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
