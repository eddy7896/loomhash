"""Storage contract for the (user_id, seed, loom_hash) tuple.

Resolves docs/open-decisions.md D-10. Any concrete backend -- in-memory
fake, Postgres+Redis, or otherwise -- must satisfy this interface and its
documented semantics:

- enroll() upserts: re-enrolling an existing user_id overwrites the prior
  record. No history/versioning is kept in this prototype.
- delete() must remove the record from every backing store the
  implementation uses, and must return True only if that removal is
  confirmed complete everywhere. It must never report success while any
  backing store still holds the seed -- a partial failure is a failure,
  not a best-effort success (see the revocation-failure resolution in
  docs/open-decisions.md). Deleting an unknown user_id is a no-op success.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass


@dataclass(frozen=True)
class EnrollmentRecord:
    user_id: str
    seed: bytes
    loom_hash: bytes
    lsh_version: int


class StorageBackend(abc.ABC):
    @abc.abstractmethod
    def enroll(self, record: EnrollmentRecord) -> None:
        """Upsert record, overwriting any existing record for record.user_id."""

    @abc.abstractmethod
    def get(self, user_id: str) -> EnrollmentRecord | None:
        """The stored record for user_id, or None if never enrolled or fully revoked."""

    @abc.abstractmethod
    def delete(self, user_id: str) -> bool:
        """Remove user_id's record everywhere. True only if confirmed complete."""
