"""Offline label generation for Stage 1 (distillation) training.

Runs MediaPipe's FaceLandmarker on a directory of face images and computes
the ground-truth 128-d target vector for each, via feature_targets.py (the
verified Python port of edge/feature_extraction.mjs's math). Writes
(image_path, target_vector) pairs to a manifest.

This is a training-time-only, offline data-preparation script. Using
mediapipe here does not violate system.md's constraint 4 (media processing
confined to the client in production) -- constraint 4 governs the deployed
service, not a script that runs once to prepare training data and is never
part of the running LoomHash server or client.

Usage:
    python training/generate_labels.py <image_dir> <output_manifest.jsonl> [--limit N]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions, vision

from feature_targets import NUM_LANDMARKS, extract_feature_vector

MODEL_PATH = Path(__file__).resolve().parent / "models" / "face_landmarker.task"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def build_landmarker() -> vision.FaceLandmarker:
    options = vision.FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(MODEL_PATH)),
        running_mode=vision.RunningMode.IMAGE,
        num_faces=1,
    )
    return vision.FaceLandmarker.create_from_options(options)


def landmarks_to_array(face_landmarks) -> np.ndarray:
    """First NUM_LANDMARKS entries are the canonical face mesh; any beyond
    that (iris refinement) are dropped -- verified against a real
    FaceLandmarker result (478 = 468 canonical + 10 iris, canonical first)
    on 2026-09-18, see STATUS.md."""
    points = face_landmarks[:NUM_LANDMARKS]
    return np.array([[p.x, p.y, p.z] for p in points], dtype=np.float64)


def generate_labels(image_dir: Path, output_path: Path, limit: int | None = None) -> None:
    landmarker = build_landmarker()
    image_paths = sorted(
        p for p in image_dir.rglob("*") if p.suffix.lower() in IMAGE_EXTENSIONS
    )
    if limit is not None:
        image_paths = image_paths[:limit]

    total = len(image_paths)
    written = 0
    skipped_no_face = 0
    skipped_error = 0

    with open(output_path, "w", encoding="utf-8") as out_file:
        for i, image_path in enumerate(image_paths):
            if i % 500 == 0:
                print(f"[{i}/{total}] written={written} no_face={skipped_no_face} error={skipped_error}")

            try:
                image = mp.Image.create_from_file(str(image_path))
                result = landmarker.detect(image)
                if not result.face_landmarks:
                    skipped_no_face += 1
                    continue

                landmarks = landmarks_to_array(result.face_landmarks[0])
                target_vector = extract_feature_vector(landmarks)

                record = {
                    "image_path": str(image_path.relative_to(image_dir)),
                    "target_vector": target_vector.tolist(),
                }
                out_file.write(json.dumps(record) + "\n")
                written += 1
            except Exception as exc:  # noqa: BLE001 -- log and continue, one bad image shouldn't kill the run
                skipped_error += 1
                print(f"  error on {image_path}: {exc}", file=sys.stderr)

    print(f"Done. total={total} written={written} no_face={skipped_no_face} error={skipped_error}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("image_dir", type=Path)
    parser.add_argument("output_manifest", type=Path)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    generate_labels(args.image_dir, args.output_manifest, args.limit)
