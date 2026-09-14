from __future__ import annotations

import unittest

from tools.verify_benchmark import verify_benchmark
from tools.verify_oracle import verify_oracle


class M0ArtifactTests(unittest.TestCase):
    def test_retained_oracle_matches_python_and_hash_manifest(self) -> None:
        verify_oracle()

    def test_retained_benchmark_has_required_grid_and_samples(self) -> None:
        verify_benchmark()
