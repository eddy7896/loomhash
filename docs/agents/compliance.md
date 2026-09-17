# Agent context: Compliance module

Read this before touching consent-revocation/crypto-shredding code. Also read [../memory-system.md](../memory-system.md)'s session-start protocol first.

## Role

Event listener for consent revocation. On a revocation event, deletes the affected user's cryptographic seed from PostgreSQL and Redis (delegating the actual delete to the Storage module's adapters — this module owns the *event handling and authorization*, not a second copy of the delete logic).

## I/O contract

- **In:** a revocation event for a user_id.
- **Out:** seed deleted from both stores; subsequent authentication for that user_id can no longer succeed (see REV-01).

## Implementation exists

Implemented in [../../loomhash/compliance/revocation.py](../../loomhash/compliance/revocation.py):

- `revoke(storage, user_id)` — the entry point. Calls `is_authorized(user_id)` first, raises `RevocationDenied` if it returns False, otherwise delegates to `storage.delete(user_id)` and returns its result unchanged (True only if confirmed gone everywhere, per the StorageBackend contract resolved in D-10).
- `is_authorized(user_id)` — **currently a placeholder that always returns True.** D-05 was only resolved in its minimal, prototype-scope form (the integrating application is trusted, no real caller authentication exists anywhere in this system yet). This function is the seam where real authorization gets plugged in later — every call site already goes through it, so that future change touches only this function, not the API Gateway route or Storage.

The API Gateway's `DELETE /v1/users/{user_id}` calls this module's `revoke()` rather than calling `storage.delete()` directly (see [api-gateway.md](api-gateway.md)) — that's what keeps the Compliance/Storage boundary real instead of just a paper distinction.

**Do not treat `is_authorized`'s current behavior as a real authorization decision** — it is a deliberate placeholder, not an oversight, and not evidence that revocation is actually protected against arbitrary callers.

Idempotent no-op for an unrecovered/unknown user_id is confirmed (`storage.delete()` already handles this per its own contract). Partial-failure handling (one store succeeds, one fails) is now tested at the API/Compliance boundary via a stub backend that always reports failure (see [../verification-checklist.md](../verification-checklist.md)'s REV-01 row) — but the *real* Postgres/Redis adapter's behavior under an actual partial outage remains untested, since no live instance of either exists in this environment.

## Legal/compliance claims — do not assert these in code comments or responses

Per [../open-decisions.md](../open-decisions.md) D-09, deleting a seed prevents the *specified future projection*, provided every usable copy (including backups/replicas/in-flight process memory) is actually gone. That is a narrower and more conditional claim than "converts pseudonymous data into fully anonymized data." Do not write code, docstrings, or API responses that assert full legal anonymization or DPDP/GDPR compliance as an established fact — that determination is outside this module's (or any single agent's) authority. Also note: system.md's "DPDP Act 2026" reference does not match the actual named law (Digital Personal Data Protection Act, 2023, with Rules 2025) — don't propagate that name into new documentation without flagging the discrepancy.

## Related requirements / decisions

Requirements: REV-01. Open decisions: D-05 (resolved, minimal — `is_authorized` reflects exactly that scope), D-09 (deferred), D-10 (resolved).
