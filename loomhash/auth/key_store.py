"""API key storage backends.

APIKeyStore is the abstract contract; InMemoryAPIKeyStore is for tests and
the dev server, PostgresAPIKeyStore is for production (shares the existing
psycopg dependency with loomhash.storage.postgres).
"""

from __future__ import annotations

import abc
from datetime import datetime, timezone

from .auth import APIKey


class APIKeyStore(abc.ABC):
    """Contract for storing and retrieving hashed API keys."""

    @abc.abstractmethod
    def get_by_id(self, key_id: str) -> APIKey | None:
        """Return the APIKey record for key_id, or None if not found."""

    @abc.abstractmethod
    def store(self, key: APIKey) -> None:
        """Persist an APIKey record. Overwrites if key_id already exists."""

    @abc.abstractmethod
    def deactivate(self, key_id: str) -> bool:
        """Mark key_id as inactive. Returns True if key existed and was deactivated."""

    @abc.abstractmethod
    def list_keys(self) -> list[APIKey]:
        """Return all APIKey records, sorted by created_at descending."""


class InMemoryAPIKeyStore(APIKeyStore):
    """Non-durable in-memory store. For tests and local dev only."""

    def __init__(self) -> None:
        self._keys: dict[str, APIKey] = {}

    def get_by_id(self, key_id: str) -> APIKey | None:
        return self._keys.get(key_id)

    def store(self, key: APIKey) -> None:
        self._keys[key.key_id] = key

    def deactivate(self, key_id: str) -> bool:
        existing = self._keys.get(key_id)
        if existing is None:
            return False
        # APIKey is frozen, so we replace with a copy
        self._keys[key_id] = APIKey(
            key_id=existing.key_id,
            key_hash=existing.key_hash,
            salt=existing.salt,
            created_at=existing.created_at,
            is_active=False,
        )
        return True

    def list_keys(self) -> list[APIKey]:
        return sorted(self._keys.values(), key=lambda k: k.created_at, reverse=True)


class PostgresAPIKeyStore(APIKeyStore):
    """Postgres-backed API key store.

    Uses the same psycopg connection pattern as loomhash.storage.postgres.
    Imports psycopg at class level so ``import loomhash.auth`` never requires
    psycopg unless PostgresAPIKeyStore is actually instantiated.
    """

    def __init__(self, conninfo: str) -> None:
        import psycopg

        self._conninfo = conninfo
        self._conn = psycopg.connect(conninfo, autocommit=True)

    def ensure_schema(self) -> None:
        """Create the api_keys table if it doesn't exist."""
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS api_keys (
                key_id     TEXT PRIMARY KEY,
                key_hash   BYTEA NOT NULL,
                salt       BYTEA NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                is_active  BOOLEAN NOT NULL DEFAULT TRUE
            )
            """
        )

    def get_by_id(self, key_id: str) -> APIKey | None:
        row = self._conn.execute(
            "SELECT key_id, key_hash, salt, created_at, is_active "
            "FROM api_keys WHERE key_id = %s",
            (key_id,),
        ).fetchone()
        if row is None:
            return None
        return APIKey(
            key_id=row[0],
            key_hash=bytes(row[1]),
            salt=bytes(row[2]),
            created_at=row[3] if row[3].tzinfo else row[3].replace(tzinfo=timezone.utc),
            is_active=row[4],
        )

    def store(self, key: APIKey) -> None:
        self._conn.execute(
            """
            INSERT INTO api_keys (key_id, key_hash, salt, created_at, is_active)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (key_id) DO UPDATE SET
                key_hash = EXCLUDED.key_hash,
                salt = EXCLUDED.salt,
                created_at = EXCLUDED.created_at,
                is_active = EXCLUDED.is_active
            """,
            (key.key_id, key.key_hash, key.salt, key.created_at, key.is_active),
        )

    def deactivate(self, key_id: str) -> bool:
        cur = self._conn.execute(
            "UPDATE api_keys SET is_active = FALSE WHERE key_id = %s AND is_active = TRUE",
            (key_id,),
        )
        return cur.rowcount > 0

    def list_keys(self) -> list[APIKey]:
        rows = self._conn.execute(
            "SELECT key_id, key_hash, salt, created_at, is_active "
            "FROM api_keys ORDER BY created_at DESC"
        ).fetchall()
        
        return [
            APIKey(
                key_id=row[0],
                key_hash=bytes(row[1]),
                salt=bytes(row[2]),
                created_at=row[3] if row[3].tzinfo else row[3].replace(tzinfo=timezone.utc),
                is_active=row[4],
            )
            for row in rows
        ]
