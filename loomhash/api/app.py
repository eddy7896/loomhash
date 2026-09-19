"""LoomHash API Gateway implementation.

Responsibilities:
  - Route /v1/enroll and /v1/authenticate requests (multipart/form-data)
  - Enforce I/O boundaries (images never persisted, vectors never persisted)
  - DELETE delegates to loomhash.compliance.revoke(), not storage.delete()
    directly (Compliance module owns revocation-event authorization).
"""

from __future__ import annotations

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
import numpy as np
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
from loomhash.inference import run_inference
from loomhash.storage import EnrollmentRecord, InMemoryStorageBackend, StorageBackend

from .schemas import (
    AuthenticateResponse,
    EnrollResponse,
    RevokeResponse,
)

# ---------------------------------------------------------------------------
# Upload constraints
# ---------------------------------------------------------------------------
_MAX_IMAGE_BYTES = 4 * 1024 * 1024   # 4 MB per image
_MIN_ENROLL_IMAGES = 8
_MAX_ENROLL_IMAGES = 12


def get_storage(request: Request) -> StorageBackend:
    return request.app.state.storage


def create_app(storage: StorageBackend | None = None, *, enable_dev_cors: bool = False) -> FastAPI:
    """Build the LoomHash API app.

    storage defaults to InMemoryStorageBackend -- a non-durable prototype
    default, reset on every process restart. Pass a
    loomhash.storage.combined.PostgresRedisStorageBackend for anything
    beyond local development.

    enable_dev_cors defaults to False (no CORS headers at all) so tests and
    any real deployment aren't silently permissive. Pass True only for local
    manual testing -- it allows any http://localhost:<port> or
    http://127.0.0.1:<port> origin.
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

    # ------------------------------------------------------------------
    # POST /v1/enroll
    # ------------------------------------------------------------------
    @app.post("/v1/enroll", response_model=EnrollResponse)
    async def enroll(
        user_id: str = Form(..., min_length=1),
        images: list[UploadFile] = File(...),
        storage: StorageBackend = Depends(get_storage),
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

        # Infer a 128-d vector per image; reject if any image is invalid
        per_frame_vectors: list[np.ndarray] = []
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
        responses={401: {"description": "Authentication failed"}},
    )
    async def authenticate(
        user_id: str = Form(..., min_length=1),
        image: UploadFile = File(...),
        storage: StorageBackend = Depends(get_storage),
    ) -> AuthenticateResponse:
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
