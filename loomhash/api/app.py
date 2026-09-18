"""FastAPI gateway (system.md API Gateway module).

Routes and response shapes resolve the remaining route/schema part of
D-10, approved 2026-09-17 (see docs/open-decisions.md). Only ever accepts
numerical vectors -- never images or frames (constraint 4) -- and never
persists or logs raw biometric media (constraint 3). Do not add request-
body logging/middleware here: a logged request body would contain the
128-d vector, which constraint 3 says must not be persisted.

authenticate() never returns the Hamming distance to the caller, even on
success: leaking that value would let an attacker hill-climb a forged
vector toward the acceptance threshold one probe at a time.

An unknown/never-enrolled user_id gets the same 401 as a failed face
match on /v1/authenticate, by explicit decision (2026-09-17) -- returning
a distinct code (e.g. 404) would let a caller enumerate which user_ids
are enrolled.

DELETE /v1/users/{user_id} delegates to loomhash.compliance.revoke()
rather than calling storage.delete() directly -- revocation-event
authorization is the Compliance module's job, not this route's (see
docs/agents/compliance.md).
"""

from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from loomhash.compliance import RevocationDenied
from loomhash.compliance import revoke as process_revocation
from loomhash.cryptography import (
    LSH_VERSION,
    generate_seed,
    hash_from_bytes,
    hash_to_bytes,
    is_match,
    project,
)
from loomhash.storage import EnrollmentRecord, InMemoryStorageBackend, StorageBackend

from .schemas import (
    AuthenticateRequest,
    AuthenticateResponse,
    EnrollRequest,
    EnrollResponse,
    RevokeResponse,
)


def get_storage(request: Request) -> StorageBackend:
    return request.app.state.storage


def create_app(storage: StorageBackend | None = None, *, enable_dev_cors: bool = False) -> FastAPI:
    """Build the LoomHash API app.

    storage defaults to InMemoryStorageBackend -- a non-durable prototype
    default, reset on every process restart. Pass a
    loomhash.storage.combined.PostgresRedisStorageBackend for anything
    beyond local development; see docs/agents/storage.md for why that
    adapter isn't the default here (untested against live services in
    this development environment).

    enable_dev_cors defaults to False (no CORS headers at all) so tests and
    any real deployment aren't silently permissive. Pass True only for local
    manual testing (see __main__.py and edge/README.md) -- it allows any
    http://localhost:<port> or http://127.0.0.1:<port> origin, which is fine
    for a developer's own machine but must never be enabled as-is in an
    actual deployment.
    """
    app = FastAPI(title="LoomHash", version="0.0.0")
    app.state.storage = storage if storage is not None else InMemoryStorageBackend()

    if enable_dev_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.post("/v1/enroll", response_model=EnrollResponse)
    def enroll(body: EnrollRequest, storage: StorageBackend = Depends(get_storage)) -> EnrollResponse:
        seed = generate_seed()
        loom_hash = project(body.vector, seed)
        record = EnrollmentRecord(
            user_id=body.user_id,
            seed=seed,
            loom_hash=hash_to_bytes(loom_hash),
            lsh_version=LSH_VERSION,
        )
        storage.enroll(record)
        return EnrollResponse(user_id=body.user_id)

    @app.post(
        "/v1/authenticate",
        response_model=AuthenticateResponse,
        responses={401: {"description": "Authentication failed"}},
    )
    def authenticate(
        body: AuthenticateRequest, storage: StorageBackend = Depends(get_storage)
    ) -> AuthenticateResponse:
        record = storage.get(body.user_id)
        if record is None:
            raise HTTPException(status_code=401, detail="authentication failed")

        query_hash = project(body.vector, record.seed)
        stored_hash = hash_from_bytes(record.loom_hash)
        if not is_match(stored_hash, query_hash):
            raise HTTPException(status_code=401, detail="authentication failed")

        return AuthenticateResponse()

    @app.delete(
        "/v1/users/{user_id}",
        response_model=RevokeResponse,
        responses={
            403: {"description": "Revocation not authorized"},
            500: {"description": "Revocation could not be confirmed in every store"},
        },
    )
    def revoke(user_id: str, storage: StorageBackend = Depends(get_storage)) -> RevokeResponse:
        try:
            deleted = process_revocation(storage, user_id)
        except RevocationDenied as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        if not deleted:
            raise HTTPException(status_code=500, detail="revocation incomplete, retry")
        return RevokeResponse(user_id=user_id)

    return app
