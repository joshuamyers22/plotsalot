from __future__ import annotations

import os
import re
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
PYTHON_BLOCK = re.compile(r"^```python\n(.*?)^```$", re.MULTILINE | re.DOTALL)


class DocumentationExampleTests(unittest.TestCase):
    def execute_python_blocks(self, document: Path) -> None:
        blocks = PYTHON_BLOCK.findall(document.read_text(encoding="utf-8"))
        self.assertTrue(blocks, f"{document} has no Python examples")
        namespace: dict[str, Any] = {"__name__": "__documentation__"}
        previous_directory = Path.cwd()
        try:
            with tempfile.TemporaryDirectory() as directory:
                os.chdir(directory)
                for index, block in enumerate(blocks, start=1):
                    with (
                        self.subTest(document=document.name, block=index),
                        redirect_stdout(StringIO()),
                    ):
                        exec(compile(block, document.name, "exec"), namespace)
        finally:
            os.chdir(previous_directory)
            plt.close("all")

    def test_readme_quick_start(self) -> None:
        self.execute_python_blocks(ROOT / "README.md")

    def test_getting_started(self) -> None:
        self.execute_python_blocks(ROOT / "docs" / "GETTING_STARTED.md")


if __name__ == "__main__":
    unittest.main()
