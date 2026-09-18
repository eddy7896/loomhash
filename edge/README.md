# Edge Extraction module

Resolves docs/open-decisions.md D-01 (the 128-d feature definition) and
D-02 (enrollment frame averaging). See docs/agents/edge-extraction.md for
the full agent-facing context and constraints.

## Layout

- `feature_extraction.mjs` — pure math (no MediaPipe dependency): centroid,
  RMS-radius normalization, deterministic 128-index selection. Fully unit
  tested, including proofs that the feature vector is invariant to any
  rotation/translation/uniform-scale applied to the whole landmark set.
- `capture.mjs` — enrollment (12-frame, >=8-valid averaging) and
  authentication (single-frame) orchestration on top of
  `feature_extraction.mjs`.
- `mediapipe_adapter.mjs` — the one place MediaPipe's actual JS API shape
  matters. Not verified against a live browser session while writing this
  (no browser available in the development environment) — see its comments.
- `*.test.mjs` — run with `node --test edge/` (Node's built-in test runner,
  no dependencies needed).
- `applet/` — a throwaway HTML/JS page to manually verify the whole
  pipeline (camera → MediaPipe → feature vector → LoomHash API) in a real
  browser. Not a product UI.

## Running the unit tests

```sh
node --test edge/
```

No `npm install` needed — zero dependencies for the tested core.

## Running the manual test applet

You need two things running at once:

1. **The LoomHash API**, with dev CORS enabled:
   ```sh
   python -m loomhash.api
   ```
   This serves on `http://127.0.0.1:8000` using the non-durable
   `InMemoryStorageBackend` — data resets every time you restart it.

2. **A static server for the applet** (plain `file://` won't reliably get
   camera permission in most browsers):
   ```sh
   cd edge/applet
   python -m http.server 5500
   ```
   Then open `http://localhost:5500` in your browser.

Click "Start camera + load MediaPipe", allow camera access, then try
Enroll → Authenticate → Revoke. **Open the browser console too** — every
detected frame logs MediaPipe's raw result object, so you can check
`mediapipe_adapter.mjs`'s field-name assumptions (`faceLandmarks`, `x`/`y`/`z`,
landmark count) against what your actual MediaPipe version returns, and fix
the adapter if they don't match. `feature_extraction.mjs` and `capture.mjs`
don't need to change even if the adapter does.

## What's NOT verified yet

This was built and unit-tested without access to a browser or webcam in
the development environment. The MediaPipe integration itself (CDN loading,
model asset URL, `FaceLandmarker.createFromOptions()`, `detectForVideo()`,
and the adapter's assumptions about the result shape) has not been run
against a live browser. Treat the applet as the first real test of that —
see docs/verification-checklist.md for exact status per requirement.
