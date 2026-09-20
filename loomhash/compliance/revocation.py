"""Consent-revocation handling (REV-01, Compliance module).

Owns revocation-event authorization and delegates the actual deletion to a
StorageBackend -- it does not re-implement Storage's delete logic (see
architecture.md: this module's job is event handling and authorization,
Storage's job is the deletion mechanics).

D-05 hardened: is_authorized() now requires a validated APIKey. For the
prototype, any valid active key is authorized to revoke any user_id.
The seam remains for future per-key authorization scoping (e.g.
integrating-application → user_id ownership).
"""

from __future__ import annotations

from loomhash.auth import APIKey
from loomhash.storage import StorageBackend


class RevocationDenied(Exception):
    """Raised when a revocation request is not authorized."""


def is_authorized(api_key: APIKey, user_id: str) -> bool:
    """Authorization check for revocation.

    Prototype scope: any valid, active API key is authorized to revoke any
    user_id. The api_key has already been cryptographically verified by the
    API gateway before reaching this function.

    Future hardening: restrict revocation to the API key that performed
    the original enrollment, or to keys with a specific ``scope`` claim.
    """
    return api_key.is_active


def revoke(storage: StorageBackend, api_key: APIKey, user_id: str) -> bool:
    """Process a consent-revocation event for user_id (REV-01).

    Raises RevocationDenied if not authorized. Otherwise returns whatever
    storage.delete() returns: True only if the seed is confirmed removed
    from every backing store, per StorageBackend's contract -- a partial
    failure must never be reported as success.
    """
    if not is_authorized(api_key, user_id):
        raise RevocationDenied(f"revocation not authorized for user_id={user_id!r}")
    return storage.delete(user_id)
