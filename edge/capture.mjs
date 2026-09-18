/**
 * Enrollment/authentication frame-aggregation logic.
 *
 * Resolves docs/open-decisions.md D-02, approved 2026-09-17. This module
 * does not call MediaPipe itself -- it takes an array of already-adapted
 * per-frame results (see mediapipe_adapter.mjs) and applies the pipeline's
 * frame-quality and averaging policy.
 *
 * Since extractFeatureVector's normalization is applied identically and
 * independently per frame, averaging the resulting VECTOR_DIM-length
 * vectors (not the raw landmark positions) is what makes a 12-frame
 * enrollment directly comparable to a 1-frame authentication attempt --
 * both go through the exact same per-frame pipeline.
 */

import { extractFeatureVector, VECTOR_DIM } from "./feature_extraction.mjs";

export const ENROLLMENT_FRAME_COUNT = 12;
export const MIN_VALID_ENROLLMENT_FRAMES = 8;

export class InsufficientFramesError extends Error {
  constructor(validCount, requiredCount) {
    super(`only ${validCount} of ${requiredCount} required frames had a detected face`);
    this.name = "InsufficientFramesError";
    this.validCount = validCount;
    this.requiredCount = requiredCount;
  }
}

/**
 * @param {({landmarks: {x:number,y:number,z:number}[]} | null)[]} frames -
 *   one entry per captured frame; null means MediaPipe detected no face in
 *   that frame.
 * @returns {number[]} the averaged VECTOR_DIM-length enrollment vector.
 * @throws {InsufficientFramesError} if fewer than MIN_VALID_ENROLLMENT_FRAMES
 *   frames had a detected face.
 */
export function computeEnrollmentVector(frames) {
  const validVectors = frames
    .filter((frame) => frame !== null)
    .map((frame) => extractFeatureVector(frame.landmarks));

  if (validVectors.length < MIN_VALID_ENROLLMENT_FRAMES) {
    throw new InsufficientFramesError(validVectors.length, MIN_VALID_ENROLLMENT_FRAMES);
  }

  const sum = new Array(VECTOR_DIM).fill(0);
  for (const vector of validVectors) {
    for (let i = 0; i < VECTOR_DIM; i++) sum[i] += vector[i];
  }
  return sum.map((total) => total / validVectors.length);
}

/**
 * @param {{landmarks: {x:number,y:number,z:number}[]} | null} frame
 * @returns {number[]} the VECTOR_DIM-length authentication vector.
 * @throws if frame is null (no face detected).
 */
export function computeAuthenticationVector(frame) {
  if (frame === null) {
    throw new Error("no face detected in the authentication frame");
  }
  return extractFeatureVector(frame.landmarks);
}
