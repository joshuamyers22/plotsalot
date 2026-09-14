from __future__ import annotations

import json
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ProjectLicenseTests(unittest.TestCase):
    def test_project_metadata_and_license_file_are_mit(self) -> None:
        metadata = tomllib.loads((ROOT / "pyproject.toml").read_text())
        license_text = (ROOT / "LICENSE").read_text()
        oracle_description = (ROOT / "oracle" / "DESCRIPTION").read_text()
        oracle_license = (ROOT / "oracle" / "LICENSE").read_text()

        self.assertEqual(metadata["project"]["license"], "MIT")
        self.assertTrue(license_text.startswith("MIT License\n"))
        self.assertIn("Copyright (c) 2026 Joshua Myers", license_text)
        self.assertIn("License: MIT + file LICENSE", oracle_description)
        self.assertIn("YEAR: 2026", oracle_license)
        self.assertIn("COPYRIGHT HOLDER: Joshua Myers", oracle_license)

    def test_only_approved_upstream_is_in_product_scope(self) -> None:
        manifest = json.loads(
            (ROOT / "docs" / "upstream" / "manifest.json").read_text()
        )

        self.assertEqual(
            [repository["name"] for repository in manifest["repositories"]],
            ["ggstatsplot"],
        )
