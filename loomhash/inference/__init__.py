"""Inference module — server-side ONNX Runtime execution.

This is the **only** server-side module permitted to receive raw image data
(system.md Constraint 3/4, revised 2026-09-18). Raw image bytes exist only
within a single call to run_inference(); they are never logged, cached,
persisted, or propagated to any other module. The caller receives only the
128-d float64 vector.

Public API: run_inference(image_bytes) -> np.ndarray, shape (128,)
"""

from .engine import run_inference

__all__ = ["run_inference"]

