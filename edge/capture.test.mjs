import assert from "node:assert/strict";
import { test } from "node:test";

import {
  InsufficientFramesError,
  MIN_VALID_ENROLLMENT_FRAMES,
  computeAuthenticationVector,
  computeEnrollmentVector,
} from "./capture.mjs";
import { NUM_LANDMARKS, VECTOR_DIM, extractFeatureVector } from "./feature_extraction.mjs";

function syntheticLandmarks(seedOffset = 0) {
  return Array.from({ length: NUM_LANDMARKS }, (_, i) => ({
    x: Math.sin(i + seedOffset) * 10,
    y: Math.cos(i * 1.3 + seedOffset) * 8,
    z: Math.sin(i * 0.7 + seedOffset) * 5,
  }));
}

function assertVectorsClose(a, b, tolerance = 1e-9) {
  assert.equal(a.length, b.length);
  for (let i = 0; i < a.length; i++) {
    assert.ok(Math.abs(a[i] - b[i]) < tolerance, `index ${i}: ${a[i]} vs ${b[i]}`);
  }
}

test("averages exactly the valid frames when all 12 are valid and identical", () => {
  const landmarks = syntheticLandmarks();
  const frame = { landmarks };
  const frames = Array(12).fill(frame);
  const result = computeEnrollmentVector(frames);
  // Summing 12 identical floats then dividing isn't bit-exact with computing
  // once, due to floating-point rounding -- compare with a tolerance instead
  // of deepEqual.
  assertVectorsClose(result, extractFeatureVector(landmarks));
});

test("averages differing valid frames component-wise", () => {
  const vectorA = extractFeatureVector(syntheticLandmarks(0));
  const vectorB = extractFeatureVector(syntheticLandmarks(1));
  const frames = [{ landmarks: syntheticLandmarks(0) }, { landmarks: syntheticLandmarks(1) }, ...Array(6).fill({ landmarks: syntheticLandmarks(0) })];
  // 7 valid frames (below the 8-minimum) should still throw; bump to 8 valid.
  frames.push({ landmarks: syntheticLandmarks(1) });
  const result = computeEnrollmentVector(frames);
  assert.equal(result.length, VECTOR_DIM);
  // Sanity: result should be a real average, not just equal to one input.
  assert.notDeepEqual(result, vectorA);
  assert.notDeepEqual(result, vectorB);
});

test("succeeds at exactly the minimum valid-frame boundary", () => {
  const validFrame = { landmarks: syntheticLandmarks() };
  const frames = [...Array(MIN_VALID_ENROLLMENT_FRAMES).fill(validFrame), null, null, null, null];
  const result = computeEnrollmentVector(frames);
  assert.equal(result.length, VECTOR_DIM);
});

test("throws InsufficientFramesError just below the minimum", () => {
  const validFrame = { landmarks: syntheticLandmarks() };
  const frames = [...Array(MIN_VALID_ENROLLMENT_FRAMES - 1).fill(validFrame), null, null, null, null, null];
  assert.throws(() => computeEnrollmentVector(frames), InsufficientFramesError);
});

test("authentication vector matches extractFeatureVector directly", () => {
  const landmarks = syntheticLandmarks();
  assert.deepEqual(computeAuthenticationVector({ landmarks }), extractFeatureVector(landmarks));
});

test("authentication throws when no face was detected", () => {
  assert.throws(() => computeAuthenticationVector(null));
});
