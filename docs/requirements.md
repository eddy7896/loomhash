# Requirements inventory

Source: [system.md](../system.md). Status: specified but unimplemented unless stated otherwise.

**Revision note (2026-09-18):** system.md's Feature 1/2 pipelines and Constraint 3/4 were substantially revised — the server's Inference module now receives raw image data (ephemerally, never persisted) and computes the 128-d vector server-side, superseding the original client-side "compute the vector, transmit only the vector" design this table was originally written against. ENR-02 and ENR-03 below are updated to match; see [open-decisions.md](open-decisions.md)'s D-04/D-08 resolution for the full reasoning, and D-12/D-13 for what's still unresolved as a result.

## Product scope

The intended service lets an integrating application enroll a person's facial geometry, verify a later sample, and revoke the ability to match that enrollment. Self-hosting and keeping camera media on the client are explicit objectives. The integrating application's identity system, operator workflows, and deployment environment are not specified.

The authentication flow retrieves a particular user's seed before matching. This implies one-to-one verification against a claimed identity; it does not define an identity search across all users. How that identity is supplied and authorized remains open.

## Functional requirements

| ID | Specified behavior | Evidence needed for acceptance |
| --- | --- | --- |
| ENR-01 | Capture 12 views across a one-second yaw rotation on the client; client-side MediaPipe rejects frames with no detected face before transmission (>=8/12 valid required). | Capture timestamps, distinct frames, and an agreed yaw/quality policy. |
| ENR-02 | **Revised 2026-09-18:** server's Inference module computes the 128-d vector per valid frame via ONNX regression (not client-side geometric math as originally specified), then averages across valid frames. | Real trained model artifact (does not exist yet — see D-04), API route accepting image data (D-12, unresolved), reproducible fixtures once both exist. |
| ENR-03 | **Revised 2026-09-18:** client sends valid frame *images* (post face-detection filtering), not a pre-computed vector; raw image data is processed server-side only within the Inference module, ephemerally, never persisted. | Network inspection demonstrating images are never logged/cached/persisted anywhere outside a single in-flight inference request; API route to actually carry image data not yet implemented (D-12). |
| ENR-04 | Generate a random 32-byte seed per enrollment and project to 256 bits using seeded LSH. | Seed-generation review and deterministic projection fixtures after algorithm approval. |
| ENR-05 | Persist the user_id, seed, and loom_hash tuple. | Adapter round-trip checks after schema and lifecycle decisions. |
| AUT-01 | Capture one frame and produce the same 128-dimensional feature representation. | Shared feature-contract checks and evaluation against multi-frame enrollment. |
| AUT-02 | Retrieve that user's seed/template and project the query using the stored seed. | Consistent cache/database behavior and seed/template pairing. |
| AUT-03 | Compute `(stored_hash ^ query_hash).bit_count() / 256.0`. | Known bit-pattern checks and valid 256-bit input bounds. |
| AUT-04 | Return HTTP 200 for distance <= 0.20; otherwise HTTP 401. | Boundary checks at 51 differing bits (accept) and 52 (reject). Other failure responses are unspecified. |
| REV-01 | On consent revocation, delete the user's seed from PostgreSQL and Redis. | Verify subsequent authentication cannot succeed through either store; backup and in-flight behavior need decisions. |

The 51/52 boundary is derived directly from the specified formula: 51/256 = 0.19921875 and 52/256 = 0.203125. It is a functional boundary, not evidence that 0.20 achieves an acceptable biometric error rate.

## Technology and constraints

| Area | Specified requirement |
| --- | --- |
| Edge | Next.js/React and client-side MediaPipe WASM, for face-detection/quality-gating only (revised 2026-09-18 — no longer computes the 128-d vector). |
| API | FastAPI, Uvicorn, and Caddy. Routes still need to be reworked to carry image data instead of vectors for enroll/authenticate (D-12, unresolved). |
| Matching | Python >= 3.10, NumPy seeded LSH, native XOR and int.bit_count(). Unaffected by the 2026-09-18 revision. |
| Inference | **Revised 2026-09-18:** server-side, CPU-only ONNX Runtime, INT8 MobileNetV4 regressor. Pipeline role now defined (image in, 128-d vector out, ephemeral processing only) — see [open-decisions.md](open-decisions.md) D-04. Not yet implemented; model artifact doesn't exist. |
| Storage | PostgreSQL persistence and Redis hot lookups. Unaffected by the 2026-09-18 revision. |
| Compliance | Consent-revocation listeners and seed removal. Unaffected by the 2026-09-18 revision. |
| Prohibited matching | No Milvus, Pinecone, or FAISS for identity matching. |
| Media handling | **Revised 2026-09-18:** server-side MediaPipe remains prohibited (client-only, per the Edge row above); the Inference module is now the sole exception permitted to receive raw image data, and only ephemerally — no raw image persistence anywhere, including there. |
| Change control | Clarify ambiguity; no unapproved dependencies, routes, schemas, or architecture changes. |

This is resolved as of 2026-09-18 — constraint 3's original wording only listed vectors/hashes as permitted server memory contents; it's been revised to explicitly account for seeds, identifiers, the LSH projection matrix, connection/runtime state, and (within the Inference module only) ephemeral raw image data. See [open-decisions.md](open-decisions.md) D-06 (the original, narrower resolution) and D-04/D-08 (this revision).

## Unspecified product requirements

The source gives no measurable accuracy, liveness, latency, throughput, availability, supported-device, accessibility, or recovery targets. It does not define enrollment authorization, duplicate enrollment, tenant boundaries, service credentials, rate limits, account recovery, or deployment packaging. Web3 anchoring is mentioned as motivation, but no chain, transaction, or anchoring feature is specified. None of these is silently included in implementation scope.
