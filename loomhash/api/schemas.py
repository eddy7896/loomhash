"""Request/response models for the API Gateway (resolves the route/schema
part of D-10, approved 2026-09-17 -- see docs/open-decisions.md).
"""Response models for the API Gateway.

Request inputs for enroll and authenticate are now multipart/form-data (D-12,
resolved 2026-09-18): user_id is a Form field, images are UploadFile fields.
FastAPI handles multipart natively, so there are no Pydantic request models for
those routes -- validation happens in app.py's route functions directly.

The old EnrollRequest / AuthenticateRequest Pydantic models (which accepted a
JSON body with a 128-d vector) have been removed. They accepted the pre-computed
vector from the edge client under the original vector-only architecture; that
design was superseded by D-04/D-12 (server-side ONNX inference). The removal is
intentional, not an oversight -- do not re-add them.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from pydantic import BaseModel

from loomhash.cryptography import VECTOR_DIM


class EnrollRequest(BaseModel):
    # extra="forbid": reject any unexpected field outright (e.g. a stray
    # "image"/"frame" field) instead of silently ignoring it, per constraint 3.
    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(..., min_length=1)
    vector: list[float] = Field(..., min_length=VECTOR_DIM, max_length=VECTOR_DIM)


class EnrollResponse(BaseModel):
    user_id: str
    status: str = "enrolled"


class AuthenticateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(..., min_length=1)
    vector: list[float] = Field(..., min_length=VECTOR_DIM, max_length=VECTOR_DIM)


class AuthenticateResponse(BaseModel):
    status: str = "authenticated"


class RevokeResponse(BaseModel):
    user_id: str
    status: str = "revoked"
