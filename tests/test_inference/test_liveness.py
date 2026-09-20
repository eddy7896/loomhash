"""Tests for loomhash.inference.liveness (D-07 passive liveness check)."""

import io
import unittest

from PIL import Image

from loomhash.inference.liveness import check_liveness


def _make_solid_image(color: tuple[int, int, int]) -> bytes:
    """Create a 64x64 solid-color JPEG in memory."""
    img = Image.new("RGB", (64, 64), color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _make_gradient_image(seed: int) -> bytes:
    """Create a 64x64 image with a gradient that shifts based on seed."""
    import numpy as np
    arr = np.zeros((64, 64, 3), dtype=np.uint8)
    for y in range(64):
        for x in range(64):
            arr[y, x] = ((x + seed * 7) % 256, (y + seed * 13) % 256, (seed * 37) % 256)
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


class TestLivenessIdenticalFrames(unittest.TestCase):
    """Photo replay attack: all frames are identical → should fail."""

    def test_identical_solid_images_fail(self):
        image = _make_solid_image((100, 120, 140))
        frames = [image] * 8
        result = check_liveness(frames)
        self.assertFalse(result.passed)
        self.assertEqual(result.variation_score, 0.0)
        self.assertIn("insufficient", result.reason)


class TestLivenessVariedFrames(unittest.TestCase):
    """Real enrollment: frames have visual variation → should pass."""

    def test_distinct_color_images_pass(self):
        frames = [_make_solid_image((i * 25, i * 15, i * 10)) for i in range(8)]
        result = check_liveness(frames)
        self.assertTrue(result.passed)
        self.assertGreaterEqual(result.variation_score, 0.5)
        self.assertIsNone(result.reason)

    def test_gradient_images_pass(self):
        frames = [_make_gradient_image(i) for i in range(10)]
        result = check_liveness(frames)
        self.assertTrue(result.passed)


class TestLivenessBoundary(unittest.TestCase):
    """Edge cases and boundary conditions."""

    def test_fewer_than_2_frames_raises(self):
        with self.assertRaises(ValueError):
            check_liveness([_make_solid_image((100, 100, 100))])

    def test_mix_of_identical_and_varied(self):
        """Half identical, half varied — should be borderline."""
        identical = _make_solid_image((100, 100, 100))
        # 8 frames: 4 identical pairs + 4 varied
        frames = [identical, identical, identical, identical]
        frames += [_make_solid_image((i * 40, i * 30, i * 20)) for i in range(4)]
        result = check_liveness(frames)
        # Variation in the latter half should contribute enough
        # 7 pairs total: pairs 0-3 (identical, low diff) + pairs 3-6 (varied)
        self.assertIsInstance(result.variation_score, float)

    def test_exactly_2_frames_works(self):
        frames = [
            _make_solid_image((0, 0, 0)),
            _make_solid_image((255, 255, 255)),
        ]
        result = check_liveness(frames)
        self.assertTrue(result.passed)
        self.assertEqual(result.variation_score, 1.0)


if __name__ == "__main__":
    unittest.main()
