#!/usr/bin/env python3
"""Round-trip check against REAL Postgres/Redis instances (not the
in-memory fake). Confirms loomhash.storage.combined.PostgresRedisStorageBackend
actually works against live services -- something the automated test suite
can't do on its own (see docs/verification-checklist.md's ENR-05/AUT-02/
REV-01 rows, which flag this exact gap).

Run this after `docker compose up -d` in deploy/ (on the VPS itself, or
from a dev machine through an SSH tunnel to the VPS -- see
deploy/README.md), with:

    POSTGRES_CONNINFO="postgresql://loomhash:PASSWORD@127.0.0.1:5432/loomhash" \\
    REDIS_PASSWORD="PASSWORD" \\
    python scripts/verify_live_storage.py

REDIS_HOST/REDIS_PORT default to 127.0.0.1/6379 (override if tunneled to
different local ports).

This is a manual verification tool, not part of the automated guardrail
scripts (check_constraints.py/check_docs.py) or the pytest/unittest suite
-- it requires live infrastructure that doesn't exist in CI or in most
development environments.
"""

import os
import sys
from pathlib import Path

# Run standalone (python scripts/verify_live_storage.py) without needing
# `pip install -e .` or a manually-set PYTHONPATH first.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import redis

from loomhash.storage.backend import EnrollmentRecord
from loomhash.storage.combined import PostgresRedisStorageBackend
from loomhash.storage.postgres import PostgresStorageBackend
from loomhash.storage.redis_cache import RedisEnrollmentCache

TEST_USER_ID = "loomhash-live-verify-test-user"


def main() -> int:
    conninfo = os.environ.get("POSTGRES_CONNINFO")
    redis_host = os.environ.get("REDIS_HOST", "127.0.0.1")
    redis_port = int(os.environ.get("REDIS_PORT", "6379"))
    redis_password = os.environ.get("REDIS_PASSWORD")

    if not conninfo:
        print("Set POSTGRES_CONNINFO -- see this script's docstring.", file=sys.stderr)
        return 1
    if not redis_password:
        print("Set REDIS_PASSWORD -- see this script's docstring.", file=sys.stderr)
        return 1

    print("Connecting to Postgres and ensuring schema...")
    postgres = PostgresStorageBackend(conninfo)
    postgres.ensure_schema()
    print("  OK: schema ensured (enrollments table exists).")

    print("Connecting to Redis...")
    client = redis.Redis(host=redis_host, port=redis_port, password=redis_password)
    if not client.ping():
        print("  Redis did not respond to PING.", file=sys.stderr)
        return 1
    print("  OK: Redis reachable and authenticated.")

    cache = RedisEnrollmentCache(client)
    backend = PostgresRedisStorageBackend(postgres, cache)

    record = EnrollmentRecord(user_id=TEST_USER_ID, seed=b"s" * 32, loom_hash=b"h" * 32, lsh_version=1)

    print(f"Round-trip: enroll -> get (cache hit) -> delete for user_id={TEST_USER_ID!r}")
    backend.enroll(record)

    fetched = backend.get(TEST_USER_ID)
    if fetched != record:
        print(f"  FAIL: round-trip mismatch: {fetched!r} != {record!r}", file=sys.stderr)
        return 1
    print("  OK: enroll + get (write-through cache) round-trips correctly.")

    deleted = backend.delete(TEST_USER_ID)
    if not deleted:
        print("  FAIL: delete() reported failure.", file=sys.stderr)
        return 1
    if backend.get(TEST_USER_ID) is not None:
        print("  FAIL: record still present after delete().", file=sys.stderr)
        return 1
    print("  OK: delete confirmed gone from both Postgres and Redis.")

    print("\nAll checks passed against the real Postgres/Redis instances.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
