# Use cases

Scope decision (2026-09-17): this documentation set targets the **feasibility prototype** milestone — correctness of the geometric enrollment/authentication/revocation pipeline. Adversarial hardening (replay resistance, liveness, deepfake defense) is documented as deferred, not as an implemented property. See [open-decisions.md](open-decisions.md) for the full resolution and which gaps remain blocking vs. deferred at this stage.

## Actors

| Actor | Description | Specified in system.md? |
| --- | --- | --- |
| End user / data subject | Person whose face is enrolled and later authenticated. | Implicit. |
| Integrating application | Backend service that calls the LoomHash API on the end user's behalf. | Implicit; its own auth/identity system is explicitly out of scope. |
| LoomHash API | The FastAPI gateway plus cryptography/storage modules. | Yes. |
| Operator | Person who deploys and administers the self-hosted service. | Implicit. |
| Compliance actor | Whoever triggers a consent-revocation event (end user, integrating app, or operator). | Implicit — the trigger source and its authorization are not specified (see D-05, D-10). |

## UC-1 — Enroll a user

**Primary flow (matches ENR-01..ENR-05 in [requirements.md](requirements.md)):**
1. Integrating application starts an enrollment session for a known user identifier (transport not yet specified — D-05).
2. Client captures 12 frames across a 1-second yaw rotation.
3. Client computes mean 3D landmarks and derives the 128-d rigid-distance vector.
4. Client sends only the 128-d vector (plus whatever identity/session metadata is approved) to the API.
5. Server generates a random 32-byte seed, projects the vector via seeded LSH into a 256-bit loom_hash.
6. Server persists (user_id, seed, loom_hash).
7. API returns enrollment success to the integrating application.

**Prototype-scope edge cases (must be defined before implementation):**
- Re-enrollment of an already-enrolled user: overwrite, reject, or version? Not specified — must be decided, not assumed.
- Capture quality/yaw-coverage rejection: what makes a frame set invalid? Currently undefined (D-02).
- Enrollment for a user identifier that does not exist in the integrating application: no validation contract exists yet.

**Deferred (post-prototype) edge cases:** spoofed capture (photo/video/3D mask), coordinated multi-frame deepfake injection, camera driver tampering. These require a threat model (D-07) not needed for feasibility validation.

## UC-2 — Authenticate a user

**Primary flow (matches AUT-01..AUT-04):**
1. Integrating application starts an authentication attempt for a claimed user identifier.
2. Client captures a single frame, derives the same 128-d feature representation used at enrollment.
3. Client sends the query vector to the API.
4. Server retrieves the stored seed and loom_hash for the claimed user_id.
5. Server projects the query vector with the stored seed into a query_hash.
6. Server computes `distance = (stored_hash ^ query_hash).bit_count() / 256.0`.
7. API returns 200 if `distance <= 0.20`, else 401.

**Prototype-scope edge cases:**
- Claimed user_id has no stored seed (never enrolled, or already revoked): must return a defined response, not a crash or ambiguous 401 that's indistinguishable from a failed match.
- Malformed or out-of-range query vector: validation contract undefined.
- Single-frame query vs. multi-frame-averaged enrollment vector: whether they are comparable under the same feature pipeline is an open evaluation question, not just an engineering one.

**Deferred edge cases:** replay of a previously captured valid vector (no freshness proof exists in the specified protocol — see architecture.md's trust-boundary analysis); virtual camera / injected vector attacks. These are explicitly out of scope until D-07/D-08 are resolved.

## UC-3 — Revoke consent (crypto-shredding)

**Primary flow (matches REV-01):**
1. An authorized actor triggers a revocation event for a user_id (authorization mechanism undefined — D-05/D-10).
2. Server deletes the user's seed from PostgreSQL and Redis.
3. Subsequent authentication attempts for that user_id can no longer succeed, because the seed required to reproduce a matching hash no longer exists.

**Prototype-scope edge cases:**
- Revocation for a user_id with no stored seed: idempotent no-op or error? Undefined.
- Partial failure (delete succeeds in Postgres, fails in Redis, or vice versa): no retry/consistency contract exists yet (see architecture.md's revocation race-condition note).
- Revocation racing an in-flight authentication holding an already-loaded seed in process memory: not addressed by "delete from both stores" alone.

**Deferred:** legal/compliance evidence that deletion achieves anonymization under DPDP/GDPR (see D-09) — a technical deletion mechanism can and should be built and tested for the prototype; the *legal claim* of anonymization is a separate, deferred deliverable.

## Explicitly out of scope for the prototype

- Multi-tenant isolation between integrating applications.
- Operator-facing admin UI or CLI beyond what's needed to run the service locally.
- Web3/on-chain anchoring of the loom_hash (mentioned in system.md only as motivation, not as a specified feature).
- Rate limiting, account recovery, and accessibility/device-support targets — none are specified in system.md.
