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

from pydantic import BaseModel

class EnrollResponse(BaseModel):
    user_id: str
    status: str = "enrolled"


class AuthenticateResponse(BaseModel):
    status: str = "authenticated"


class RevokeResponse(BaseModel):
    user_id: str
    status: str = "revoked"
