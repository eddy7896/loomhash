"""Python port of edge/feature_extraction.mjs's math, for generating training
targets (ground-truth 128-d vectors) from MediaPipe landmarks during offline
label generation. Must stay byte-for-byte equivalent to the JS original --
see test_feature_targets.py, which cross-validates both implementations
against the same synthetic input via a Node subprocess.

This is a training-time-only tool. Importing mediapipe here (see
generate_labels.py) does not violate system.md's constraint 4: constraint 4
governs the production server, not an offline data-preparation script that
never runs as part of the deployed service.
"""

from __future__ import annotations

import numpy as np

NUM_LANDMARKS = 468  # canonical MediaPipe face-mesh landmarks, excluding the 10 iris points
VECTOR_DIM = 128
FEATURE_VERSION = 1  # must match edge/feature_extraction.mjs's FEATURE_VERSION


def _js_round(x: float) -> int:
    """Match JavaScript's Math.round: round half up (floor(x + 0.5)), not
    Python's round() which rounds half to even. i * NUM_LANDMARKS / VECTOR_DIM
    hits exact .5 boundaries for some i (e.g. i=16 -> 58.5), where the two
    behave differently -- this was caught by test_feature_targets.py's
    cross-validation against the real JS implementation (2/128 indices
    disagreed before this fix).
    """
    import math

    return math.floor(x + 0.5)


# Deterministic, evenly-spaced indices across 0..467 -- must match the JS
# SELECTED_INDICES exactly (see the cross-validation test).
SELECTED_INDICES = tuple(_js_round(i * NUM_LANDMARKS / VECTOR_DIM) for i in range(VECTOR_DIM))


def extract_feature_vector(landmarks: np.ndarray) -> np.ndarray:
    """Compute the VECTOR_DIM-length feature vector for one frame.

    landmarks: array of shape (NUM_LANDMARKS, 3) -- (x, y, z) per landmark,
    in whatever coordinate space MediaPipe returns them (this function's
    normalization does not depend on that space's exact meaning).
    """
    landmarks = np.asarray(landmarks, dtype=np.float64)
    if landmarks.shape != (NUM_LANDMARKS, 3):
        raise ValueError(f"expected shape ({NUM_LANDMARKS}, 3), got {landmarks.shape}")

    center = landmarks.mean(axis=0)
    deltas = landmarks - center
    distances = np.linalg.norm(deltas, axis=1)
    radius = float(np.sqrt(np.mean(distances**2)))
    if radius == 0:
        raise ValueError("degenerate landmark set: all points coincide (radius is zero)")

    selected = distances[list(SELECTED_INDICES)]
    return selected / radius
