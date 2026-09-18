# System Context: LoomHash

**Project Name:** LoomHash (Self-Hosted Privacy-Preserving Biometric Microservice)
**Mission:** Provide enterprise-grade, deepfake-resistant 3D facial authentication via a self-hosted, privacy-preserving architecture.

**Privacy model (revised 2026-09-18 — see docs/open-decisions.md D-08):** This system is **not** zero-knowledge in the formal sense — the server's Inference module does receive raw face image data. The privacy property actually provided is **ephemeral, no-persistence processing**: raw image data exists only in server process memory for the duration of a single inference request, is never written to disk, cache, or logs, and is discarded immediately after the 128-d vector is extracted — except for enrollments where the user/developer has explicitly opted into the separate model-improvement data pipeline (Feature 4). Do not describe this system as "zero-knowledge" in new documentation, marketing copy, or code comments; that term was inaccurate for this design and its use was corrected on this date.

## 1. Core Development Methodologies

### Ask, Do Not Assume
All AI agents (OpenAI, Gemini, Claude, Cursor, etc.) contributing to this codebase must adhere strictly to the "Ask, Do Not Assume" protocol:
* If a technical implementation detail is ambiguous, pause and prompt the user for clarification.
* Do not introduce new third-party libraries or external dependencies without explicit user consent.
* Do not infer database schemas or API routes outside of the defined Feature Set Documentation. 

### Modular Architecture
The project must maintain strict decoupling of concerns. AI agents must isolate logic into the following independent modules:
* **Edge Extraction Module:** Client-side WASM for camera capture, MediaPipe-based face detection/quality gating (reject frames with no detected face), and transmission of valid frame images to the server. Does **not** compute the 128-d vector itself (revised 2026-09-18 — see below).
* **Cryptography Module:** Pure Python LSH projection and XOR matching logic.
* **Inference Module:** Server-side ONNX Runtime neural regressor. Receives raw face image data (one image per valid captured frame) and outputs a 128-d vector per frame. The only module permitted to receive raw image data; must process it ephemerally only (see the Privacy model note above) and never persist it, except via the opt-in path in Feature 4.
* **Storage Module:** Redis and PostgreSQL database adapters.
* **Compliance Module:** Event listeners for crypto-shredding and DPDP/GDPR consent revocation.

## 2. Agent Directives and Hallucination Checks

Before outputting code, agents must run an internal hallucination check against these immutable constraints:
* **Constraint 1 (No Vector DBs for Identity):** Ensure no code imports or utilizes Milvus, Pinecone, or FAISS for matching user identities. Matching must only use Locality-Sensitive Hashing and native bitwise XOR.
* **Constraint 2 (Python Version):** Ensure code targets Python 3.10 or higher. The `int.bit_count()` method is mandatory for hardware-accelerated Hamming distance checks.
* **Constraint 3 (Data Privacy — revised 2026-09-18):** Verify that no endpoint, cache, or log writes raw image data (.jpg, .png, arrays) to disk under the default enrollment/authentication flow. Raw image data may exist in server process memory only within the Inference module, only for the duration of a single inference request, and must never be logged, cached, or persisted there — including by generic error handlers, APM/tracing middleware, or exception logging that might capture a request body. The **only** exception is data explicitly retained through the separate, clearly-distinct opt-in model-improvement pipeline (Feature 4), which requires its own explicit consent and is never part of the default flow. All other modules (API Gateway routing logic, Cryptography, Storage, Compliance) still only ever handle 128-d float vectors, 256-bit hashes, seeds, and identifiers — never raw image data.
* **Constraint 4 (Compute Location — revised 2026-09-18):** Client-side MediaPipe performs face detection and frame quality-gating (reject frames with no detected face) before any network transmission. The server's Inference module is the sole server-side component permitted to receive raw image data (one image per valid captured frame) and is responsible for converting it to the 128-d vector; every other server-side module (API Gateway's routing/validation logic outside the inference call, Cryptography, Storage, Compliance) must only ever handle numerical vectors, hashes, seeds, and identifiers.

## 3. System Architecture

The infrastructure operates as a hybrid edge-cloud pipeline.

* **Edge Client:** Next.js / React, MediaPipe WASM (face detection/quality-gating only — see Modular Architecture above).
* **Inference Engine:** Server-side ONNX Runtime (INT8 Quantized MobileNetV4 / ConvNeXt) strictly running on CPU. Loaded once at process startup, not per request. Weights stay server-side (self-hosted by the integrating developer) — not shipped to clients, unlike a browser/WASM inference approach, specifically to keep the trained model proprietary and to support future retraining without redistributing weights.
* **API Gateway:** FastAPI, Uvicorn, Caddy Reverse Proxy.
* **Cache and Persistence:** Redis for hot key lookups, PostgreSQL for persistent storage.
* **Math and Crypto Core:** Native Python `numpy` for seeded LSH projection, native `int.bit_count()` for scoring.

## 4. Feature Set Documentation

### Core Data Structures
* **128-d Rigid Vector:** Output of the server-side Inference module's ONNX regressor for one face image (revised 2026-09-18 — previously defined as client-computed Euclidean distances between fixed cranial points; that computation is superseded, not deleted — see docs/open-decisions.md D-04 for the disposition of the prior client-side implementation).
* **Cryptographic Seed (32-byte):** A random salt generated per user, stored off-chain in PostgreSQL/Redis.
* **256-bit LoomHash:** The final binarized string resulting from the seeded LSH projection.

### Feature 1: Enrollment Pipeline (revised 2026-09-18 — see docs/open-decisions.md D-04)
1. Client captures 12 multi-view frames spanning a 1-second yaw rotation.
2. Client runs MediaPipe face detection per frame; frames with no detected face are rejected client-side (never transmitted). At least 8 of the 12 frames must have a detected face or enrollment fails client-side.
3. Network transmits the valid frame images (not a pre-computed vector) to the API.
4. Server's Inference module runs the ONNX regressor on each valid frame image, ephemerally (see Constraint 3), producing one 128-d vector per frame; these are discarded from memory immediately after use except via the Feature 4 opt-in path.
5. Server averages the per-frame vectors into a single 128-d enrollment vector.
6. Server generates a random cryptographic seed.
7. Server projects the vector using the seed via LSH to create a 256-bit loom_hash.
8. Server saves the (user_id, seed, loom_hash) tuple to the database.

### Feature 2: Authentication Pipeline (revised 2026-09-18 — see docs/open-decisions.md D-04)
1. Client captures a single frame; MediaPipe confirms a face is detected before transmission.
2. Network transmits the frame image (not a pre-computed vector) to the API.
3. Server's Inference module runs the ONNX regressor on the image, ephemerally, producing the 128-d query vector; discarded from memory immediately after use except via the Feature 4 opt-in path.
4. Server retrieves the seed and loom_hash from Redis/Postgres.
5. Server projects the query vector using the stored seed to create a query_hash.
6. Server calculates Hamming distance: distance = (stored_hash ^ query_hash).bit_count() / 256.0
7. Gateway evaluates logic: If distance is <= 0.20, return 200 OK. Else, return 401 Unauthorized.

### Feature 3: Crypto-Shredding (DPDP 2026 and GDPR)
* To comply with the DPDP Act 2026 (Purpose Limitation) and GDPR (Right to Erasure) while allowing immutable Web3 hash anchoring, the system utilizes Crypto-Shredding.
* If a user revokes consent, the system executes a DELETE query dropping the user's cryptographic seed from PostgreSQL/Redis.
* Result: Without the seed, the 256-bit hash becomes mathematically untraceable, converting pseudonymous data into fully anonymized data.

### Feature 4: Opt-In Model-Improvement Data Pipeline (added 2026-09-18 — design only, not yet implemented)
* Purpose: the Inference module's ONNX regressor needs real training/retraining data to improve accuracy and adapt to how a user's face changes over time (aging, seasonal appearance changes). Ephemeral processing (Constraint 3) means the default flow retains nothing to train on — this feature is the only sanctioned way real usage data may be retained.
* Strictly opt-in and strictly separate from the default enrollment/authentication flow in Features 1-2: a user (or the integrating developer, on the user's behalf, subject to its own consent obligations) must explicitly consent to this specific retention purpose. Enrolling or authenticating under Features 1-2 must never implicitly enable this.
* When enabled for a given user, the raw enrollment/authentication images for that user (not just the derived vector) may be retained in a store that is access-controlled and physically/logically separate from the `enrollments` table — never mixed with the default ephemeral-only path.
* Retention duration, deletion/revocation mechanics for this specific store, exact training methodology, and how/whether retrained model versions get distributed to self-hosted instances are **not yet defined** — see docs/open-decisions.md for the open items this creates. Do not implement collection, storage, or use of this data until those are resolved and explicitly approved; this section describes the intended shape only.

## 5. System Memory and Context Handling

To ensure continuous alignment across OpenAI, Gemini, and Claude, agents must manage context via explicit file reads/writes:
* Agents must parse this `system.md` file at the start of every new session.
* Do not rely on LLM thread history for architectural rules. Treat this document as the absolute source of truth.
* If architectural changes are approved by the user, the acting agent MUST rewrite this `system.md` file to reflect the new state.

## 6. Live Documentation and System Checks

Agents must maintain a synchronous state of the project build using a live status document.
* **File Requirement:** Agents must create and maintain a `STATUS.md` or `CHANGELOG.md` file in the root directory.
* **Check-in Protocol:** After completing a modular component (e.g. finalizing the FastAPI routing), the agent must append a timestamped entry to the live documentation.
* **Check-out Protocol:** When a new agent takes over the workspace, it must read the live documentation to understand what was built by the previous LLM, preventing duplicate work or regression bugs.