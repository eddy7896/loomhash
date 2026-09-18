# Agent context: Storage module

Read this before touching PostgreSQL/Redis adapters or schema. Also read [../memory-system.md](../memory-system.md)'s session-start protocol first.

## Role

Persist and retrieve the logical (user_id, seed, loom_hash) tuple via PostgreSQL (durable) and Redis (hot lookup cache). Nothing else defines identity linkage or template storage.

## I/O contract

- **Write (enrollment):** user_id, 32-byte seed, 256-bit loom_hash.
- **Read (authentication):** given a user_id, return its seed and loom_hash.
- **Delete (revocation):** given a user_id, remove its seed from both PostgreSQL and Redis.

## Immutable constraints that apply here

- **Constraint 3 (Data Privacy):** only vectors/hashes/seeds and their identifiers may be persisted. Never write raw frames, meshes, or images to any table, cache key, or log — including debug/error logs that might accidentally serialize a request body.

## D-10, D-05 (minimal), and D-06 are resolved — implementation exists

Schema, cache policy, replacement policy, and revocation semantics were approved 2026-09-17; see the resolution text in [../open-decisions.md](../open-decisions.md). Implemented in [../../loomhash/storage/](../../loomhash/storage/):

- `backend.py` — the `StorageBackend` abstract contract and `EnrollmentRecord`. Any new backend must satisfy this.
- `memory.py` — `InMemoryStorageBackend`, a non-durable fake used for tests.
- `postgres.py` — `PostgresStorageBackend`, the durable source of truth (Postgres table `enrollments`).
- `redis_cache.py` — `RedisEnrollmentCache`, a write-through cache, never authoritative.
- `combined.py` — `PostgresRedisStorageBackend`, wiring the two together per the write-through design; `delete()` only reports success if both stores confirm removal.

`psycopg` and `redis-py` were approved as new dependencies for this (see pyproject.toml).

**Resolved 2026-09-18:** the user ran [../../scripts/verify_live_storage.py](../../scripts/verify_live_storage.py) against real Docker-hosted PostgreSQL 16 + Redis 7 on their VPS (see [../../deploy/](../../deploy/)) and it passed — schema creation, enroll, get (through the write-through cache), and delete (confirmed gone from both stores) all work against live services, not just `InMemoryStorageBackend`. `tests/test_storage/test_adapters_construct.py` is now superseded for this purpose (it only checked import/construction).

**What's still NOT covered:** a real partial-outage scenario — one store genuinely failing while the other succeeds mid-`delete()` — has never been exercised against the real adapters. `test_revoke_returns_500_when_storage_reports_incomplete_deletion` proves the API/Compliance layer reacts correctly *when told* deletion failed (via a stub), not that `PostgresRedisStorageBackend` correctly detects a real partial failure. Concurrent-access and cache-eviction/TTL behavior are also untested against real infra. See [../verification-checklist.md](../verification-checklist.md)'s REV-01 row for the exact scope.

## What is still NOT defined

Full caller authentication/authorization (beyond the minimal "trusted caller-supplied user_id" resolution of D-05), API routes/request shapes (that's the API Gateway module's job), and TTL/eviction policy for the Redis cache (current design has no TTL — cache entries live until explicitly overwritten or deleted).

## Related requirements / decisions

Requirements: ENR-05, AUT-02, REV-01. Open decisions: D-05 (resolved, minimal), D-06 (resolved), D-10 (resolved).
