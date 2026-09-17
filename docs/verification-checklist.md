# Verification checklist

Living document. One row per functional requirement from [requirements.md](requirements.md). A status changes only when real evidence exists — a test run, a reviewed fixture, a reproducible check — not because code was written. See [memory-system.md](memory-system.md) for the update protocol.

Status values: **Pending** (not yet implemented or not yet tested), **Verified** (evidence exists and is linked), **Blocked** (cannot be verified until a listed open decision is resolved).

| ID | Requirement | Status | Blocked by | Evidence |
| --- | --- | --- | --- | --- |
| ENR-01 | Capture 12 views across a 1s yaw rotation | Pending | D-02 | — |
| ENR-02 | Compute mean 3D landmarks -> 128-d rigid-distance vector | Pending | D-01 | — |
| ENR-03 | Transmit only the numerical vector | Pending | D-05 (identity/control metadata) | — |
| ENR-04 | Random 32-byte seed + seeded LSH -> 256-bit loom_hash | Pending | D-03 | — |
| ENR-05 | Persist (user_id, seed, loom_hash) | Pending | D-10 (schema) | — |
| AUT-01 | Single-frame capture -> same 128-d feature representation | Pending | D-01, D-02 | — |
| AUT-02 | Retrieve stored seed/template, project query with stored seed | Pending | D-10 | — |
| AUT-03 | `(stored_hash ^ query_hash).bit_count() / 256.0` | Pending | D-03 | — |
| AUT-04 | 200 if distance <= 0.20 else 401 | Pending | AUT-03 | — |
| REV-01 | Delete user's seed from PostgreSQL and Redis on revocation | Pending | D-05, D-10 | — |

## How to fill in evidence

- For a deterministic/algorithmic requirement (e.g., AUT-03's boundary math), evidence is a link or path to the test file plus the specific cases run (e.g., "51 differing bits -> accept, 52 -> reject, tested in `tests/test_matching.py::test_boundary`").
- For a requirement involving real biometric input (e.g., ENR-01/ENR-02), evidence must reference the consented evaluation protocol described in [open-decisions.md](open-decisions.md)'s proposed validation sequence — not a single developer's own face tested once.
- For a storage/lifecycle requirement (e.g., ENR-05, REV-01), evidence is the specific adapter test plus which failure modes (partial write, concurrent access) were exercised.
- If a row is marked Verified, the evidence field must be specific enough for another agent to re-run or re-check it without asking the original author.

## Current state

Every row is Pending: no application code exists yet (see STATUS.md). This table exists now so that as soon as implementation starts, "done" means "verified here," not "code was written."
