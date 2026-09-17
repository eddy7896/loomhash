# Agent context: Cryptography module

Read this before touching LSH projection or matching code. Also read [../memory-system.md](../memory-system.md)'s session-start protocol first.

## Role

Pure Python: seeded LSH projection of a 128-d vector into a 256-bit loom_hash, and Hamming-distance comparison between two 256-bit hashes. Nothing here is a general-purpose vector index — see constraint 1.

## I/O contract

- **Projection in:** 128-d vector + 32-byte seed. **Out:** 256-bit loom_hash.
- **Matching in:** stored_hash, query_hash (both 256-bit). **Out:** `distance = (stored_hash ^ query_hash).bit_count() / 256.0`, then 200/401 per AUT-04's 0.20 threshold (51/256 = 0.19921875 accepts, 52/256 = 0.203125 rejects — this boundary is derived directly from the spec, do not re-derive a different one).

## Immutable constraints that apply here

- **Constraint 1 (No Vector DBs for Identity):** never import or reach for `faiss`, `pinecone`, `pymilvus`/milvus, or any ANN index for identity matching. Matching is native `int.bit_count()` XOR only, full stop — not an approximation, not a fallback path.
- **Constraint 2 (Python Version):** target Python >= 3.10. Hamming distance must use `int.bit_count()`, not `bin(x).count('1')` or a NumPy popcount trick.
- **Constraint 3 (Data Privacy):** this module only ever handles vectors, seeds, and hashes — never raw images. It should not need to import any image library at all; if it does, stop and ask why.

## What is NOT yet defined — do not invent it

Per [../open-decisions.md](../open-decisions.md) D-03, "seeded LSH" has no approved concrete definition yet: projection matrix distribution and dimensions, how the 32-byte seed maps to the RNG, the sign/tie-breaking rule for binarization, numeric precision, and bit ordering. Do not pick one silently — the entire security and matching-accuracy story depends on this choice, and it needs explicit sign-off plus a documented version identifier so a future change doesn't silently break existing enrollments.

## Related requirements / decisions

Requirements: ENR-04, AUT-02, AUT-03, AUT-04. Open decisions: D-03. Deferred for the prototype milestone: any formal zero-knowledge proof property (D-08) — this module is a similarity-hashing scheme, not a ZK protocol, unless and until that's separately designed and approved.
