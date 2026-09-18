/**
 * Pure feature-extraction math for the Edge Extraction module.
 *
 * Resolves docs/open-decisions.md D-01, approved 2026-09-17 (revised
 * during implementation -- see the note below and STATUS.md). Operates
 * on plain {x,y,z} landmark data, NOT MediaPipe's result objects directly
 * -- see mediapipe_adapter.mjs for the (browser-unverified) bridge between
 * the two. Keeping this file MediaPipe-shape-agnostic makes it fully
 * unit-testable with synthetic data and isolates any wrong assumption
 * about MediaPipe's exact field names to one small, clearly-flagged file.
 *
 * Feature definition: for each frame, take the 468 canonical (non-iris)
 * face-mesh landmarks, compute their centroid and RMS radius (root-mean-
 * square distance from centroid), then report distance-to-centroid /
 * RMS-radius for 128 deterministic, evenly-spaced landmark indices across
 * the full 0..467 range.
 *
 * This ratio is mathematically invariant to any rotation, translation, or
 * uniform scale applied to the whole landmark set (proven and tested in
 * feature_extraction.test.mjs) -- so no explicit pose-alignment step is
 * needed for THIS property, and the originally-approved plan to apply
 * MediaPipe's facialTransformationMatrixes was dropped as both redundant
 * for a purely rigid transform and dependent on an API shape that
 * couldn't be confirmed from documentation. This does NOT make the
 * feature robust to the perspective distortion a real head rotation
 * introduces in raw image-space landmarks, or to non-rigid expression
 * changes -- pose/expression robustness is explicitly out of scope for
 * this feasibility-prototype milestone (see docs/open-decisions.md).
 * Indices are chosen algorithmically rather than hand-picked anatomical
 * points specifically to avoid asserting unverified semantic identities
 * for MediaPipe's landmark indices from memory.
 */

export const NUM_LANDMARKS = 468; // canonical MediaPipe face-mesh landmarks, excluding the 10 iris points
export const VECTOR_DIM = 128;
export const FEATURE_VERSION = 1;

// Deterministic, evenly-spaced indices across 0..467. Changing this
// selection changes every previously-computed feature vector -- bump
// FEATURE_VERSION and record the change in docs/open-decisions.md.
export const SELECTED_INDICES = Object.freeze(
  Array.from({ length: VECTOR_DIM }, (_, i) => Math.round((i * NUM_LANDMARKS) / VECTOR_DIM)),
);

function distance(a, b) {
  const dx = a.x - b.x;
  const dy = a.y - b.y;
  const dz = a.z - b.z;
  return Math.sqrt(dx * dx + dy * dy + dz * dz);
}

function centroid(points) {
  const sum = points.reduce(
    (acc, p) => ({ x: acc.x + p.x, y: acc.y + p.y, z: acc.z + p.z }),
    { x: 0, y: 0, z: 0 },
  );
  return { x: sum.x / points.length, y: sum.y / points.length, z: sum.z / points.length };
}

function rmsRadius(points, center) {
  const meanSquare = points.reduce((acc, p) => acc + distance(p, center) ** 2, 0) / points.length;
  return Math.sqrt(meanSquare);
}

/**
 * Compute the VECTOR_DIM-length feature vector for one frame.
 *
 * @param {{x:number,y:number,z:number}[]} landmarks - exactly NUM_LANDMARKS
 *   canonical (non-iris) landmarks, in whatever coordinate space MediaPipe
 *   returns them (this function's normalization does not depend on that
 *   space's exact meaning).
 * @returns {number[]} length-VECTOR_DIM array of floats.
 */
export function extractFeatureVector(landmarks) {
  if (landmarks.length !== NUM_LANDMARKS) {
    throw new Error(`expected ${NUM_LANDMARKS} landmarks, got ${landmarks.length}`);
  }

  const center = centroid(landmarks);
  const radius = rmsRadius(landmarks, center);
  if (radius === 0) {
    throw new Error("degenerate landmark set: all points coincide (radius is zero)");
  }

  return SELECTED_INDICES.map((idx) => distance(landmarks[idx], center) / radius);
}
