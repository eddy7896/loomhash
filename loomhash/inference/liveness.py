"""Server-side passive liveness verification for enrollment frames (D-07).

Analyzes the 8-12 enrollment images for sufficient visual variation across
consecutive frames to detect trivial replay attacks: a stack of identical
photos, a static printout, or a single-frame video loop.

**What this catches:**
  - Photo replay (all frames identical → 0% variation)
  - Static-face video replay (very low inter-frame variation)
  - Single printed photo held up to camera (identical frames)

**What this does NOT catch (deferred per D-07):**
  - High-quality video deepfakes with natural head motion
  - 3D-printed or silicone masks
  - Screen replay of a video with genuine head rotation

Privacy: All image data is local to the function call. No image data is
stored, logged, or transmitted on any code path.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

import numpy as np
from PIL import Image

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Minimum mean absolute pixel-difference between consecutive frame-pairs
# for a pair to be considered "different". Normalized to [0, 255].
_MIN_PAIR_DIFFERENCE = 2.0

# Fraction of consecutive frame-pairs that must exceed _MIN_PAIR_DIFFERENCE
# for the liveness check to pass.
_MIN_VARIATION_RATIO = 0.50

# Center-crop ratio for comparison — ignore edges where camera distortion or
# alignment shifts add noise.
_CROP_RATIO = 0.6

# Resize frames to this small resolution before comparison (speed, not quality).
_CMP_SIZE = (64, 64)


@dataclass(frozen=True)
class LivenessResult:
    """Result of a liveness check on enrollment frames."""

    passed: bool
    variation_score: float  # fraction of frame-pairs with sufficient variation
    reason: str | None  # human-readable failure reason, None if passed


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def check_liveness(image_bytes_list: list[bytes]) -> LivenessResult:
    """Analyze enrollment frames for sufficient inter-frame variation.

    Args:
        image_bytes_list: Raw bytes for each enrollment image (8-12 frames).

    Returns:
        LivenessResult with pass/fail, the computed variation score, and a
        human-readable reason on failure.

    Raises:
        ValueError: if fewer than 2 frames are provided (need at least one
                    pair to compare).
    """
    if len(image_bytes_list) < 2:
        raise ValueError("liveness check requires at least 2 frames")

    # Decode, resize, center-crop, and convert to numpy arrays
    frames = []
    for raw in image_bytes_list:
        try:
            frames.append(_prepare_frame(raw))
        except Exception:
            # If an image can't be decoded, skip it — the inference step will
            # catch and report the specific bad image with its index.
            continue

    if len(frames) < 2:
        # Not enough decodable frames to compare
        return LivenessResult(
            passed=False,
            variation_score=0.0,
            reason="fewer than 2 frames could be decoded for liveness analysis",
        )

    # Compute pairwise mean absolute differences
    n_pairs = len(frames) - 1
    varying_pairs = 0
    for i in range(n_pairs):
        diff = np.mean(np.abs(frames[i].astype(np.float32) - frames[i + 1].astype(np.float32)))
        if diff >= _MIN_PAIR_DIFFERENCE:
            varying_pairs += 1

    variation_score = varying_pairs / n_pairs

    if variation_score < _MIN_VARIATION_RATIO:
        return LivenessResult(
            passed=False,
            variation_score=variation_score,
            reason=(
                f"insufficient inter-frame variation: {variation_score:.0%} of frame pairs "
                f"show visual change (minimum {_MIN_VARIATION_RATIO:.0%} required). "
                f"This may indicate a photo replay or static-face attack."
            ),
        )

    return LivenessResult(passed=True, variation_score=variation_score, reason=None)


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------


def _prepare_frame(image_bytes: bytes) -> np.ndarray:
    """Decode → resize → center-crop → uint8 numpy array."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = img.resize(_CMP_SIZE, Image.BILINEAR)

    arr = np.asarray(img, dtype=np.uint8)  # (H, W, 3)

    # Center crop
    h, w = arr.shape[:2]
    ch = int(h * _CROP_RATIO)
    cw = int(w * _CROP_RATIO)
    y0 = (h - ch) // 2
    x0 = (w - cw) // 2
    return arr[y0 : y0 + ch, x0 : x0 + cw]
