from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RepositoryPolicyTests(unittest.TestCase):
    def test_prepublication_documentation_baseline_exists(self) -> None:
        required = {
            "checklists/REPOSITORY_SETUP.md",
            "checklists/RELEASE_READINESS.md",
            "docs/GETTING_STARTED.md",
            "docs/INTERPRETATION_AND_LIMITATIONS.md",
            "docs/README.md",
            "docs/RELEASING.md",
            "docs/USER_GUIDE.md",
            "src/plotsalot/py.typed",
        }

        missing = sorted(path for path in required if not (ROOT / path).is_file())

        self.assertEqual(missing, [])

    def test_pypi_metadata_uses_canonical_project_identity(self) -> None:
        metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))[
            "project"
        ]

        self.assertEqual(metadata["name"], "plotsalot")
        self.assertEqual(metadata["license"], "MIT")
        self.assertEqual(metadata["license-files"], ["LICENSE"])
        self.assertEqual(metadata["authors"], [{"name": "Joshua Myers"}])
        self.assertIn("Typing :: Typed", metadata["classifiers"])
        self.assertEqual(
            metadata["urls"]["Repository"],
            "https://github.com/joshuamyers22/plotsalot",
        )

    def test_release_assets_are_explicit(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("files: dist/*\n", workflow)
        for artifact in (
            "dist/*.whl",
            "dist/*.tar.gz",
            "dist/release-sbom.cdx.json",
            "dist/SHA256SUMS",
        ):
            with self.subTest(artifact=artifact):
                self.assertIn(artifact, workflow)

    def test_release_uses_trusted_publishing_without_a_long_lived_token(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("publish-pypi:", workflow)
        self.assertIn("name: pypi", workflow)
        self.assertIn("id-token: write", workflow)
        self.assertIn(
            "uv publish --trusted-publishing always dist/*.whl dist/*.tar.gz",
            workflow,
        )
        self.assertNotIn("PYPI_TOKEN", workflow)
        self.assertNotIn("secrets.", workflow)


if __name__ == "__main__":
    unittest.main()
