# Agent context: Inference module

Read this before touching any ONNX Runtime code. Also read [../memory-system.md](../memory-system.md)'s session-start protocol first.

## Role

Server-side, CPU-only ONNX Runtime execution of an INT8-quantized MobileNetV4-backbone regressor. Receives one face image per valid captured frame (not a vector) and outputs a 128-d vector per frame. This is the **only** server-side module permitted to receive raw image data — see system.md's Constraint 3/4 (revised 2026-09-18) and the Privacy model note at the top of system.md.

**This is a real architecture change from how the project started.** Originally (and as this file used to say) the server was vector-only and any server-side image processing was forbidden. That was revised 2026-09-18 after extended discussion with the user about model-weight protection and future retraining needs — see [../open-decisions.md](../open-decisions.md)'s D-04/D-08 resolution for the full reasoning. Don't "fix" this module back toward vector-only input; that would undo an explicit, reasoned decision.

## D-04 is resolved (architecture only) — no code exists yet

The I/O contract is defined and approved:

- **Input:** tensor name `"input"`, shape `[1, 3, 224, 224]`, float32, RGB, normalized with ImageNet mean `[0.485, 0.456, 0.406]` / std `[0.229, 0.224, 0.225]`.
- **Output:** tensor name `"output"`, shape `[1, 128]`, float32 — the 128-d vector, fed directly into [loomhash/cryptography/lsh.py](../../loomhash/cryptography/lsh.py)'s `project()`.
- **Runtime:** `onnxruntime.InferenceSession(path, providers=["CPUExecutionProvider"])`, loaded once at process startup, not per request. `onnxruntime` is the dependency to add — not `torch`/`torchvision`.

**Do not write integration code yet.** The `loom_engine_int8.onnx` model file does not exist — training it is a substantial separate ML project (data collection, training loop, INT8 export), explicitly out of scope for this session. The user was offered the option to build integration plumbing against a placeholder/mock model file and explicitly declined (2026-09-18), choosing to wait for the real artifact. Do not write `onnxruntime.InferenceSession` calls, add `onnxruntime` to pyproject.toml, or fabricate a placeholder .onnx file unless the user asks for that specifically — it was a considered "not yet," not an oversight.

## What else blocks real implementation, even once a model file exists

- **D-12** (unresolved): the API Gateway's `/v1/enroll`/`/v1/authenticate` routes currently accept `{user_id, vector[128]}` — built and tested under the old vector-only architecture. They need to accept image data instead, and the request encoding (multipart, base64-JSON, raw bytes) isn't decided. Don't touch `loomhash/api/schemas.py`/`app.py` for this until D-12 is resolved.
- **D-13** (unresolved): [../../edge/feature_extraction.mjs](../../edge/feature_extraction.mjs) and [../../edge/capture.mjs](../../edge/capture.mjs) implement the now-superseded client-side geometric-math feature computation, with 15 passing tests. Their disposition (keep as fallback, repurpose, retire) isn't decided. Don't delete or stop maintaining them without that decision.

## Immutable constraints that apply here

- **Constraint 2:** Python >= 3.10 runtime environment.
- **Constraint 3 (revised):** raw image data may exist in this module's process memory only for the duration of a single inference request — never logged, cached, or persisted, including by generic error/exception logging or APM middleware that might capture a request body. The one exception is the not-yet-implemented Feature 4 opt-in pipeline (see [../open-decisions.md](../open-decisions.md) D-11) — nothing else may retain image data.
- **Constraint 4 (revised):** this module is the *only* server-side code path allowed to touch raw images. Every other server-side module (API Gateway's non-inference logic, Cryptography, Storage, Compliance) must stay vector/hash/seed-only.

## Related requirements / decisions

No requirement ID currently references this module (requirements.md predates this architecture revision and needs updating). Open decisions: D-04 (resolved, architecture only), D-11 (Feature 4 details, unresolved), D-12 (API request encoding, unresolved, blocking), D-13 (edge/ code disposition, unresolved).
