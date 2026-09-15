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
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
MANIFEST = ROOT / "docs" / "m7" / "public-contract.json"
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
    error_codes = _coded_error_values()
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


def _coded_error_values() -> dict[str, list[str]]:
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


def build_manifest() -> dict[str, Any]:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = pyproject["project"]
    symbols, errors = _public_symbols()
    serializable = [
        symbol["name"]
        for symbol in symbols
        if symbol.get("has_to_dict") is True and symbol["kind"] != "protocol"
    ]
    return {
        "manifest_version": 1,
        "status": "m7a_inventory",
        "generated_from": {
            "package": "src/plotsalot/__init__.py",
            "metadata": "pyproject.toml",
            "schemas": "schemas/*.json",
            "cli_parsers": "src/plotsalot/*_cli.py and src/plotsalot/cli.py",
        },
        "distribution": {
            "name": project["name"],
            "version": project["version"],
            "requires_python": project["requires-python"],
        },
        "public_api": {
            "export_count": len(symbols),
            "symbols": symbols,
        },
        "serialized_result_types": serializable,
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


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    rendered = render_manifest()
    if args.write:
        MANIFEST.write_text(rendered, encoding="utf-8")
        print(f"wrote {MANIFEST.relative_to(ROOT)}")
        return 0
    if not MANIFEST.is_file():
        print(f"missing {MANIFEST.relative_to(ROOT)}", file=sys.stderr)
        return 1
    retained = MANIFEST.read_text(encoding="utf-8")
    if retained == rendered:
        print("Public contract manifest is current")
        return 0
    diff = difflib.unified_diff(
        retained.splitlines(),
        rendered.splitlines(),
        fromfile=str(MANIFEST.relative_to(ROOT)),
        tofile="generated public contract",
        lineterm="",
    )
    print("\n".join(diff), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
