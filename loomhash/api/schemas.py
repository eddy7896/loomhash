"""Request/response models for the API Gateway (resolves the route/schema
part of D-10, approved 2026-09-17 -- see docs/open-decisions.md).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

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
