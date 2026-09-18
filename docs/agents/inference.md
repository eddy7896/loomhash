# Agent context: Inference module

Read this before touching any ONNX Runtime code. Also read [../memory-system.md](../memory-system.md)'s session-start protocol first.

## Role

Server-side, CPU-only ONNX Runtime execution of an INT8-quantized MobileNetV4-backbone regressor. Receives one face image per valid captured frame (not a vector) and outputs a 128-d vector per frame. This is the **only** server-side module permitted to receive raw image data — see system.md's Constraint 3/4 (revised 2026-09-18) and the Privacy model note at the top of system.md.

**This is a real architecture change from how the project started.** Originally (and as this file used to say) the server was vector-only and any server-side image processing was forbidden. That was revised 2026-09-18 after extended discussion with the user about model-weight protection and future retraining needs — see [../open-decisions.md](../open-decisions.md)'s D-04/D-08 resolution for the full reasoning. Don't "fix" this module back toward vector-only input; that would undo an explicit, reasoned decision.

## D-04 is fully implemented

The I/O contract is defined and wired in `loomhash/inference/engine.py`:

- **Input:** tensor name `"input"`, shape `[1, 3, 224, 224]`, float32, RGB, normalized with ImageNet mean `[0.485, 0.456, 0.406]` / std `[0.229, 0.224, 0.225]`.
- **Output:** tensor name `"output"`, shape `[1, 128]`, float32 — the 128-d vector, fed directly into [loomhash/cryptography/lsh.py](../../loomhash/cryptography/lsh.py)'s `project()`.
- **Runtime:** `onnxruntime.InferenceSession(_MODEL_PATH, providers=["CPUExecutionProvider"])`, loaded once at process startup, not per request.
- **Model file:** `loom_engine_int8.onnx` is located at `loomhash/inference/models/`.

## What blocks further work

- **D-11** (unresolved): The Feature 4 opt-in pipeline (retraining loop) is undefined. Do not implement retention for model improvement yet.

## Immutable constraints that apply here

- **Constraint 2:** Python >= 3.10 runtime environment.
- **Constraint 3 (revised):** raw image data may exist in this module's process memory only for the duration of a single inference request — never logged, cached, or persisted, including by generic error/exception logging or APM middleware that might capture a request body. The one exception is the not-yet-implemented Feature 4 opt-in pipeline (see [../open-decisions.md](../open-decisions.md) D-11) — nothing else may retain image data.
- **Constraint 4 (revised):** this module is the *only* server-side code path allowed to touch raw images. Every other server-side module (API Gateway's non-inference logic, Cryptography, Storage, Compliance) must stay vector/hash/seed-only.

## Related requirements / decisions

No requirement ID currently references this module (requirements.md predates this architecture revision and needs updating). Open decisions: D-04 (resolved, architecture only), D-11 (Feature 4 details, unresolved), D-12 (API request encoding, unresolved, blocking), D-13 (edge/ code disposition, unresolved).
