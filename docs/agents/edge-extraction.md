# Agent context: Edge Extraction module

Read this before touching any client-side capture/feature code. Also read [../memory-system.md](../memory-system.md)'s session-start protocol first.

## Role

Client-side (Next.js/React + MediaPipe WASM) capture and feature derivation. Converts camera frames into the 128-d rigid-distance vector. Nothing else in the system may do this job — see constraint 4 below.

## I/O contract

- **In:** live camera frames (enrollment: 12 frames across a 1s yaw rotation; authentication: 1 frame).
- **Out:** a 128-dimensional numerical vector, sent to the API. Nothing else biometric leaves the client (no frames, no mesh, no landmark coordinates).

## Immutable constraints that apply here

- **Constraint 4 (Compute Location):** all MediaPipe/mesh/frame processing happens in this module, client-side, only. If you find yourself importing mediapipe, cv2, or any frame-processing library into server code, that's a different module's bug, not something to "helpfully" fix by adding it there.
- **Constraint 3 (Data Privacy):** do not add any code path that uploads, caches, or logs raw frames or the facial mesh — only the final 128-d vector may leave the browser.

## D-01 and D-02 are resolved — implementation exists

Feature definition and frame-averaging policy were approved 2026-09-17 (D-01 was revised mid-implementation — see the note in [../open-decisions.md](../open-decisions.md)). Implemented in [../../edge/](../../edge/):

- `feature_extraction.mjs` — pure math, no MediaPipe dependency: centroid, RMS-radius normalization, 128 deterministic evenly-spaced landmark indices across MediaPipe's 468 canonical (non-iris) landmarks. Unit tested, including proofs that the feature is invariant to any rotation/translation/uniform-scale of the whole landmark set.
- `capture.mjs` — enrollment (12-frame capture, >=8-valid-frame requirement, average the per-frame vectors) and authentication (single-frame, same per-frame pipeline).
- `mediapipe_adapter.mjs` — bridges a real `FaceLandmarkerResult` to the plain `{landmarks}` shape the above two files expect. **This is the one file whose MediaPipe-API-shape assumptions were not verified against a live browser** while writing this (no browser/webcam in the development environment) — see its comments before trusting it blindly.
- `applet/` — a throwaway HTML/JS manual-test page (camera → MediaPipe → vector → LoomHash API), not a product UI. See [../../edge/README.md](../../edge/README.md) for how to run it alongside `python -m loomhash.api`.

Run the unit tests with `node --test edge/` — no `npm install` needed (zero dependencies for the tested core; the applet loads `@mediapipe/tasks-vision` from a CDN at runtime, not via npm).

**Do not reintroduce MediaPipe's `facialTransformationMatrixes` as an alignment step** without a concrete reason — it was deliberately dropped as mathematically redundant for this feature's centroid-relative-distance definition (see the open-decisions.md note) and its exact JS shape was never confirmed.

**Gap:** none of this has been exercised against a real camera or real MediaPipe output. If you get access to a browser, running `edge/applet/` and checking the console-logged raw `FaceLandmarkerResult` against `mediapipe_adapter.mjs`'s assumptions is the highest-value next verification step — see [../verification-checklist.md](../verification-checklist.md)'s ENR-01/ENR-02/AUT-01 rows.

## What is still NOT defined

Real biometric accuracy (genuine/impostor evaluation) — this feature definition is explicitly a prototype-scope pipeline-correctness choice, not a claim of biometric quality. Frame-quality/liveness checks beyond "did MediaPipe detect a face at all" remain deferred (D-07). The actual Next.js/React product UI doesn't exist — only the tested core logic and the manual-test applet do.

## Related requirements / decisions

Requirements: ENR-01, ENR-02, AUT-01. Open decisions: D-01 (resolved), D-02 (resolved), D-07 (deferred for the prototype milestone — see [../use-cases.md](../use-cases.md)).
