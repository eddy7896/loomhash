import assert from "node:assert/strict";
import { test } from "node:test";

import { NUM_LANDMARKS, SELECTED_INDICES, VECTOR_DIM, extractFeatureVector } from "./feature_extraction.mjs";

// Deterministic synthetic landmarks -- no randomness, fully reproducible.
function syntheticLandmarks(seedOffset = 0) {
  return Array.from({ length: NUM_LANDMARKS }, (_, i) => ({
    x: Math.sin(i + seedOffset) * 10,
    y: Math.cos(i * 1.3 + seedOffset) * 8,
    z: Math.sin(i * 0.7 + seedOffset) * 5,
  }));
}

function translate(points, dx, dy, dz) {
  return points.map((p) => ({ x: p.x + dx, y: p.y + dy, z: p.z + dz }));
}

function scale(points, k) {
  return points.map((p) => ({ x: p.x * k, y: p.y * k, z: p.z * k }));
}

function rotateZ(points, theta) {
  const cos = Math.cos(theta);
  const sin = Math.sin(theta);
  return points.map((p) => ({
    x: p.x * cos - p.y * sin,
    y: p.x * sin + p.y * cos,
    z: p.z,
  }));
}

function assertVectorsClose(a, b, tolerance = 1e-9) {
  assert.equal(a.length, b.length);
  for (let i = 0; i < a.length; i++) {
    assert.ok(
      Math.abs(a[i] - b[i]) < tolerance,
      `index ${i}: ${a[i]} vs ${b[i]} (diff ${Math.abs(a[i] - b[i])})`,
    );
  }
}

test("SELECTED_INDICES has 128 distinct, in-range, increasing indices", () => {
  assert.equal(SELECTED_INDICES.length, VECTOR_DIM);
  const unique = new Set(SELECTED_INDICES);
  assert.equal(unique.size, VECTOR_DIM, "indices must be distinct");
  for (const idx of SELECTED_INDICES) {
    assert.ok(idx >= 0 && idx < NUM_LANDMARKS, `index ${idx} out of range`);
  }
  for (let i = 1; i < SELECTED_INDICES.length; i++) {
    assert.ok(SELECTED_INDICES[i] > SELECTED_INDICES[i - 1], "indices must be strictly increasing");
  }
});

test("rejects the wrong number of landmarks", () => {
  assert.throws(() => extractFeatureVector(syntheticLandmarks().slice(0, 100)));
});

test("rejects a degenerate (all-coincident) landmark set", () => {
  const same = Array.from({ length: NUM_LANDMARKS }, () => ({ x: 1, y: 2, z: 3 }));
  assert.throws(() => extractFeatureVector(same));
});

test("is deterministic for the same input", () => {
  const landmarks = syntheticLandmarks();
  assert.deepEqual(extractFeatureVector(landmarks), extractFeatureVector(landmarks));
});

test("two different landmark sets produce different vectors", () => {
  const a = extractFeatureVector(syntheticLandmarks(0));
  const b = extractFeatureVector(syntheticLandmarks(1));
  assert.notDeepEqual(a, b);
});

test("is invariant to translation of the whole landmark set", () => {
  const landmarks = syntheticLandmarks();
  const translated = translate(landmarks, 100, -50, 7);
  assertVectorsClose(extractFeatureVector(landmarks), extractFeatureVector(translated));
});

test("is invariant to rotation of the whole landmark set", () => {
  const landmarks = syntheticLandmarks();
  const rotated = rotateZ(landmarks, Math.PI / 3);
  assertVectorsClose(extractFeatureVector(landmarks), extractFeatureVector(rotated));
});

test("is invariant to uniform scaling of the whole landmark set", () => {
  const landmarks = syntheticLandmarks();
  const scaled = scale(landmarks, 2.5);
  assertVectorsClose(extractFeatureVector(landmarks), extractFeatureVector(scaled));
});

test("is invariant to a combined rotate+translate+scale transform", () => {
  const landmarks = syntheticLandmarks();
  const transformed = translate(scale(rotateZ(landmarks, 1.1), 0.4), 3, -9, 12);
  assertVectorsClose(extractFeatureVector(landmarks), extractFeatureVector(transformed), 1e-8);
});
