# System Context: LoomHash

**Project Name:** LoomHash (Self-Hosted Zero-Knowledge Biometric Microservice)
**Mission:** Provide enterprise-grade, deepfake-resistant 3D facial authentication via a privacy-first, zero-knowledge architecture.

## 1. Core Development Methodologies

### Ask, Do Not Assume
All AI agents (OpenAI, Gemini, Claude, Cursor, etc.) contributing to this codebase must adhere strictly to the "Ask, Do Not Assume" protocol:
* If a technical implementation detail is ambiguous, pause and prompt the user for clarification.
* Do not introduce new third-party libraries or external dependencies without explicit user consent.
* Do not infer database schemas or API routes outside of the defined Feature Set Documentation. 

### Modular Architecture
The project must maintain strict decoupling of concerns. AI agents must isolate logic into the following independent modules:
* **Edge Extraction Module:** Client-side WASM for camera capture and 128-d vector generation.
* **Cryptography Module:** Pure Python LSH projection and XOR matching logic.
* **Inference Module:** ONNX Runtime neural regressor.
* **Storage Module:** Redis and PostgreSQL database adapters.
* **Compliance Module:** Event listeners for crypto-shredding and DPDP/GDPR consent revocation.

## 2. Agent Directives and Hallucination Checks

Before outputting code, agents must run an internal hallucination check against these immutable constraints:
* **Constraint 1 (No Vector DBs for Identity):** Ensure no code imports or utilizes Milvus, Pinecone, or FAISS for matching user identities. Matching must only use Locality-Sensitive Hashing and native bitwise XOR.
* **Constraint 2 (Python Version):** Ensure code targets Python 3.10 or higher. The `int.bit_count()` method is mandatory for hardware-accelerated Hamming distance checks.
* **Constraint 3 (Data Privacy):** Verify that no endpoint, cache, or log writes raw image data (.jpg, .png, arrays) to disk. Only 128-d float vectors and 256-bit hashes are permitted to exist in server memory.
* **Constraint 4 (Compute Location):** Verify that media processing (MediaPipe) is confined to the client side. The server API must only accept numerical vectors.

## 3. System Architecture

The infrastructure operates as a hybrid edge-cloud pipeline.

* **Edge Client:** Next.js / React, MediaPipe WASM.
* **Inference Engine:** ONNX Runtime (INT8 Quantized MobileNetV4 / ConvNeXt) strictly running on CPU.
* **API Gateway:** FastAPI, Uvicorn, Caddy Reverse Proxy.
* **Cache and Persistence:** Redis for hot key lookups, PostgreSQL for persistent storage.
* **Math and Crypto Core:** Native Python `numpy` for seeded LSH projection, native `int.bit_count()` for scoring.

## 4. Feature Set Documentation

### Core Data Structures
* **128-d Rigid Vector:** Euclidean distances between fixed cranial points (e.g. nasion to zygomatic arch).
* **Cryptographic Seed (32-byte):** A random salt generated per user, stored off-chain in PostgreSQL/Redis.
* **256-bit LoomHash:** The final binarized string resulting from the seeded LSH projection.

### Feature 1: Enrollment Pipeline
1. Client captures 12 multi-view frames spanning a 1-second yaw rotation.
2. Client extracts 3D facial mesh, computes mean landmarks, and derives the 128-d rigid distance vector.
3. Network transmits only the 128-d vector to the API.
4. Server generates a random cryptographic seed.
5. Server projects the vector using the seed via LSH to create a 256-bit loom_hash.
6. Server saves the (user_id, seed, loom_hash) tuple to the database.

### Feature 2: Authentication Pipeline
1. Client captures a single frame, extracts the 3D mesh, and computes the 128-d query vector.
2. Network transmits the query vector to the API.
3. Server retrieves the seed and loom_hash from Redis/Postgres.
4. Server projects the query vector using the stored seed to create a query_hash.
5. Server calculates Hamming distance: distance = (stored_hash ^ query_hash).bit_count() / 256.0
6. Gateway evaluates logic: If distance is <= 0.20, return 200 OK. Else, return 401 Unauthorized.

### Feature 3: Crypto-Shredding (DPDP 2026 and GDPR)
* To comply with the DPDP Act 2026 (Purpose Limitation) and GDPR (Right to Erasure) while allowing immutable Web3 hash anchoring, the system utilizes Crypto-Shredding.
* If a user revokes consent, the system executes a DELETE query dropping the user's cryptographic seed from PostgreSQL/Redis.
* Result: Without the seed, the 256-bit hash becomes mathematically untraceable, converting pseudonymous data into fully anonymized data.

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