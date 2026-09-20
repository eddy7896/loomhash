"""In-memory fake StorageBackend. For tests only.

Single-process, non-durable, not shared across processes. It exists so the
storage contract's logic (upsert-on-re-enroll, delete semantics) can be
tested without a live Postgres/Redis instance. Real persistence is
PostgresRedisStorageBackend (loomhash/storage/combined.py).
"""

from __future__ import annotations

from .backend import EnrollmentRecord, StorageBackend


class InMemoryStorageBackend(StorageBackend):
    def __init__(self) -> None:
        self._records: dict[str, EnrollmentRecord] = {}

    def enroll(self, record: EnrollmentRecord) -> None:
        self._records[record.user_id] = record

    def get(self, user_id: str) -> EnrollmentRecord | None:
        return self._records.get(user_id)

    def delete(self, user_id: str) -> bool:
        self._records.pop(user_id, None)
        return user_id not in self._records

    def list_users(self) -> list[str]:
        return list(self._records.keys())
