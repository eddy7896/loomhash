# Requirements inventory

Source: [system.md](../system.md). Status: specified but unimplemented unless stated otherwise.

## Product scope

The intended service lets an integrating application enroll a person's facial geometry, verify a later sample, and revoke the ability to match that enrollment. Self-hosting and keeping camera media on the client are explicit objectives. The integrating application's identity system, operator workflows, and deployment environment are not specified.

The authentication flow retrieves a particular user's seed before matching. This implies one-to-one verification against a claimed identity; it does not define an identity search across all users. How that identity is supplied and authorized remains open.

## Functional requirements

| ID | Specified behavior | Evidence needed for acceptance |
| --- | --- | --- |
| ENR-01 | Capture 12 views across a one-second yaw rotation on the client. | Capture timestamps, distinct frames, and an agreed yaw/quality policy. |
| ENR-02 | Compute mean 3D landmarks, then a 128-dimensional rigid-distance vector. | Approved landmark pairs, coordinate system, alignment, normalization, and reproducible fixtures. |
| ENR-03 | Send only the numerical vector as biometric input. | Network inspection demonstrating that images and landmark meshes are not transmitted. Identity/control metadata needs clarification. |
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
| Edge | Next.js/React and client-side MediaPipe WASM. |
| API | FastAPI, Uvicorn, and Caddy. Routes and complete request/response contracts are undefined. |
| Matching | Python >= 3.10, NumPy seeded LSH, native XOR and int.bit_count(). |
| Inference | CPU-only ONNX Runtime with an INT8 MobileNetV4 or ConvNeXt regressor; pipeline role is undefined. |
| Storage | PostgreSQL persistence and Redis hot lookups. |
| Compliance | Consent-revocation listeners and seed removal. |
| Prohibited matching | No Milvus, Pinecone, or FAISS for identity matching. |
| Media handling | No server-side MediaPipe; no raw image persistence in endpoints, caches, or logs. |
| Change control | Clarify ambiguity; no unapproved dependencies, routes, schemas, or architecture changes. |

The literal restriction that only vectors and hashes may exist in server memory conflicts with the required seed, user identifier, projection matrix, and inference state. The likely intended restriction concerns biometric media, but that interpretation needs approval.

## Unspecified product requirements

The source gives no measurable accuracy, liveness, latency, throughput, availability, supported-device, accessibility, or recovery targets. It does not define enrollment authorization, duplicate enrollment, tenant boundaries, service credentials, rate limits, account recovery, or deployment packaging. Web3 anchoring is mentioned as motivation, but no chain, transaction, or anchoring feature is specified. None of these is silently included in implementation scope.
