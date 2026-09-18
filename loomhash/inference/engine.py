"""ONNX Runtime inference engine (Inference module, D-04 resolved 2026-09-18).

Loads loom_engine_int8.onnx once at import time (module-level singleton) and
exposes run_inference(image_bytes) -> np.ndarray, shape (128,).

I/O contract (D-04, docs/open-decisions.md):
  Input tensor  "input"  : [1, 3, 224, 224] float32, RGB,
                            ImageNet-normalized (mean=[0.485,0.456,0.406],
                            std=[0.229,0.224,0.225]).
  Output tensor "output" : [1, 128] float32 -- the 128-d vector fed into
                            loomhash.cryptography.project().

Privacy (Constraint 3, revised 2026-09-18):
  Raw image bytes are decoded and converted to a float array inside
  preprocess(); both are local variables that go out of scope before
  run_inference() returns. Nothing image-shaped is stored as an attribute,
  logged, or passed outside this module. Exception handlers here must NOT
  log exc_info or the exception itself if it might contain image-shaped data
  (in practice a PIL/numpy decode error never does, but the rule is stated
  explicitly so future maintainers don't add a generic logger.exception call
  that might capture a request body).

Do NOT add per-request session creation -- InferenceSession.__init__ is
expensive and does model loading/graph optimisation. The module-level
_SESSION singleton is intentional.
"""

from __future__ import annotations

import pathlib

import numpy as np

try:
    import onnxruntime as ort
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "onnxruntime is required for the Inference module. "
        "Add 'onnxruntime>=1.17' to your environment."
    ) from exc

try:
    from PIL import Image
    import io as _io
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "Pillow is required for the Inference module. "
        "Add 'Pillow>=10.0' to your environment."
    ) from exc

# ---------------------------------------------------------------------------
# Constants — must match the training pipeline (training/colab_train_stage1.ipynb)
# and the agreed I/O contract in docs/open-decisions.md D-04.
# ---------------------------------------------------------------------------
_MODEL_PATH = pathlib.Path(__file__).parent / "models" / "loom_engine_int8.onnx"

_IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
_IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)

_INPUT_SIZE = (224, 224)  # (width, height) for PIL.Image.resize
_INPUT_NAME = "input"
_OUTPUT_NAME = "output"
_VECTOR_DIM = 128

# ---------------------------------------------------------------------------
# Module-level singleton -- loaded once at import, not per request.
# ---------------------------------------------------------------------------
_SESSION: ort.InferenceSession = ort.InferenceSession(
    str(_MODEL_PATH),
    providers=["CPUExecutionProvider"],
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _preprocess(image_bytes: bytes) -> np.ndarray:
    """Decode image bytes → [1, 3, 224, 224] float32 ImageNet-normalised array.

    All intermediate objects (PIL image, numpy arrays) are local to this
    function and collected when it returns -- no image-shaped data escapes.
    """
    img = Image.open(_io.BytesIO(image_bytes)).convert("RGB")
    img = img.resize(_INPUT_SIZE, Image.BILINEAR)

    # HWC uint8  →  CHW float32  →  ImageNet-normalise
    arr = np.asarray(img, dtype=np.float32) / 255.0          # (224, 224, 3)
    arr = (arr - _IMAGENET_MEAN) / _IMAGENET_STD             # (224, 224, 3)
    arr = arr.transpose(2, 0, 1)                              # (3, 224, 224)
    arr = arr[np.newaxis, ...]                                # (1, 3, 224, 224)
    return arr


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_inference(image_bytes: bytes) -> np.ndarray:
    """Run the ONNX regressor on one face image; return a 128-d float64 vector.

    Args:
        image_bytes: Raw bytes of a JPEG, PNG, or any PIL-supported image
                     containing a face. Must be non-empty.

    Returns:
        np.ndarray of shape (128,) and dtype float64. This is the vector
        passed directly into loomhash.cryptography.project().

    Raises:
        ValueError: if image_bytes is empty or cannot be decoded as an image.
        RuntimeError: if the model output has an unexpected shape (indicates a
                      model file mismatch with this code -- check _MODEL_PATH
                      and the D-04 I/O contract).

    Privacy note: image_bytes and all intermediate arrays are local to this
    call. Nothing image-shaped is stored or logged on any code path.
    """
    if not image_bytes:
        raise ValueError("image_bytes must not be empty")

    try:
        input_array = _preprocess(image_bytes)
    except Exception as exc:
        # Re-raise as ValueError so callers get a predictable exception type
        # for a bad image, not a PIL-specific one. Do NOT include image_bytes
        # in the message -- constraint 3.
        raise ValueError(f"could not decode image: {exc}") from exc

    outputs = _SESSION.run([_OUTPUT_NAME], {_INPUT_NAME: input_array})
    vector = outputs[0]  # shape (1, 128)

    if vector.shape != (1, _VECTOR_DIM):
        raise RuntimeError(
            f"model output shape {vector.shape} does not match expected "
            f"(1, {_VECTOR_DIM}) -- check loom_engine_int8.onnx matches D-04 contract"
        )

    return vector[0].astype(np.float64)  # shape (128,), float64 for lsh.project()

