"""Tests for loomhash.inference.engine (Inference module, D-04).

These tests run against the real loom_engine_int8.onnx model artifact -- they
are integration tests in the sense that they require the model file to exist at
loomhash/inference/models/loom_engine_int8.onnx.  They do NOT test biometric
accuracy (that requires the separate consented evaluation protocol described in
docs/open-decisions.md); they test that the module loads correctly, produces
the right output shape/dtype, and rejects bad inputs cleanly.
"""

import io
import unittest

import numpy as np
from PIL import Image

from loomhash.inference import run_inference
from loomhash.inference.engine import _VECTOR_DIM


def _make_jpeg(width: int = 224, height: int = 224, color: tuple = (128, 100, 80)) -> bytes:
    """Return minimal in-memory JPEG bytes -- no disk I/O."""
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _make_png(width: int = 64, height: int = 64) -> bytes:
    img = Image.new("RGB", (width, height), color=(200, 150, 100))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestRunInference(unittest.TestCase):

    def test_output_shape(self):
        """run_inference returns a 1-D array of length VECTOR_DIM."""
        vec = run_inference(_make_jpeg())
        self.assertEqual(vec.shape, (_VECTOR_DIM,))

    def test_output_dtype_float64(self):
        """Output dtype is float64 (as required by lsh.project())."""
        vec = run_inference(_make_jpeg())
        self.assertEqual(vec.dtype, np.float64)

    def test_deterministic(self):
        """Same image bytes → identical output vector."""
        img = _make_jpeg(color=(10, 20, 30))
        v1 = run_inference(img)
        v2 = run_inference(img)
        np.testing.assert_array_equal(v1, v2)

    def test_different_images_give_different_vectors(self):
        """Two different solid-colour images produce different vectors."""
        v1 = run_inference(_make_jpeg(color=(10, 20, 30)))
        v2 = run_inference(_make_jpeg(color=(200, 180, 160)))
        self.assertFalse(np.array_equal(v1, v2))

    def test_accepts_png(self):
        """PNG images are accepted (PIL converts to RGB before inference)."""
        vec = run_inference(_make_png())
        self.assertEqual(vec.shape, (_VECTOR_DIM,))

    def test_accepts_non_square_image(self):
        """Non-square images are accepted (resized to 224x224 internally)."""
        vec = run_inference(_make_jpeg(width=320, height=240))
        self.assertEqual(vec.shape, (_VECTOR_DIM,))

    def test_empty_bytes_raises_value_error(self):
        """Empty bytes → ValueError (not a cryptic PIL or numpy crash)."""
        with self.assertRaises(ValueError):
            run_inference(b"")

    def test_invalid_bytes_raises_value_error(self):
        """Random non-image bytes → ValueError."""
        with self.assertRaises(ValueError):
            run_inference(b"\x00\x01\x02\x03garbage data that is not a valid image")

    def test_output_finite(self):
        """Output vector must be all-finite (no NaN / Inf from quantized model)."""
        vec = run_inference(_make_jpeg())
        self.assertTrue(np.all(np.isfinite(vec)), "Vector contains NaN or Inf")


if __name__ == "__main__":
    unittest.main()

