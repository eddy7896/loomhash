"""LoomHash API Gateway implementation.

Responsibilities:
  - Route /v1/enroll and /v1/authenticate requests (multipart/form-data)
  - Enforce caller authentication via API key (X-API-Key header, D-05)
  - Rate-limit /v1/authenticate to prevent brute-force (D-05)
  - Enforce enrollment liveness checks (D-07)
  - Enforce I/O boundaries (images never persisted, vectors never persisted)
  - DELETE delegates to loomhash.compliance.revoke(), not storage.delete()
    directly (Compliance module owns revocation-event authorization).
"""

from __future__ import annotations

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile
import numpy as np
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from loomhash.auth import (
    APIKey,
    APIKeyStore,
    InMemoryAPIKeyStore,
    RateLimiter,
    parse_key_id,
    verify_api_key,
)
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
from loomhash.inference import run_inference
from loomhash.inference.liveness import check_liveness
from loomhash.storage import EnrollmentRecord, InMemoryStorageBackend, StorageBackend

from .schemas import (
    AuthenticateResponse,
    EnrollResponse,
    RevokeResponse,
)
from .admin_routes import router as admin_router
from loomhash.storage.admin import APIEvent, AdminStore, InMemoryAdminStore

# ---------------------------------------------------------------------------
# Upload constraints
# ---------------------------------------------------------------------------
_MAX_IMAGE_BYTES = 4 * 1024 * 1024   # 4 MB per image
_MIN_ENROLL_IMAGES = 8
_MAX_ENROLL_IMAGES = 12


def get_storage(request: Request) -> StorageBackend:
    return request.app.state.storage


def get_key_store(request: Request) -> APIKeyStore:
    return request.app.state.key_store


def get_rate_limiter(request: Request) -> RateLimiter:
    return request.app.state.rate_limiter


def get_admin_store(request: Request) -> AdminStore:
    return request.app.state.admin_store

# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------

async def require_api_key(
    request: Request,
    x_api_key: str | None = Header(None),
) -> APIKey:
    """FastAPI dependency: validate X-API-Key header and return the APIKey record.

    Returns 401 on missing, malformed, unknown, inactive, or invalid keys.
    The error message is deliberately generic to avoid leaking whether a
    key_id exists.
    """
    if not x_api_key:
        raise HTTPException(status_code=401, detail="invalid or missing API key")

    key_id = parse_key_id(x_api_key)
    if key_id is None:
        raise HTTPException(status_code=401, detail="invalid or missing API key")

    key_store = get_key_store(request)
    stored = key_store.get_by_id(key_id)
    if stored is None or not verify_api_key(x_api_key, stored):
        raise HTTPException(status_code=401, detail="invalid or missing API key")

    return stored


def create_app(
    storage: StorageBackend | None = None,
    *,
    key_store: APIKeyStore | None = None,
    rate_limiter: RateLimiter | None = None,
    admin_store: AdminStore | None = None,
    enable_dev_cors: bool = False,
) -> FastAPI:
    """Build the LoomHash API app.

    storage defaults to InMemoryStorageBackend -- a non-durable prototype
    default, reset on every process restart. Pass a
    loomhash.storage.combined.PostgresRedisStorageBackend for anything
    beyond local development.

    key_store defaults to InMemoryAPIKeyStore -- tests and dev server should
    pre-populate it with at least one key.

    rate_limiter defaults to a new RateLimiter with standard limits.

    enable_dev_cors defaults to False (no CORS headers at all) so tests and
    any real deployment aren't silently permissive. Pass True only for local
    manual testing -- it allows any http://localhost:<port> or
    http://127.0.0.1:<port> origin.
    """
    app = FastAPI(title="LoomHash", version="0.0.0")
    app.state.storage = storage if storage is not None else InMemoryStorageBackend()
    app.state.key_store = key_store if key_store is not None else InMemoryAPIKeyStore()
    app.state.rate_limiter = rate_limiter if rate_limiter is not None else RateLimiter()
    app.state.admin_store = admin_store if admin_store is not None else InMemoryAdminStore()

    if enable_dev_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.middleware("http")
    async def telemetry_middleware(request: Request, call_next):
        import time
        start_time = time.perf_counter()
        
        response = await call_next(request)
        
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        
        key_id = None
        x_api_key = request.headers.get("x-api-key")
        if x_api_key:
            key_id = parse_key_id(x_api_key)
            
        event = APIEvent(
            key_id=key_id,
            endpoint=request.url.path,
            status_code=response.status_code,
            latency_ms=latency_ms,
        )
        # Using a background task here in production would be better, but synchronous is fine for MVP
        request.app.state.admin_store.log_event(event)
        
        return response

    app.include_router(admin_router)

    # ------------------------------------------------------------------
    # POST /v1/enroll
    # ------------------------------------------------------------------
    @app.post("/v1/enroll", response_model=EnrollResponse)
    async def enroll(
        user_id: str = Form(..., min_length=1),
        images: list[UploadFile] = File(...),
        storage: StorageBackend = Depends(get_storage),
        api_key: APIKey = Depends(require_api_key),
    ) -> EnrollResponse:
        # Validate image count
        if len(images) < _MIN_ENROLL_IMAGES or len(images) > _MAX_ENROLL_IMAGES:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"enroll requires {_MIN_ENROLL_IMAGES}-{_MAX_ENROLL_IMAGES} images, "
                    f"got {len(images)}"
                ),
            )

        # Read all images and validate
        raw_images: list[bytes] = []
        for i, upload in enumerate(images):
            if upload.content_type and not upload.content_type.startswith("image/"):
                raise HTTPException(
                    status_code=422,
                    detail=f"image[{i}] has non-image content-type: {upload.content_type}",
                )
            raw = await upload.read()
            if len(raw) > _MAX_IMAGE_BYTES:
                raise HTTPException(
                    status_code=422,
                    detail=f"image[{i}] exceeds {_MAX_IMAGE_BYTES // (1024*1024)} MB limit",
                )
            raw_images.append(raw)

        # Liveness check (D-07): reject if frames lack sufficient variation
        liveness = check_liveness(raw_images)
        if not liveness.passed:
            raise HTTPException(
                status_code=422,
                detail=f"liveness check failed: {liveness.reason}",
            )

        # Infer a 128-d vector per image
        per_frame_vectors: list[np.ndarray] = []
        for i, raw in enumerate(raw_images):
            try:
                vec = run_inference(raw)  # shape (128,), float64; raw discarded here
            except ValueError as exc:
                raise HTTPException(status_code=422, detail=f"image[{i}]: {exc}") from exc
            per_frame_vectors.append(vec)

        # Average per-frame vectors -> single enrollment vector
        enrollment_vector = np.mean(per_frame_vectors, axis=0)  # shape (128,)

        seed = generate_seed()
        loom_hash = project(enrollment_vector, seed)
        record = EnrollmentRecord(
            user_id=user_id,
            seed=seed,
            loom_hash=hash_to_bytes(loom_hash),
            lsh_version=LSH_VERSION,
        )
        storage.enroll(record)
        return EnrollResponse(user_id=user_id)

    # ------------------------------------------------------------------
    # POST /v1/authenticate
    # ------------------------------------------------------------------
    @app.post(
        "/v1/authenticate",
        response_model=AuthenticateResponse,
        responses={
            401: {"description": "Authentication failed or invalid API key"},
            429: {"description": "Rate limit exceeded"},
        },
    )
    async def authenticate(
        request: Request,
        user_id: str = Form(..., min_length=1),
        image: UploadFile = File(...),
        storage: StorageBackend = Depends(get_storage),
        api_key: APIKey = Depends(require_api_key),
    ) -> AuthenticateResponse:
        # Rate limiting (D-05): per-key limit on authentication attempts
        limiter = get_rate_limiter(request)
        if not limiter.check(api_key.key_id):
            retry_after = limiter.retry_after(api_key.key_id)
            return JSONResponse(  # type: ignore[return-value]
                status_code=429,
                content={"detail": "rate limit exceeded"},
                headers={"Retry-After": str(int(retry_after) + 1)},
            )
        limiter.record(api_key.key_id)

        record = storage.get(user_id)
        if record is None:
            raise HTTPException(status_code=401, detail="authentication failed")

        if image.content_type and not image.content_type.startswith("image/"):
            raise HTTPException(
                status_code=422,
                detail=f"image has non-image content-type: {image.content_type}",
            )
        raw = await image.read()
        if len(raw) > _MAX_IMAGE_BYTES:
            raise HTTPException(
                status_code=422,
                detail=f"image exceeds {_MAX_IMAGE_BYTES // (1024*1024)} MB limit",
            )

        try:
            query_vector = run_inference(raw)  # shape (128,), float64; raw discarded here
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        query_hash = project(query_vector, record.seed)
        stored_hash = hash_from_bytes(record.loom_hash)
        if not is_match(stored_hash, query_hash):
            raise HTTPException(status_code=401, detail="authentication failed")

        return AuthenticateResponse()

    # ------------------------------------------------------------------
    # DELETE /v1/users/{user_id}
    # ------------------------------------------------------------------
    @app.delete(
        "/v1/users/{user_id}",
        response_model=RevokeResponse,
        responses={
            401: {"description": "Invalid or missing API key"},
            403: {"description": "Revocation not authorized"},
            500: {"description": "Revocation could not be confirmed in every store"},
        },
    )
    def revoke(
        user_id: str,
        storage: StorageBackend = Depends(get_storage),
        api_key: APIKey = Depends(require_api_key),
    ) -> RevokeResponse:
        try:
            deleted = process_revocation(storage, api_key, user_id)
        except RevocationDenied as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        if not deleted:
            raise HTTPException(status_code=500, detail="revocation incomplete, retry")
        return RevokeResponse(user_id=user_id)

    return app
