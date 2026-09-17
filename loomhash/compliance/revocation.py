"""Consent-revocation handling (REV-01, Compliance module).

Owns revocation-event authorization and delegates the actual deletion to a
StorageBackend -- it does not re-implement Storage's delete logic (see
architecture.md: this module's job is event handling and authorization,
Storage's job is the deletion mechanics).

There is currently no caller-authentication/authorization model at all
(D-05 was resolved only in its minimal, prototype-scope form: the
integrating application is trusted -- see docs/open-decisions.md).
is_authorized() is a placeholder that always allows. It exists as the seam
where real authorization gets plugged in once D-05's full hardening is
scoped, so that change touches this one function instead of every call
site (including the API Gateway route).
"""

from __future__ import annotations

from loomhash.storage import StorageBackend


class RevocationDenied(Exception):
    """Raised when a revocation request is not authorized."""


def is_authorized(user_id: str) -> bool:
    """Placeholder authorization check -- always allows (D-05 minimal scope)."""
    return True


def revoke(storage: StorageBackend, user_id: str) -> bool:
    """Process a consent-revocation event for user_id (REV-01).

    Raises RevocationDenied if not authorized. Otherwise returns whatever
    storage.delete() returns: True only if the seed is confirmed removed
    from every backing store, per StorageBackend's contract -- a partial
    failure must never be reported as success.
    """
    if not is_authorized(user_id):
        raise RevocationDenied(f"revocation not authorized for user_id={user_id!r}")
    return storage.delete(user_id)
