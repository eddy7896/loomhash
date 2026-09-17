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

## What is NOT yet defined — do not invent it

Per [../open-decisions.md](../open-decisions.md) D-01 and D-02, the following have no approved definition. Do not guess a value and ship it as if final; propose it as an explicit, labeled proposal instead:

- Which cranial landmark pairs make up the 128 distances, their coordinate system, and normalization/scale.
- Pose registration across the 12 enrollment frames (averaging method, rejected-frame/quality policy, yaw coverage check).
- Whether/how a single authentication frame's feature vector is made comparable to the multi-frame enrollment average.

## Related requirements / decisions

Requirements: ENR-01, ENR-02, AUT-01. Open decisions: D-01, D-02, D-07 (deferred for the prototype milestone — see [../use-cases.md](../use-cases.md)).
