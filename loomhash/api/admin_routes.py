"""Admin routes for the Developer Dashboard.

Exposes endpoints for managing API keys, viewing analytics and billing,
and configuring project settings. In a real deployment, these would be protected
by developer authentication (e.g., JWT). For this prototype, they are unprotected.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from loomhash.auth.auth import generate_api_key
from loomhash.auth.key_store import APIKeyStore
from loomhash.storage import StorageBackend
from loomhash.storage.admin import AdminStore


router = APIRouter(prefix="/v1/admin", tags=["admin"])


class APIKeyResponse(BaseModel):
    key_id: str
    raw_key: str | None = None
    created_at: int
    is_active: bool


class SettingUpdate(BaseModel):
    value: str


from fastapi import Request

#
# Dependencies
#

def get_key_store(request: Request) -> APIKeyStore:
    return request.app.state.key_store


def get_admin_store(request: Request) -> AdminStore:
    return request.app.state.admin_store


def get_storage_backend(request: Request) -> StorageBackend:
    return request.app.state.storage


#
# API Keys (Authentication Tab)
#

@router.get("/keys", response_model=list[APIKeyResponse])
def list_keys(key_store: APIKeyStore = Depends(get_key_store)):
    keys = key_store.list_keys()
    return [
        APIKeyResponse(
            key_id=k.key_id,
            created_at=int(k.created_at.timestamp()),
            is_active=k.is_active,
        )
        for k in keys
    ]


@router.post("/keys", response_model=APIKeyResponse)
def create_key(key_store: APIKeyStore = Depends(get_key_store)):
    raw_key, api_key = generate_api_key()
    key_store.store(api_key)
    return APIKeyResponse(
        key_id=api_key.key_id,
        raw_key=raw_key,
        created_at=int(api_key.created_at.timestamp()),
        is_active=api_key.is_active,
    )


@router.delete("/keys/{key_id}")
def deactivate_key(key_id: str, key_store: APIKeyStore = Depends(get_key_store)):
    success = key_store.deactivate(key_id)
    if not success:
        raise HTTPException(status_code=404, detail="Key not found or already inactive")
    return {"status": "deactivated"}


#
# Analytics (Overview Tab)
#

@router.get("/analytics")
def get_analytics(admin_store: AdminStore = Depends(get_admin_store)):
    return admin_store.get_analytics()


#
# Billing (Billing Tab)
#

@router.get("/billing")
def get_billing(admin_store: AdminStore = Depends(get_admin_store)):
    return admin_store.get_billing()


#
# Users (Users Tab)
#

@router.get("/users")
def list_users(storage: StorageBackend = Depends(get_storage_backend)):
    # Simply list the user_ids currently enrolled
    return {"users": storage.list_users()}


#
# Settings (Settings Tab)
#

@router.get("/settings")
def get_settings(admin_store: AdminStore = Depends(get_admin_store)):
    return admin_store.get_settings()


@router.put("/settings/{key}")
def update_setting(
    key: str, update: SettingUpdate, admin_store: AdminStore = Depends(get_admin_store)
):
    admin_store.set_setting(key, update.value)
    return {"status": "updated", "key": key, "value": update.value}
