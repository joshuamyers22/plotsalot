"""Verify the exact plotsalot wheel and source distribution contents."""

from __future__ import annotations

import hashlib
import tarfile
import tomllib
import zipfile
from email.parser import BytesParser
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
EXPECTED_SCRIPTS = {
    "plotsalot": "plotsalot.cli:main",
    "plotsalot-dataset": "plotsalot.dataset_cli:main",
    "plotsalot-regression": "plotsalot.analysis_cli:main",
    "plotsalot-validate": "plotsalot.time_validation_cli:main",
}
FORBIDDEN_PARTS = {
    ".git",
    ".DS_Store",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo", ".pem", ".key"}
MACHINE_PATH_MARKERS = (
    b"/" + b"Users/",
    b"C:" + b"\\Users\\",
    b"/home/" + b"runner/work/",
)


def _project() -> tuple[str, str, str]:
    document = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = document["project"]
    return project["name"], project["version"], project["requires-python"]


def _members_are_safe(names: list[str]) -> None:
    for name in names:
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"unsafe archive member: {name}")
        if FORBIDDEN_PARTS.intersection(path.parts):
            raise ValueError(f"development residue in archive: {name}")
        if path.suffix in FORBIDDEN_SUFFIXES or path.name.startswith(".env"):
            raise ValueError(f"sensitive or generated file in archive: {name}")


def _verify_wheel(path: Path, name: str, version: str, requires_python: str) -> None:
    dist_info = f"{name.replace('-', '_')}-{version}.dist-info"
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError(f"corrupt wheel member in {path.name}")
        members = archive.namelist()
        _members_are_safe(members)
        expected_runtime = {
            source.relative_to(ROOT / "src").as_posix()
            for source in (ROOT / "src" / "plotsalot").glob("*")
            if source.is_file()
        }
        missing_runtime = expected_runtime.difference(members)
        if missing_runtime:
            raise ValueError(f"wheel omits runtime files: {sorted(missing_runtime)}")
        forbidden_roots = {"tests", "tools", "oracle", "benchmarks", "docs"}
        leaked = [
            item for item in members if PurePosixPath(item).parts[0] in forbidden_roots
        ]
        if leaked:
            raise ValueError(f"wheel includes development files: {leaked}")
        metadata = BytesParser().parsebytes(archive.read(f"{dist_info}/METADATA"))
        expected_metadata = {
            "Name": name,
            "Version": version,
            "Requires-Python": requires_python,
            "License-Expression": "MIT",
        }
        for field, expected in expected_metadata.items():
            if metadata[field] != expected:
                raise ValueError(
                    f"wheel metadata {field} is {metadata[field]!r}, "
                    f"expected {expected!r}"
                )
        body = archive.read(f"{dist_info}/METADATA")
        if b"# plotsalot" not in body:
            raise ValueError("wheel metadata omits the README description")
        entries = archive.read(f"{dist_info}/entry_points.txt").decode("utf-8")
        expected_entries = "\n".join(
            ["[console_scripts]"]
            + [f"{key} = {value}" for key, value in sorted(EXPECTED_SCRIPTS.items())]
            + [""]
        )
        if entries != expected_entries:
            raise ValueError(
                "wheel console entry points do not match the public contract"
            )
        if f"{dist_info}/licenses/LICENSE" not in members:
            raise ValueError("wheel omits the MIT license")
        for member in members:
            content = archive.read(member)
            if any(marker in content for marker in MACHINE_PATH_MARKERS):
                raise ValueError(f"wheel contains a machine-specific path in {member}")


def _verify_sdist(path: Path, name: str, version: str) -> None:
    prefix = f"{name}-{version}"
    with tarfile.open(path, "r:gz") as archive:
        members = archive.getmembers()
        names = [member.name for member in members]
        _members_are_safe(names)
        required = {
            f"{prefix}/LICENSE",
            f"{prefix}/README.md",
            f"{prefix}/pyproject.toml",
            f"{prefix}/src/plotsalot/__init__.py",
            f"{prefix}/src/plotsalot/py.typed",
        }
        missing = required.difference(names)
        if missing:
            raise ValueError(f"sdist omits required files: {sorted(missing)}")
        for member in members:
            if not member.isfile():
                continue
            extracted = archive.extractfile(member)
            if extracted is None:
                raise ValueError(f"unable to inspect sdist member: {member.name}")
            content = extracted.read()
            if any(marker in content for marker in MACHINE_PATH_MARKERS):
                raise ValueError(
                    f"sdist contains a machine-specific path in {member.name}"
                )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    name, version, requires_python = _project()
    wheels = sorted(DIST.glob("*.whl"))
    sdists = sorted(DIST.glob("*.tar.gz"))
    expected_wheel = f"{name.replace('-', '_')}-{version}-py3-none-any.whl"
    expected_sdist = f"{name}-{version}.tar.gz"
    if [path.name for path in wheels] != [expected_wheel]:
        raise ValueError(
            f"expected only {expected_wheel}, found {[p.name for p in wheels]}"
        )
    if [path.name for path in sdists] != [expected_sdist]:
        raise ValueError(
            f"expected only {expected_sdist}, found {[p.name for p in sdists]}"
        )
    _verify_wheel(wheels[0], name, version, requires_python)
    _verify_sdist(sdists[0], name, version)
    for artifact in (wheels[0], sdists[0]):
        print(f"{_sha256(artifact)}  {artifact.name}")
    print("release artifact contents and metadata verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
