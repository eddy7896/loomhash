"""PostgreSQL adapter: the durable source of truth for enrollments (D-10).

Requires a reachable PostgreSQL instance and the psycopg driver (added to
pyproject.toml with explicit user approval on 2026-09-17 -- see STATUS.md).
No PostgreSQL instance is available in the development environment this
was written in, so this adapter is import/construction-tested only; it has
not been run against a real database. Treat it as Pending in
docs/verification-checklist.md until it has.
"""

from __future__ import annotations

import psycopg

from .backend import EnrollmentRecord, StorageBackend

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS enrollments (
    user_id TEXT PRIMARY KEY,
    seed BYTEA NOT NULL,
    loom_hash BYTEA NOT NULL,
    lsh_version INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""

UPSERT_SQL = """
INSERT INTO enrollments (user_id, seed, loom_hash, lsh_version, updated_at)
VALUES (%s, %s, %s, %s, now())
ON CONFLICT (user_id) DO UPDATE SET
    seed = EXCLUDED.seed,
    loom_hash = EXCLUDED.loom_hash,
    lsh_version = EXCLUDED.lsh_version,
    updated_at = now();
"""

SELECT_SQL = "SELECT user_id, seed, loom_hash, lsh_version FROM enrollments WHERE user_id = %s;"

DELETE_SQL = "DELETE FROM enrollments WHERE user_id = %s;"


class PostgresStorageBackend(StorageBackend):
    def __init__(self, conninfo: str) -> None:
        self._conninfo = conninfo

    def _connect(self) -> psycopg.Connection:
        return psycopg.connect(self._conninfo)

    def ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(CREATE_TABLE_SQL)

    def enroll(self, record: EnrollmentRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                UPSERT_SQL,
                (record.user_id, record.seed, record.loom_hash, record.lsh_version),
            )

    def get(self, user_id: str) -> EnrollmentRecord | None:
        with self._connect() as conn:
            row = conn.execute(SELECT_SQL, (user_id,)).fetchone()
        if row is None:
            return None
        return EnrollmentRecord(
            user_id=row[0], seed=bytes(row[1]), loom_hash=bytes(row[2]), lsh_version=row[3]
        )

    def delete(self, user_id: str) -> bool:
        with self._connect() as conn:
            conn.execute(DELETE_SQL, (user_id,))
        return self.get(user_id) is None

    def list_users(self) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute("SELECT user_id FROM enrollments ORDER BY created_at DESC;").fetchall()
        return [row[0] for row in rows]
