"""Cross-validates the Python port (feature_targets.py) against the real JS
implementation (edge/feature_extraction.mjs) that actually ships -- run via
`node training/js_cross_check.mjs <seed_offset>`. If these ever disagree,
the training labels would not match what production edge code (once D-13 is
resolved) or the historical implementation actually computes.
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from feature_targets import NUM_LANDMARKS, SELECTED_INDICES, VECTOR_DIM, _js_round, extract_feature_vector

REPO_ROOT = Path(__file__).resolve().parent.parent


def synthetic_landmarks(seed_offset: float = 0.0) -> np.ndarray:
    i = np.arange(NUM_LANDMARKS)
    x = np.sin(i + seed_offset) * 10
    y = np.cos(i * 1.3 + seed_offset) * 8
    z = np.sin(i * 0.7 + seed_offset) * 5
    return np.stack([x, y, z], axis=1)


def js_feature_vector(seed_offset: float = 0.0) -> list:
    result = subprocess.run(
        ["node", "training/js_cross_check.mjs", str(seed_offset)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


class TestCrossValidation(unittest.TestCase):
    def test_selected_indices_match_js(self):
        # SELECTED_INDICES isn't exposed by js_cross_check.mjs directly, but
        # any mismatch here would show up as a vector mismatch below too --
        # this just narrows down *what* differs if that test ever fails.
        self.assertEqual(len(SELECTED_INDICES), VECTOR_DIM)
        # Uses _js_round, not plain round(), to match JS's Math.round
        # (round-half-up) rather than Python's round-half-to-even -- see
        # feature_targets.py's _js_round docstring for why this matters.
        js_indices = [_js_round(i * NUM_LANDMARKS / VECTOR_DIM) for i in range(VECTOR_DIM)]
        self.assertEqual(list(SELECTED_INDICES), js_indices)

    def test_python_matches_js_seed_0(self):
        py_vector = extract_feature_vector(synthetic_landmarks(0.0))
        js_vector = js_feature_vector(0.0)
        np.testing.assert_allclose(py_vector, js_vector, atol=1e-9)

    def test_python_matches_js_seed_1(self):
        py_vector = extract_feature_vector(synthetic_landmarks(1.0))
        js_vector = js_feature_vector(1.0)
        np.testing.assert_allclose(py_vector, js_vector, atol=1e-9)

    def test_python_matches_js_seed_negative(self):
        py_vector = extract_feature_vector(synthetic_landmarks(-3.5))
        js_vector = js_feature_vector(-3.5)
        np.testing.assert_allclose(py_vector, js_vector, atol=1e-9)


if __name__ == "__main__":
    unittest.main()
