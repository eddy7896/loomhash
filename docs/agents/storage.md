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

## What is NOT yet defined — do not invent it

Per [../open-decisions.md](../open-decisions.md) D-10, none of the following are approved yet: exact table/schema design, Redis key format and TTL/eviction policy, cache-vs-database authority on conflicting reads, enrollment-replacement policy (re-enroll overwrites vs. rejects vs. versions), and revocation's partial-failure/consistency behavior across the two stores (see [../architecture.md](../architecture.md)'s trust-boundary note on this race). Do not invent a schema or migration and present it as settled — propose it and flag it as a proposal pending approval.

## Related requirements / decisions

Requirements: ENR-05, AUT-02, REV-01. Open decisions: D-05 (identity/user_id origin), D-06 (memory-constraint wording clarification), D-10.
