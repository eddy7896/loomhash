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

## D-03 is resolved — implementation exists

The seeded-LSH definition (projection distribution, seed-to-RNG mapping, sign rule, precision, bit order) was approved 2026-09-17 and is implemented in [../../loomhash/cryptography/lsh.py](../../loomhash/cryptography/lsh.py) as `LSH_VERSION = 1`, with matching logic in [../../loomhash/cryptography/matching.py](../../loomhash/cryptography/matching.py). Tests against synthetic (non-biometric) vectors live in [../../tests/test_cryptography/](../../tests/test_cryptography/). See the resolution text in [../open-decisions.md](../open-decisions.md) for the exact parameters.

**Do not change any parameter of the existing scheme (distribution, HASH_BITS, sign rule, packing order) without bumping `LSH_VERSION` and recording the change in open-decisions.md** — doing so silently would make new hashes incomparable with every previously stored hash.

## What is still NOT covered by this module

- Real biometric evaluation (genuine/impostor accuracy) — the existing tests only establish algorithmic determinism and boundary correctness with synthetic vectors, not biometric accuracy. See the proposed validation sequence in [../open-decisions.md](../open-decisions.md).
- Any formal zero-knowledge proof property (D-08, deferred) — this module is a similarity-hashing scheme, not a ZK protocol, unless and until that's separately designed and approved.

## Related requirements / decisions

Requirements: ENR-04, AUT-02, AUT-03, AUT-04. Open decisions: D-03 (resolved).
