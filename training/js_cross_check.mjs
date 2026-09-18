// Outputs the JS feature_extraction.mjs's result for the same synthetic
// landmarks used in its own test suite, as JSON on stdout. Used by
// test_feature_targets.py to cross-validate the Python port against the
// real JS implementation that edge/ actually ships.
import { extractFeatureVector, NUM_LANDMARKS } from "../edge/feature_extraction.mjs";

function syntheticLandmarks(seedOffset = 0) {
  return Array.from({ length: NUM_LANDMARKS }, (_, i) => ({
    x: Math.sin(i + seedOffset) * 10,
    y: Math.cos(i * 1.3 + seedOffset) * 8,
    z: Math.sin(i * 0.7 + seedOffset) * 5,
  }));
}

const seedOffset = Number(process.argv[2] ?? 0);
const vector = extractFeatureVector(syntheticLandmarks(seedOffset));
process.stdout.write(JSON.stringify(vector));
