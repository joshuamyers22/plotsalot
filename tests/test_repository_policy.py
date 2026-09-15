from __future__ import annotations

import json
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
            "docs/API_STABILITY.md",
            "docs/M7_CALIBRATION_PLAN.md",
            "docs/MILESTONE_7.md",
            "docs/README.md",
            "docs/RELEASING.md",
            "docs/USER_GUIDE.md",
            "docs/adr/ADR-007-public-api-schema-stability.md",
            "docs/evidence/M7_VERIFICATION_LOOP.md",
            "docs/m7/compatibility-disposition.json",
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

    def test_m7_compatibility_ledger_covers_pinned_exports(self) -> None:
        ledger = json.loads(
            (ROOT / "docs" / "m7" / "compatibility-disposition.json").read_text(
                encoding="utf-8"
            )
        )
        expected = {
            "combine_plots",
            "extract_caption",
            "extract_stats",
            "extract_subtitle",
            "ggbarstats",
            "ggbetweenstats",
            "ggcoefstats",
            "ggcorrmat",
            "ggdotplotstats",
            "gghistostats",
            "ggpiestats",
            "ggscatterstats",
            "ggwithinstats",
            "grouped_ggbarstats",
            "grouped_ggbetweenstats",
            "grouped_ggcorrmat",
            "grouped_ggdotplotstats",
            "grouped_gghistostats",
            "grouped_ggpiestats",
            "grouped_ggscatterstats",
            "grouped_ggwithinstats",
            "theme_ggstatsplot",
        }
        exports = ledger["exports"]
        self.assertEqual(ledger["status"], "accepted")
        self.assertEqual(
            ledger["approval"],
            {
                "decision": "M7-D1",
                "owner": "Joshua Myers",
                "approved_at": "2026-09-15",
                "scope": "stabilize_existing_adapted_surface",
            },
        )
        names = [item["upstream_export"] for item in exports]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(set(names), expected)
        self.assertEqual(ledger["upstream"]["export_count"], len(expected))

        upstream = json.loads(
            (ROOT / "docs" / "upstream" / "manifest.json").read_text(encoding="utf-8")
        )["repositories"][0]
        self.assertEqual(ledger["upstream"]["name"], upstream["name"])
        self.assertEqual(ledger["upstream"]["revision"], upstream["revision"])
        self.assertEqual(
            ledger["upstream"]["export_count"],
            upstream["inventory"]["exported_symbols"],
        )

        import plotsalot

        public_names = set(plotsalot.__all__)
        ledger_surfaces = {
            surface for item in exports for surface in item["python_surfaces"]
        }
        self.assertEqual(ledger_surfaces - public_names, set())

        gaps = [gap for item in exports for gap in item["gaps"]]
        gap_ids = [gap["id"] for gap in gaps]
        self.assertEqual(len(gap_ids), len(set(gap_ids)))
        allowed = set(ledger["proposal"]["gap_dispositions"])
        self.assertTrue(gaps)
        self.assertTrue(all(gap["proposal"] in allowed for gap in gaps))
        self.assertEqual(
            sum(gap["proposal"] == "post_1_0" for gap in gaps),
            29,
        )
        self.assertEqual(
            sum(gap["proposal"] == "rejected" for gap in gaps),
            19,
        )


if __name__ == "__main__":
    unittest.main()
