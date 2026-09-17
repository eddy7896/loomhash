"""Redis write-through cache for enrollments (D-10).

Not authoritative: PostgresStorageBackend is the source of truth. A cache
miss or a Redis failure must fall back to Postgres and must never invent
data. Requires a reachable Redis instance and the redis-py driver (added
to pyproject.toml with explicit user approval on 2026-09-17 -- see
STATUS.md). No Redis instance is available in the development environment
this was written in, so this adapter is import/construction-tested only;
it has not been run against a real Redis. Treat it as Pending in
docs/verification-checklist.md until it has.
"""

from __future__ import annotations

import redis

from .backend import EnrollmentRecord

KEY_PREFIX = "loomhash:enrollment:"


class RedisEnrollmentCache:
    def __init__(self, client: redis.Redis) -> None:
        self._client = client

    @staticmethod
    def _key(user_id: str) -> str:
        return f"{KEY_PREFIX}{user_id}"

    def put(self, record: EnrollmentRecord) -> None:
        self._client.hset(
            self._key(record.user_id),
            mapping={
                "seed": record.seed,
                "loom_hash": record.loom_hash,
                "lsh_version": record.lsh_version,
            },
        )

    def get(self, user_id: str) -> EnrollmentRecord | None:
        data = self._client.hgetall(self._key(user_id))
        if not data:
            return None
        return EnrollmentRecord(
            user_id=user_id,
            seed=data[b"seed"],
            loom_hash=data[b"loom_hash"],
            lsh_version=int(data[b"lsh_version"]),
        )

    def delete(self, user_id: str) -> bool:
        self._client.delete(self._key(user_id))
        return self.get(user_id) is None
