# LoomHash Project Status

## 2026-09-17 21:11:41 +05:30 — Project context initialized

- Saved the supplied architecture and agent directives verbatim in system.md.
- Workspace was empty before initialization; no application components have been implemented.
- No dependencies have been installed or added.
- Implementation scope remains pending user selection. Clarify ambiguous implementation details, API routes, and database schemas before implementing them, as required by system.md.
- Security, biometric accuracy, deepfake resistance, anonymization, and regulatory compliance claims in the supplied specification have not been validated.

## Next step

Review docs/open-decisions.md and resolve feature extraction, projection, and security-scope decisions before implementation.

## 2026-09-17 21:17:50 +05:30 — Initial documentation and requirements analysis completed

- Inspected the workspace and read system.md and STATUS.md; no pre-existing documentation folder or application code was present.
- Created docs/README.md, docs/requirements.md, docs/architecture.md, and docs/open-decisions.md.
- Mapped specified enrollment, authentication, and consent-revocation behavior to acceptance evidence and module responsibilities.
- Documented unresolved feature definitions, LSH determinism, ONNX integration, identity binding, memory constraints, replay resistance, and deletion lifecycle.
- Checked primary MediaPipe, ONNX Runtime, MeitY, and EDPB sources; linked references and distinguished analysis from specified requirements.
- Preserved system.md unchanged. No application code, dependencies, API routes, or database schemas were introduced.
- Verification: checked documentation links and the derived 51/52-bit matching boundary. Runtime tests are not applicable to this documentation-only change.

## 2026-09-17 — Documentation set expanded: memory, hallucination checks, use cases, per-module agent context

- Asked the user four scoping questions before writing: milestone target, agent-context file granularity, hallucination-check format, and live-tracking granularity. Answers: feasibility prototype, per-module agent files, checklist + automated script, and a dedicated verification-checklist.md alongside STATUS.md.
- Added docs/use-cases.md: actor-level UC-1 (enroll), UC-2 (authenticate), UC-3 (revoke) flows with prototype-scope vs. deferred edge cases.
- Added docs/memory-system.md documenting the file-based memory tiers (system.md, STATUS.md, open-decisions.md, verification-checklist.md) and the session start/end read-write protocol.
- Added docs/hallucination-checks.md operationalizing system.md's four immutable constraints and "Ask, Do Not Assume" rule into a pre-flight checklist.
- Added scripts/check_constraints.py, a heuristic grep-based scanner for forbidden vector-DB imports, server-side media-processing imports, raw-image-write patterns, and non-`int.bit_count()` popcount code. Ran it against the repo: 1 file scanned (itself), 0 hard violations, 3 expected self-referential warnings from its own pattern strings.
- Added docs/verification-checklist.md: one Pending row per requirement ID (ENR-01..REV-01), to be flipped to Verified only with linked evidence.
- Added docs/agents/{edge-extraction,cryptography,inference,storage,compliance,api-gateway}.md: per-module role, I/O contract, applicable immutable constraints, and explicitly undefined items not to be invented.
- Edited docs/open-decisions.md to add a "Resolved decisions" section recording the feasibility-prototype milestone choice and reclassifying D-01..D-10 as blocking vs. deferred under that scope.
- Updated docs/README.md's reading order and working rules to reference all new files.
- Verification: read every new/edited file back; ran the new script successfully. No application code, dependencies, API routes, or database schemas were introduced; system.md remains unchanged.

## 2026-09-17 — Guardrails and system checks wired up (git, hooks, CI, agent auto-load)

- Asked the user three scoping questions: whether to `git init` (yes), which guardrail layers to add (root CLAUDE.md, pre-commit hook, GitHub Actions CI, pyproject.toml Python pin — all four), and whether to add a doc-consistency doctor script beyond the constraint scanner (yes).
- Ran `git init` — this was previously not a git repository. No commit was made; files are left staged for the user to review and commit.
- Added scripts/check_docs.py: cross-checks that every requirement ID in docs/requirements.md appears in docs/verification-checklist.md, every D-xx decision ID referenced under docs/ is defined in docs/open-decisions.md, no verification-checklist.md row is marked Verified with an empty evidence cell, and all six docs/agents/*.md files exist. Ran it clean against the current docs.
- Added hooks/pre-commit (tracked) running both check_constraints.py and check_docs.py, and installed a shim at .git/hooks/pre-commit that execs the tracked copy so the logic stays versioned. Verified the installed hook runs and exits 0 against the current repo state.
- Added .github/workflows/guardrails.yml running both scripts on push/pull_request with Python 3.10.
- Added pyproject.toml declaring `requires-python = ">=3.10"` (constraint 2) and no dependencies.
- Added root CLAUDE.md so Claude Code auto-loads the session-start reading order, the four immutable constraints, the guardrail wiring, and the "Ask, Do Not Assume" working rules at the start of every session, rather than relying on being told to open docs/.
- Cross-linked the new guardrail files from docs/hallucination-checks.md (Enforcement section) and docs/memory-system.md (CLAUDE.md added to the memory-tier table).
- Verification: ran `python scripts/check_constraints.py` and `python scripts/check_docs.py` directly and via the installed pre-commit hook — all exit 0. No application code, dependencies (beyond the requires-python declaration), API routes, or database schemas were introduced; system.md remains unchanged.

## 2026-09-17 — Cryptography module: first implementation (D-03 resolved)

- Asked the user which module to start with; picked Cryptography as lowest-setup (pure Python, numpy already spec-approved, no new deps).
- Proposed a concrete resolution for D-03 (seeded LSH definition) before writing any code: random-hyperplane/SimHash projection, 256x128 iid N(0,1) matrix seeded via `numpy.random.default_rng(int.from_bytes(seed, "big"))`, sign-bit binarization (>=0 -> 1), MSB-first packing, float64, tagged `LSH_VERSION = 1`. User approved as proposed.
- Implemented loomhash/cryptography/lsh.py (`generate_seed`, `projection_matrix`, `project`) and loomhash/cryptography/matching.py (`hamming_distance`, `is_match`), satisfying constraint 1 (no vector-DB import) and constraint 2 (`int.bit_count()`, not a popcount fallback).
- Added tests/test_cryptography/{test_lsh,test_matching}.py using stdlib `unittest` (no new test-framework dependency added without consent): seed/vector determinism and validation with synthetic (non-biometric) vectors, plus the exact AUT-03/AUT-04 boundary (51/256 = 0.19921875 accepts, 52/256 = 0.203125 rejects). One test (`test_different_vector_gives_different_hash`) initially failed because a uniform `+1.0` vector shift happened not to cross zero on any of the 256 projected components for the fixed test seed — not an implementation bug, but a weak test; fixed by asserting against a negated vector instead, which is guaranteed (up to measure-zero exact-zero ties) to flip virtually every sign bit. All 14 tests now pass.
- Updated pyproject.toml: added `numpy>=1.24` as a dependency (already mandated by system.md section 3, not a new agent-introduced dependency) and setuptools packaging config so `loomhash` is installable.
- Updated docs/open-decisions.md: added D-03's resolution to the "Resolved decisions" table with the exact parameters and a pointer to the code; struck through the original D-03 row in the blocking table rather than deleting it.
- Updated docs/verification-checklist.md: ENR-04, AUT-03, and AUT-04 moved from Pending to Verified (algorithmic/matching-logic scope only — explicitly noted that biometric-accuracy evaluation and the actual HTTP 200/401 response mapping are still separate, unverified concerns), each with a link to the specific test file and cases.
- Updated docs/agents/cryptography.md to point at the implementation and warn that changing any LSH parameter now requires bumping `LSH_VERSION`.
- Verification: ran `python -m unittest discover -s tests -t .` (14/14 pass), `python scripts/check_constraints.py` (0 hard violations), and `python scripts/check_docs.py` (consistent) — all after these changes.

## 2026-09-17 — Storage module: second implementation (D-10, D-05 minimal, D-06 resolved)

- User picked Storage as the next module over Edge Extraction (lower setup cost, unblocks a full enroll->store->authenticate loop using the already-built cryptography module).
- Before writing code, checked for local infra: no psycopg/psycopg2/redis installed, and neither PostgreSQL (5432) nor Redis (6379) reachable on localhost in this environment.
- Asked three scoping questions and got explicit approval for each: (1) schema/cache design — Postgres `enrollments(user_id, seed, loom_hash, lsh_version, created_at, updated_at)` as source of truth, Redis as a write-through cache, upsert-on-re-enroll; (2) revocation failure semantics — delete() must report failure (not best-effort success) if either store fails, so a lingering cached seed can't defeat crypto-shredding; (3) dependency approach — add `psycopg[binary]` and `redis-py` now as new approved dependencies, even though neither can be integration-tested here without live services.
- Added `hash_to_bytes`/`hash_from_bytes` to loomhash/cryptography/lsh.py (32-byte big-endian serialization matching the existing MSB-first bit packing) so loom_hash can be stored as BYTEA/Redis-hash-field bytes; round-trip tested in test_lsh.py.
- Implemented loomhash/storage/: `backend.py` (StorageBackend ABC + EnrollmentRecord contract), `memory.py` (InMemoryStorageBackend, a non-durable fake for tests), `postgres.py` (PostgresStorageBackend using psycopg, upsert via `ON CONFLICT DO UPDATE`), `redis_cache.py` (RedisEnrollmentCache using redis-py, write-through, never authoritative), `combined.py` (PostgresRedisStorageBackend wiring both together; `delete()` returns `postgres_ok and cache_ok`). `loomhash/storage/__init__.py` deliberately does not import the Postgres/Redis modules at package level, so `import loomhash.storage` never requires those drivers to be importable.
- Installed psycopg[binary] and redis-py via pip in this environment and added both to pyproject.toml's dependencies with a comment explaining why (spec-mandated tech, explicitly approved, untested against live services).
- Added tests/test_storage/test_contract.py: a shared `StorageBackendContractTests` mixin (round-trip, upsert-on-re-enroll, per-user isolation, delete + idempotent delete, delete-then-re-enroll), run against `InMemoryStorageBackend`. Added test_adapters_construct.py: import/construction-only smoke tests for the Postgres/Redis adapters, explicitly documented as NOT exercising real database behavior since no live instance exists here.
- Updated docs/open-decisions.md: added D-10, D-05 (minimal/prototype-scope only), and D-06 to "Resolved decisions" with full parameters; struck through their rows in the blocking table; reclassified the summary paragraph so only D-01/D-02 (Edge Extraction) remain blocking among the non-deferred items.
- Updated docs/verification-checklist.md: ENR-05, AUT-02, and REV-01 moved to "Verified (contract only)", each evidence note explicitly flagging that the real Postgres/Redis adapters remain unverified against live services, and that REV-01's partial-failure path (one store succeeds, one fails) has no test at all yet because the in-memory fake has no way to fail.
- Updated docs/agents/storage.md to point at the implementation and flag the live-service testing gap prominently so a future agent doesn't mistake "contract verified" for "adapters proven against real Postgres/Redis."
- Verification: ran `python -m unittest discover -s tests -t .` (27/27 pass), `python scripts/check_constraints.py` (0 hard violations), and `python scripts/check_docs.py` (consistent).
