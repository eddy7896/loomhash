"""Hamming-distance matching between two 256-bit LoomHash values (AUT-03/AUT-04).

Native int.bit_count() only -- no vector-DB / ANN library, per system.md
constraint 1, and Python >= 3.10 for bit_count() availability, per constraint 2.
"""

from .lsh import HASH_BITS

MATCH_THRESHOLD = 0.20


def hamming_distance(hash_a: int, hash_b: int) -> float:
    """Normalized Hamming distance in [0.0, 1.0] between two HASH_BITS-bit hashes."""
    return (hash_a ^ hash_b).bit_count() / HASH_BITS


def is_match(hash_a: int, hash_b: int, threshold: float = MATCH_THRESHOLD) -> bool:
    """True if hash_a and hash_b are within threshold Hamming distance (AUT-04)."""
    return hamming_distance(hash_a, hash_b) <= threshold
