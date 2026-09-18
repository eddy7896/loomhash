/**
 * Thin bridge from a real MediaPipe FaceLandmarkerResult (@mediapipe/tasks-
 * vision) to the plain {landmarks} shape feature_extraction.mjs and
 * capture.mjs expect.
 *
 * This is the ONE place in the Edge Extraction module where MediaPipe's
 * actual JS API shape matters, and it was NOT confirmed against a live
 * browser session while writing this -- the official docs fetched while
 * designing this module didn't expose the exact JS-side field names.
 * applet/main.mjs logs the raw result to the browser console specifically
 * so this adapter's assumptions can be checked against ground truth. If
 * result.faceLandmarks turns out to be named differently, or landmarks use
 * different field names than x/y/z, fix it here -- feature_extraction.mjs
 * and capture.mjs don't need to change.
 */

import { NUM_LANDMARKS } from "./feature_extraction.mjs";

/**
 * @param {*} result - the object returned by FaceLandmarker.detectForVideo()/detect().
 * @returns {{landmarks: {x:number,y:number,z:number}[]} | null} null if no
 *   face was detected in this frame.
 */
export function frameFromFaceLandmarkerResult(result) {
  const faces = result?.faceLandmarks;
  if (!faces || faces.length === 0) {
    return null;
  }

  const raw = faces[0];
  let landmarks;
  if (raw.length === NUM_LANDMARKS) {
    landmarks = raw;
  } else if (raw.length > NUM_LANDMARKS) {
    // Assumes the canonical NUM_LANDMARKS landmarks come first and any
    // extra ones (e.g. the 10 iris-refinement points some configurations
    // add) are appended after. Verify this against the applet's console
    // output (it prints raw.length) for your MediaPipe version.
    landmarks = raw.slice(0, NUM_LANDMARKS);
  } else {
    throw new Error(
      `expected at least ${NUM_LANDMARKS} landmarks, got ${raw.length} -- ` +
        "MediaPipe's output shape may differ from what this adapter assumes; " +
        "check the console-logged raw result.",
    );
  }

  return { landmarks: landmarks.map((p) => ({ x: p.x, y: p.y, z: p.z })) };
}
