# Agent context: API Gateway module

Read this before touching FastAPI routes or request/response handling. Also read [../memory-system.md](../memory-system.md)'s session-start protocol first.

## Role

FastAPI + Uvicorn (behind Caddy) service that receives numerical biometric input from clients and coordinates the enrollment/authentication flows across the Cryptography and Storage modules. Owns request validation and HTTP-level response semantics; does not own the LSH/matching math or persistence details itself.

## I/O contract

- **Accepts:** numerical vectors (128-d feature vector) plus whatever identity/session metadata gets approved. Never accepts images, frames, or mesh data — see constraint 4.
- **Returns:** per AUT-04, 200 for a successful authentication match, 401 for a mismatch. Other failure modes (validation errors, unknown user, rate limits) are unspecified — do not invent status codes/response bodies for them without flagging it as a proposal.

## Immutable constraints that apply here

- **Constraint 3 (Data Privacy):** no endpoint may accept, cache, or log raw image data. Reject any request-body design that includes an image/frame field.
- **Constraint 4 (Compute Location):** this module must never import mediapipe or perform frame/mesh processing server-side. If a "convenience" feature seems to require that, it's a scope change requiring explicit approval, not a routine implementation choice.

## D-05 (minimal) and D-10 are resolved — implementation exists

Routes, request/response contracts, and error semantics were approved 2026-09-17; see [../open-decisions.md](../open-decisions.md). Implemented in [../../loomhash/api/](../../loomhash/api/):

- `schemas.py` — `EnrollRequest`/`AuthenticateRequest` (both `extra="forbid"`, fixed 128-length `vector` field) and their response models.
- `app.py` — `create_app(storage=None)`: `POST /v1/enroll`, `POST /v1/authenticate`, `DELETE /v1/users/{user_id}`. Defaults to `InMemoryStorageBackend` (non-durable) when no storage backend is passed in. `DELETE /v1/users/{user_id}` calls `loomhash.compliance.revoke()`, not `storage.delete()` directly — see [compliance.md](compliance.md). Do not "simplify" this back to a direct storage call; that was the exact boundary blur the Compliance module was built to fix.
- `__main__.py` — `python -m loomhash.api` for local manual smoke-testing only (in-memory storage, resets on restart).

End-to-end tested (real HTTP requests through the ASGI app via `TestClient`, in-memory storage) in [../../tests/test_api/test_routes.py](../../tests/test_api/test_routes.py): full enroll -> authenticate -> revoke loop, upsert-on-re-enroll invalidating the old vector, unknown-user 401, wrong-length-vector 422, and unexpected-field 422.

**Do not add request/response logging that could capture the vector, seed, or hash** — constraint 3 applies to this module's logs too, not just its storage. **Do not add a distance/score field to the authenticate response** — that was a deliberate decision to prevent hill-climbing attacks, not an oversight.

**Gap:** never run against the real `PostgresRedisStorageBackend` — only against `InMemoryStorageBackend`, since no live Postgres/Redis exists in this environment (see [storage.md](storage.md)). Wiring a real backend into `create_app()` for an actual deployment is a separate, not-yet-done step.

## What is still NOT defined

Caller authentication/authorization beyond the "trusted caller-supplied user_id" (D-05 minimal); rate limiting; Caddy reverse-proxy configuration (a deployment concern, not this module's code).

## Related requirements / decisions

Requirements: ENR-03, ENR-05, AUT-01..AUT-04, REV-01 (as the entry point coordinating storage/compliance). Open decisions: D-05 (resolved, minimal), D-06 (resolved), D-10 (resolved).
