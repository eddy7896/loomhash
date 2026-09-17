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

**Important gap:** the Postgres/Redis adapters are import/construction-tested only (`tests/test_storage/test_adapters_construct.py`) — there is no live Postgres or Redis instance in this development environment, so none of the real query/cache/partial-failure behavior has actually been run. Treat `PostgresStorageBackend`, `RedisEnrollmentCache`, and `PostgresRedisStorageBackend` as unverified against real services until someone runs them against an actual PostgreSQL and Redis and updates [../verification-checklist.md](../verification-checklist.md) accordingly. The contract itself (upsert, delete semantics) is verified, but only via `InMemoryStorageBackend`.

## What is still NOT defined

Full caller authentication/authorization (beyond the minimal "trusted caller-supplied user_id" resolution of D-05), API routes/request shapes (that's the API Gateway module's job), and TTL/eviction policy for the Redis cache (current design has no TTL — cache entries live until explicitly overwritten or deleted).

## Related requirements / decisions

Requirements: ENR-05, AUT-02, REV-01. Open decisions: D-05 (resolved, minimal), D-06 (resolved), D-10 (resolved).
