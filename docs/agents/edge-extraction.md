# Agent context: Edge Extraction module

Read this before touching any client-side capture/feature code. Also read [../memory-system.md](../memory-system.md)'s session-start protocol first.

**Architecture revision, 2026-09-18 (D-13, unresolved):** this module's role changed. It no longer computes the 128-d vector — that moved server-side, into the new Inference module (see [inference.md](inference.md), [../open-decisions.md](../open-decisions.md) D-04/D-08). This module's job now is capture + MediaPipe face-detection/quality-gating + transmitting valid frame images. Everything below describing "Out: a 128-dimensional numerical vector" reflects the still-live, tested, but now-superseded code — it has not been reworked yet, and D-13 (whether to keep, repurpose, or retire it) is unresolved. Do not delete this code or stop maintaining it without that decision; its frame-orchestration/quality-gating logic in `capture.mjs` is still relevant to the new design even though its vector-computation math (`feature_extraction.mjs`) is superseded.

## Role

Client-side (Next.js/React + MediaPipe WASM) capture and face-detection quality-gating. Formerly also computed the 128-d vector; that's now the Inference module's job (server-side) — see the revision note above.

## I/O contract (target, post-D-13; not yet implemented)

- **In:** live camera frames (enrollment: 12 frames across a 1s yaw rotation; authentication: 1 frame).
- **Out:** valid frame images (those where MediaPipe detected a face) transmitted to the server's Inference module — not a pre-computed vector. Nothing else biometric leaves the client (no landmark coordinates, no derived features) — the images themselves are the payload now, which is a real change from the original "only a vector leaves the client" design; see D-04/D-08's resolution for why.

## Immutable constraints that apply here

- **Constraint 4 (Compute Location, revised):** MediaPipe face-detection/quality-gating happens client-side only. Feature-vector computation is no longer this module's job — do not reintroduce the geometric-math vector computation here as if it's still current; the Inference module owns that now.
- **Constraint 3 (Data Privacy, revised):** frame images may be transmitted to the server now (to the Inference module specifically) — that's expected, not a violation. What's still prohibited: caching/logging raw frames client-side beyond what's needed to transmit them, and transmitting anything to any server endpoint other than the Inference module's intended path.

## D-01 and D-02 are resolved (for the superseded design) — implementation exists

Feature definition and frame-averaging policy were approved 2026-09-17 (D-01 was revised mid-implementation — see the note in [../open-decisions.md](../open-decisions.md)). **As of 2026-09-18 this feature-computation approach is superseded by server-side ONNX regression (D-04/D-08)** — the code below still exists, still passes its tests, and its frame-orchestration logic is still relevant, but it is no longer the approved way the 128-d vector gets computed. Implemented in [../../edge/](../../edge/):

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

Requirements: ENR-01, ENR-02, AUT-01. Open decisions: D-01 (resolved, superseded design), D-02 (resolved, superseded design), D-07 (deferred for the prototype milestone — see [../use-cases.md](../use-cases.md)), D-13 (unresolved — disposition of this module's existing code).
