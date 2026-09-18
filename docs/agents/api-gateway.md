# Agent context: API Gateway module

Read this before touching FastAPI routes or request/response handling. Also read [../memory-system.md](../memory-system.md)'s session-start protocol first.

**Architecture revision implemented, 2026-09-18 (D-12, resolved):** system.md's pipeline was revised so the server's Inference module now receives raw images and computes the 128-d vector server-side (see [inference.md](inference.md), [../open-decisions.md](../open-decisions.md) D-04/D-08). The API routes accept `multipart/form-data` with images, but never log or cache them (Constraint 3).

## Role

FastAPI + Uvicorn (behind Caddy) service that receives image uploads via multipart/form-data from clients and coordinates the inference, enrollment, and authentication flows across the Inference, Cryptography, and Storage modules. Owns request validation and HTTP-level response semantics.

## I/O contract

- **Accepts:** `multipart/form-data` uploads. `POST /v1/enroll` takes `user_id` and 8-12 `images`. `POST /v1/authenticate` takes `user_id` and 1 `image`.
- **Returns:** per AUT-04, 200 for a successful authentication match, 401 for a mismatch. Other failure modes (validation errors, unknown user, rate limits) return 422 or 401.

## Immutable constraints that apply here

- **Constraint 3 (Data Privacy):** no endpoint may cache or log raw image data. Images are read directly into memory (`await upload.read()`) and passed ephemerally to the Inference module.
- **Constraint 4 (Compute Location):** this module must never import mediapipe or perform frame/mesh processing server-side.

## Implementation details

Routes and request/response contracts were implemented in [../../loomhash/api/](../../loomhash/api/):

- `schemas.py` — Response models (`EnrollResponse`, `AuthenticateResponse`, `RevokeResponse`). Request models are handled natively by FastAPI's `File`/`Form`.
- `app.py` — `create_app(storage=None)`: `POST /v1/enroll`, `POST /v1/authenticate`, `DELETE /v1/users/{user_id}`. Defaults to `InMemoryStorageBackend` (non-durable) when no storage backend is passed in. `DELETE /v1/users/{user_id}` calls `loomhash.compliance.revoke()`, not `storage.delete()` directly — see [compliance.md](compliance.md). Do not "simplify" this back to a direct storage call; that was the exact boundary blur the Compliance module was built to fix.
- `__main__.py` — `python -m loomhash.api` for local manual smoke-testing only (in-memory storage, resets on restart).

End-to-end tested (real HTTP requests through the ASGI app via `TestClient`, in-memory storage) in [../../tests/test_api/test_routes.py](../../tests/test_api/test_routes.py): full enroll -> authenticate -> revoke loop, upsert-on-re-enroll invalidating the old vector, unknown-user 401, wrong-length-vector 422, and unexpected-field 422.

**Do not add request/response logging that could capture the vector, seed, or hash** — constraint 3 applies to this module's logs too, not just its storage. **Do not add a distance/score field to the authenticate response** — that was a deliberate decision to prevent hill-climbing attacks, not an oversight.

**Gap:** never run against the real `PostgresRedisStorageBackend` — only against `InMemoryStorageBackend`, since no live Postgres/Redis exists in this environment (see [storage.md](storage.md)). Wiring a real backend into `create_app()` for an actual deployment is a separate, not-yet-done step.

## What is still NOT defined

Caller authentication/authorization beyond the "trusted caller-supplied user_id" (D-05 minimal); rate limiting; Caddy reverse-proxy configuration (a deployment concern, not this module's code).

## Related requirements / decisions

Requirements: ENR-03, ENR-05, AUT-01..AUT-04, REV-01 (as the entry point coordinating storage/compliance). Open decisions: D-05 (resolved, minimal), D-06 (resolved), D-10 (resolved), D-12 (unresolved, blocking any request-schema rework).
