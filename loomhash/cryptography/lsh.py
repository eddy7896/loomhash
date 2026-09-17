"""Seeded LSH projection.

Resolves docs/open-decisions.md D-03. Random-hyperplane (SimHash-style)
projection: a HASH_BITS x VECTOR_DIM matrix of iid standard-normal samples,
deterministically generated from a 32-byte seed, converts a 128-d feature
vector into a 256-bit hash by taking the sign of each projected component.

LSH_VERSION exists because changing any parameter here (distribution, bit
count, sign rule, packing order) makes new hashes incomparable with hashes
produced by a previous version. Bump it, and document the change in
docs/open-decisions.md, before altering this module's behavior.
"""

import secrets

import numpy as np

VECTOR_DIM = 128
HASH_BITS = 256
LSH_VERSION = 1


def generate_seed() -> bytes:
    """A fresh random 32-byte seed (ENR-04)."""
    return secrets.token_bytes(32)


def _rng_from_seed(seed: bytes) -> np.random.Generator:
    if len(seed) != 32:
        raise ValueError(f"seed must be exactly 32 bytes, got {len(seed)}")
    seed_int = int.from_bytes(seed, "big")
    return np.random.default_rng(seed_int)


def projection_matrix(seed: bytes) -> np.ndarray:
    """The HASH_BITS x VECTOR_DIM matrix of iid N(0, 1) samples for this seed."""
    rng = _rng_from_seed(seed)
    return rng.standard_normal((HASH_BITS, VECTOR_DIM))


def project(vector, seed: bytes) -> int:
    """Project a 128-d vector into a 256-bit integer hash under the given seed.

    Bit i is 1 if the i-th projected component is >= 0, else 0. Bits are
    packed MSB-first: bit 0 (from projection_matrix row 0) is the most
    significant bit of the returned integer.
    """
    vector = np.asarray(vector, dtype=np.float64)
    if vector.shape != (VECTOR_DIM,):
        raise ValueError(f"vector must have shape ({VECTOR_DIM},), got {vector.shape}")

    matrix = projection_matrix(seed)
    projected = matrix @ vector

    hash_int = 0
    for value in projected:
        hash_int = (hash_int << 1) | int(value >= 0)
    return hash_int
