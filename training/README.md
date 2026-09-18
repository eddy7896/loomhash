# Training the Inference module's ONNX model

Resolves the "model doesn't exist yet" gap noted throughout docs/open-decisions.md D-04 and docs/agents/inference.md. This directory does not ship to production -- it produces the `.onnx` file that `loomhash/inference/` (not yet built, see D-12) will eventually load.

## Status: Stage 1 (distillation) only

Two-stage plan, per the 2026-09-18 discussion recorded in STATUS.md:

1. **Stage 1 -- distillation (this directory implements this).** Train the MobileNetV4-backbone regressor to reproduce, directly from a face image, the same 128-d vector that MediaPipe + `edge/feature_extraction.mjs`'s geometric math already computes. No identity labels needed -- any face image works as training data.
2. **Stage 2 -- metric learning (not started).** Fine-tune with triplet/contrastive loss for actual verification accuracy. Needs identity-grouped images (multiple photos per person) with confirmed usage rights for the intended purpose. CelebA has identity annotations (10,177 identities) that could support this, but that specific file is "released upon request for research purposes only" directly from CUHK -- not bundled in the ordinary image/attribute download, and not something this pipeline pulls from a third-party mirror on your behalf even where a mirror happens to expose an identity-like column. Get it yourself first.

## Scope: non-commercial R&D / proof-of-concept only (2026-09-18)

Per explicit direction: this phase is validation/POC, not a commercial release, so CelebA and WIDER FACE's non-commercial-research licenses are usable here. **This is a real, binding boundary, not a formality:** CelebA's license explicitly extends its non-commercial restriction to *derived data* -- meaning `loom_engine_int8.onnx` (and anything fine-tuned from it) produced by this pipeline can only be used for this R&D/validation phase, never shipped in a commercial release. Productionizing later means retraining from scratch on commercially-clear data (FairFace alone, or a properly-licensed replacement for CelebA/WIDER FACE), not continuing from this checkpoint.

## Dataset licensing -- checked, not assumed

Four datasets were originally proposed (FairFace, CelebA, LFW, WIDER FACE). Verified against primary sources before using any of them:

| Dataset | Verdict | Why |
| --- | --- | --- |
| **FairFace** | ✅ Used | CC BY 4.0, commercial use permitted with attribution to Karkkainen & Joo. No identity labels (demographic-attribute dataset) -- Stage 1 only. Safe to use even outside the R&D-only scope above. |
| **CelebA** | ✅ Used, R&D-scope only | "Non-commercial research purposes only," restriction explicitly extends to derived data -- fine for this POC phase per the explicit scope decision above, not for a commercial release. Images used; identity annotations (`celeb_id`, where a mirror happens to expose it) deliberately not used -- see Stage 2 note above. |
| **WIDER FACE** | ⚠️ Optional, R&D-scope only, currently unavailable via `datasets` | CC BY-NC-ND 4.0 (non-commercial, no-derivatives) -- same R&D-only scope would apply if it loads. In practice `CUHK-CSE/wider_face` uses a legacy "loading script" repo format the `datasets` library no longer supports at all (`RuntimeError: Dataset scripts are no longer supported`), and HF's viewer won't auto-convert it to Parquet ("runs arbitrary Python code"). The notebook wraps this in a try/except and continues without it rather than blocking the run -- a real fix means pulling the original zip files from the authors' Google Drive directly (e.g. via `gdown`) and parsing the annotation file yourself; not built. |
| **LFW** | ⚠️ Not used, unverified | A secondary source claimed CC-BY-4.0/commercial-OK, but the primary source (vis-www.cs.umass.edu) was unreachable from the dev environment to confirm, and LFW is flagged in the AIAAIC AI-incident repository for consent concerns (scraped from news photos without biometric-use consent). Get independent/legal confirmation before using it for anything, commercial or not. |

If you add a dataset for Stage 2, verify its actual license the same way -- don't assume a dataset is usable because it's popular or old, and don't assume "non-commercial" datasets are fine outside an explicitly non-commercial phase of the project.

## Files

- `feature_targets.py` -- Python port of `edge/feature_extraction.mjs`'s math. Cross-validated against the real JS implementation in `test_feature_targets.py` (shells out to `node`) -- this caught a real bug (Python's `round()` vs JS's `Math.round()` disagree at exact `.5` boundaries) before it could have silently produced 2/128 wrong label values across the whole training set.
- `generate_labels.py` -- offline batch label generation from a local image directory, using MediaPipe's Python Tasks API. A training-time-only tool; does not run as part of the production service, so it does not violate system.md constraint 4.
- `js_cross_check.mjs` -- small Node helper used only by the Python cross-validation tests.
- `colab_train_stage1.ipynb` -- the actual training pipeline: downloads FairFace + CelebA (+ WIDER FACE if it loads -- currently doesn't, see the table above), generates labels, trains, exports to ONNX, INT8-quantizes, verifies. Built for Google Colab (free GPU, avoids fighting local CUDA/torch version conflicts -- see STATUS.md for what went wrong trying to do this locally). Clones the repo inside the notebook so it trains against the exact committed `feature_targets.py`, not a pasted-in copy that could drift.
- `requirements.txt` -- training-only deps, if you'd rather run locally than in Colab. Not referenced by pyproject.toml; nothing here ships to production.
- `models/` -- gitignored scratch space for downloaded model/test assets (the MediaPipe `.task` file, etc.) -- not committed, regenerated by running the scripts.

## Running it

1. Open `colab_train_stage1.ipynb` in Google Colab.
2. Runtime > Change runtime type > select a GPU.
3. Run cells top to bottom. Start with the default subset sizes (15,000 FairFace + 15,000 CelebA + 5,000 WIDER FACE source images) to confirm the whole pipeline works before scaling up.
4. Download the resulting `loom_engine_int8.onnx` from the last cell.
5. Once you have it: update docs/open-decisions.md D-04 and docs/verification-checklist.md to say a real trained artifact exists (everything currently says it doesn't) **and record that it's R&D/non-commercial-scope only** per the scope note above, and only then start on `loomhash/inference/` (blocked on D-12 -- the API Gateway still needs reworking to carry images).

## What this does NOT do

- Does not train Stage 2 (metric learning) -- CelebA's identity file hasn't been requested/obtained yet.
- Does not claim any biometric accuracy. The cosine-similarity check in the notebook's last cells only confirms INT8 quantization didn't destroy the model's output -- real accuracy needs the consented genuine/impostor evaluation protocol in docs/open-decisions.md's proposed validation sequence.
- Does not wire the resulting model into the actual LoomHash service -- that's `loomhash/inference/`, still unbuilt.
- Does not produce anything usable in a commercial release -- see the scope note above.
