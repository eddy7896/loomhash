# Verification checklist

Living document. One row per functional requirement from [requirements.md](requirements.md). A status changes only when real evidence exists — a test run, a reviewed fixture, a reproducible check — not because code was written. See [memory-system.md](memory-system.md) for the update protocol.

Status values: **Pending** (not yet implemented or not yet tested), **Verified** (evidence exists and is linked), **Blocked** (cannot be verified until a listed open decision is resolved).

| ID | Requirement | Status | Blocked by | Evidence |
| --- | --- | --- | --- | --- |
| ENR-01 | Capture 12 views across a 1s yaw rotation | Pending | D-02 | — |
| ENR-02 | Compute mean 3D landmarks -> 128-d rigid-distance vector | Pending | D-01 | — |
| ENR-03 | Transmit only the numerical vector | Pending | D-05 (identity/control metadata) | — |
| ENR-04 | Random 32-byte seed + seeded LSH -> 256-bit loom_hash | Verified (algorithmic only) | — | `generate_seed`/`project` in [loomhash/cryptography/lsh.py](../loomhash/cryptography/lsh.py), tested in [tests/test_cryptography/test_lsh.py](../tests/test_cryptography/test_lsh.py) (determinism, seed/vector sensitivity, range, input validation) against synthetic vectors. Biometric-accuracy evaluation is separately required per the proposed validation sequence below before this can be called biometrically verified. |
| ENR-05 | Persist (user_id, seed, loom_hash) | Verified (contract only) | — | `InMemoryStorageBackend` in [loomhash/storage/memory.py](../loomhash/storage/memory.py), contract tested in [tests/test_storage/test_contract.py](../tests/test_storage/test_contract.py) (round-trip, upsert-on-re-enroll, per-user isolation). `PostgresStorageBackend`/`RedisEnrollmentCache`/`PostgresRedisStorageBackend` implement the same contract but are **not** integration-tested — no live Postgres/Redis in this environment; only import/construction checked in `test_adapters_construct.py`. |
| AUT-01 | Single-frame capture -> same 128-d feature representation | Pending | D-01, D-02 | — |
| AUT-02 | Retrieve stored seed/template, project query with stored seed | Verified (contract only) | — | Same evidence as ENR-05 — `get()` tested via the in-memory fake; real-backend retrieval untested against live services. |
| AUT-03 | `(stored_hash ^ query_hash).bit_count() / 256.0` | Verified | — | `hamming_distance` in [loomhash/cryptography/matching.py](../loomhash/cryptography/matching.py), tested in [tests/test_cryptography/test_matching.py](../tests/test_cryptography/test_matching.py) against known bit-pattern hashes (identical, fully-different, 51-bit-difference cases). |
| AUT-04 | 200 if distance <= 0.20 else 401 | Verified (matching logic only) | — | `is_match` boundary tested at exactly 51/256 (accept) and 52/256 (reject) in `test_matching.py::TestIsMatch`. The actual HTTP 200/401 response mapping is not yet implemented (no API gateway code exists) — this row covers only the threshold decision `is_match` encodes. |
| REV-01 | Delete user's seed from PostgreSQL and Redis on revocation | Verified (contract only) | — | `delete()`'s both-stores-must-succeed-or-fail semantics tested via the in-memory fake in `test_contract.py` (`test_delete_removes_record`, `test_delete_is_idempotent_for_unknown_user`). `PostgresRedisStorageBackend.delete()` implements the same `postgres_ok and cache_ok` rule but is untested against live services — partial-failure behavior (one store succeeds, the other doesn't) has no test at all yet, in-memory or real, since the in-memory fake has no way to fail. |

## How to fill in evidence

- For a deterministic/algorithmic requirement (e.g., AUT-03's boundary math), evidence is a link or path to the test file plus the specific cases run (e.g., "51 differing bits -> accept, 52 -> reject, tested in `tests/test_matching.py::test_boundary`").
- For a requirement involving real biometric input (e.g., ENR-01/ENR-02), evidence must reference the consented evaluation protocol described in [open-decisions.md](open-decisions.md)'s proposed validation sequence — not a single developer's own face tested once.
- For a storage/lifecycle requirement (e.g., ENR-05, REV-01), evidence is the specific adapter test plus which failure modes (partial write, concurrent access) were exercised.
- If a row is marked Verified, the evidence field must be specific enough for another agent to re-run or re-check it without asking the original author.

## Current state

Every row is Pending: no application code exists yet (see STATUS.md). This table exists now so that as soon as implementation starts, "done" means "verified here," not "code was written."
