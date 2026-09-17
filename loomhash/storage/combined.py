"""Combined Postgres + Redis StorageBackend (D-10 resolution).

Postgres is the source of truth; Redis is a write-through cache consulted
first on read and populated on write and on cache-miss reads. delete()
only reports success if both stores confirm the record is gone -- see the
revocation-failure resolution in docs/open-decisions.md.

Not integration-tested against live services -- see postgres.py and
redis_cache.py.
"""

from __future__ import annotations

from .backend import EnrollmentRecord, StorageBackend
from .postgres import PostgresStorageBackend
from .redis_cache import RedisEnrollmentCache


class PostgresRedisStorageBackend(StorageBackend):
    def __init__(self, postgres: PostgresStorageBackend, cache: RedisEnrollmentCache) -> None:
        self._postgres = postgres
        self._cache = cache

    def enroll(self, record: EnrollmentRecord) -> None:
        self._postgres.enroll(record)
        self._cache.put(record)

    def get(self, user_id: str) -> EnrollmentRecord | None:
        cached = self._cache.get(user_id)
        if cached is not None:
            return cached
        record = self._postgres.get(user_id)
        if record is not None:
            self._cache.put(record)
        return record

    def delete(self, user_id: str) -> bool:
        postgres_ok = self._postgres.delete(user_id)
        cache_ok = self._cache.delete(user_id)
        return postgres_ok and cache_ok
