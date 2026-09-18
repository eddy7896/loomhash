/**
 * Manual test applet wiring: camera -> MediaPipe -> feature vector -> LoomHash API.
 *
 * Not a product UI. See edge/README.md for how to run this. The MediaPipe
 * CDN URLs and model asset URL below are the standard published pattern
 * from MediaPipe's tasks-vision examples; they were not exercised against
 * a live browser while this was written (no browser available in the
 * development environment) -- if FaceLandmarker.createFromOptions() fails
 * to load, check MediaPipe's current docs for an updated model URL.
 */

import { FaceLandmarker, FilesetResolver } from "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision/vision_bundle.mjs";

import { computeAuthenticationVector, computeEnrollmentVector, ENROLLMENT_FRAME_COUNT } from "../capture.mjs";
import { frameFromFaceLandmarkerResult } from "../mediapipe_adapter.mjs";

const API_BASE = "http://127.0.0.1:8000";

const videoEl = document.getElementById("video");
const statusEl = document.getElementById("status");
const userIdEl = document.getElementById("user-id");

let faceLandmarker = null;

function log(message) {
  statusEl.textContent += `${message}\n`;
  console.log(message);
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function initMediaPipe() {
  log("Loading MediaPipe FaceLandmarker (this can take a few seconds)...");
  const vision = await FilesetResolver.forVisionTasks(
    "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision/wasm",
  );
  faceLandmarker = await FaceLandmarker.createFromOptions(vision, {
    baseOptions: {
      modelAssetPath:
        "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
      delegate: "GPU",
    },
    runningMode: "VIDEO",
    numFaces: 1,
  });
  log("FaceLandmarker ready.");
}

async function startCamera() {
  const stream = await navigator.mediaDevices.getUserMedia({ video: true });
  videoEl.srcObject = stream;
  await videoEl.play();
  log("Camera started.");
}

function detectFrame() {
  const result = faceLandmarker.detectForVideo(videoEl, performance.now());
  // Logged so mediapipe_adapter.mjs's field-name assumptions can be checked
  // against what your MediaPipe version actually returns.
  console.log("raw FaceLandmarkerResult:", result);
  return frameFromFaceLandmarkerResult(result);
}

async function captureEnrollmentFrames() {
  const frames = [];
  const intervalMs = 1000 / ENROLLMENT_FRAME_COUNT;
  for (let i = 0; i < ENROLLMENT_FRAME_COUNT; i++) {
    frames.push(detectFrame());
    await sleep(intervalMs);
  }
  return frames;
}

async function postJson(path, body) {
  const resp = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await resp.json().catch(() => ({}));
  return { status: resp.status, data };
}

document.getElementById("init-btn").addEventListener("click", async () => {
  try {
    await initMediaPipe();
    await startCamera();
  } catch (err) {
    log(`Setup failed: ${err.message}`);
  }
});

document.getElementById("enroll-btn").addEventListener("click", async () => {
  const userId = userIdEl.value.trim();
  if (!userId) return log("Enter a user_id first.");
  if (!faceLandmarker) return log("Click 'Start camera + load MediaPipe' first.");

  log("Turn your head slowly for about 1 second...");
  const frames = await captureEnrollmentFrames();
  let vector;
  try {
    vector = computeEnrollmentVector(frames);
  } catch (err) {
    log(`Enrollment vector computation failed: ${err.message}`);
    return;
  }
  const { status, data } = await postJson("/v1/enroll", { user_id: userId, vector });
  log(`POST /v1/enroll -> ${status} ${JSON.stringify(data)}`);
});

document.getElementById("auth-btn").addEventListener("click", async () => {
  const userId = userIdEl.value.trim();
  if (!userId) return log("Enter a user_id first.");
  if (!faceLandmarker) return log("Click 'Start camera + load MediaPipe' first.");

  const frame = detectFrame();
  let vector;
  try {
    vector = computeAuthenticationVector(frame);
  } catch (err) {
    log(`Authentication vector computation failed: ${err.message}`);
    return;
  }
  const { status, data } = await postJson("/v1/authenticate", { user_id: userId, vector });
  log(`POST /v1/authenticate -> ${status} ${JSON.stringify(data)}`);
});

document.getElementById("revoke-btn").addEventListener("click", async () => {
  const userId = userIdEl.value.trim();
  if (!userId) return log("Enter a user_id first.");

  const resp = await fetch(`${API_BASE}/v1/users/${encodeURIComponent(userId)}`, { method: "DELETE" });
  const data = await resp.json().catch(() => ({}));
  log(`DELETE /v1/users/${userId} -> ${resp.status} ${JSON.stringify(data)}`);
});
