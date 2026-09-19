/**
 * Manual test applet wiring: camera -> image frames -> LoomHash API.
 *
 * This reflects the D-04/D-12 Server-Side Inference architecture where the
 * edge device just captures JPEGs and POSTs them via multipart/form-data.
 * The old MediaPipe edge extraction has been superseded.
 */

const API_BASE = "http://127.0.0.1:8000";

const videoEl = document.getElementById("video");
const statusEl = document.getElementById("status");
const userIdEl = document.getElementById("user-id");
const canvasEl = document.createElement("canvas");
const ctx = canvasEl.getContext("2d");

const ENROLLMENT_FRAME_COUNT = 12;

function log(message) {
  statusEl.textContent += `${message}\n`;
  console.log(message);
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function startCamera() {
  log("Requesting camera access...");
  const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" } });
  videoEl.srcObject = stream;
  await videoEl.play();
  
  canvasEl.width = videoEl.videoWidth;
  canvasEl.height = videoEl.videoHeight;
  log("Camera started.");
}

// Captures a frame from the video element and returns a Blob (JPEG)
function captureJpegBlob() {
  return new Promise((resolve) => {
    ctx.drawImage(videoEl, 0, 0, canvasEl.width, canvasEl.height);
    canvasEl.toBlob((blob) => resolve(blob), "image/jpeg", 0.9);
  });
}

async function captureEnrollmentImages() {
  const blobs = [];
  const intervalMs = 1000 / ENROLLMENT_FRAME_COUNT;
  for (let i = 0; i < ENROLLMENT_FRAME_COUNT; i++) {
    blobs.push(await captureJpegBlob());
    await sleep(intervalMs);
  }
  return blobs;
}

document.getElementById("init-btn").addEventListener("click", async () => {
  try {
    await startCamera();
  } catch (err) {
    log(`Setup failed: ${err.message}`);
  }
});

document.getElementById("enroll-btn").addEventListener("click", async () => {
  const userId = userIdEl.value.trim();
  if (!userId) return log("Enter a user_id first.");
  if (!videoEl.srcObject) return log("Click 'Start camera' first.");

  log("Turn your head slowly for about 1 second...");
  const blobs = await captureEnrollmentImages();
  
  const formData = new FormData();
  formData.append("user_id", userId);
  blobs.forEach((blob, i) => formData.append("images", blob, `frame_${i}.jpg`));

  log("Uploading frames to API (this will process on the server)...");
  try {
    const resp = await fetch(`${API_BASE}/v1/enroll`, {
      method: "POST",
      body: formData,
    });
    const data = await resp.json().catch(() => ({}));
    log(`POST /v1/enroll -> ${resp.status} ${JSON.stringify(data)}`);
  } catch (err) {
    log(`Fetch failed: ${err.message}`);
  }
});

document.getElementById("auth-btn").addEventListener("click", async () => {
  const userId = userIdEl.value.trim();
  if (!userId) return log("Enter a user_id first.");
  if (!videoEl.srcObject) return log("Click 'Start camera' first.");

  log("Capturing authentication frame...");
  const blob = await captureJpegBlob();
  
  const formData = new FormData();
  formData.append("user_id", userId);
  formData.append("image", blob, "auth.jpg");

  try {
    const resp = await fetch(`${API_BASE}/v1/authenticate`, {
      method: "POST",
      body: formData,
    });
    const data = await resp.json().catch(() => ({}));
    log(`POST /v1/authenticate -> ${resp.status} ${JSON.stringify(data)}`);
  } catch (err) {
    log(`Fetch failed: ${err.message}`);
  }
});

document.getElementById("revoke-btn").addEventListener("click", async () => {
  const userId = userIdEl.value.trim();
  if (!userId) return log("Enter a user_id first.");

  try {
    const resp = await fetch(`${API_BASE}/v1/users/${encodeURIComponent(userId)}`, { method: "DELETE" });
    const data = await resp.json().catch(() => ({}));
    log(`DELETE /v1/users/${userId} -> ${resp.status} ${JSON.stringify(data)}`);
  } catch (err) {
    log(`Fetch failed: ${err.message}`);
  }
});
