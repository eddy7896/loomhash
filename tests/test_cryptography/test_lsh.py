"""Synthetic (non-biometric) checks for the seeded LSH projection (D-03).

These establish algorithm behavior only -- determinism, seed sensitivity,
and input validation. They say nothing about biometric accuracy, which
needs the consented evaluation protocol in docs/open-decisions.md.
"""

import unittest

from loomhash.cryptography import (
    HASH_BITS,
    VECTOR_DIM,
    generate_seed,
    hash_from_bytes,
    hash_to_bytes,
    project,
)


class TestGenerateSeed(unittest.TestCase):
    def test_seed_is_32_bytes(self):
        self.assertEqual(len(generate_seed()), 32)

    def test_seeds_are_not_repeated(self):
        seeds = {generate_seed() for _ in range(100)}
        self.assertEqual(len(seeds), 100)


class TestProject(unittest.TestCase):
    def setUp(self):
        self.seed_a = bytes(range(32))
        self.seed_b = bytes(range(1, 33))
        self.vector = [float(i) for i in range(VECTOR_DIM)]

    def test_hash_is_in_valid_range(self):
        h = project(self.vector, self.seed_a)
        self.assertGreaterEqual(h, 0)
        self.assertLess(h, 2 ** HASH_BITS)

    def test_deterministic_for_same_seed_and_vector(self):
        h1 = project(self.vector, self.seed_a)
        h2 = project(self.vector, self.seed_a)
        self.assertEqual(h1, h2)

    def test_different_seed_gives_different_hash(self):
        h_a = project(self.vector, self.seed_a)
        h_b = project(self.vector, self.seed_b)
        self.assertNotEqual(h_a, h_b)

    def test_different_vector_gives_different_hash(self):
        # Negating the vector flips the sign of every projected component
        # (matrix @ (-v) == -(matrix @ v)), so it should flip virtually every
        # bit -- unlike an arbitrary shift, which can coincidentally cross
        # zero on none of the 256 rows for a given seed.
        negated_vector = [-v for v in self.vector]
        h1 = project(self.vector, self.seed_a)
        h2 = project(negated_vector, self.seed_a)
        self.assertNotEqual(h1, h2)

    def test_rejects_wrong_length_seed(self):
        with self.assertRaises(ValueError):
            project(self.vector, b"too-short")

    def test_rejects_wrong_length_vector(self):
        with self.assertRaises(ValueError):
            project(self.vector[:-1], self.seed_a)


class TestHashBytesRoundTrip(unittest.TestCase):
    def test_round_trips(self):
        h = project([float(i) for i in range(VECTOR_DIM)], bytes(range(32)))
        self.assertEqual(hash_from_bytes(hash_to_bytes(h)), h)

    def test_bytes_length_is_32(self):
        h = project([float(i) for i in range(VECTOR_DIM)], bytes(range(32)))
        self.assertEqual(len(hash_to_bytes(h)), HASH_BITS // 8)

    def test_rejects_wrong_length_bytes(self):
        with self.assertRaises(ValueError):
            hash_from_bytes(b"too-short")


if __name__ == "__main__":
    unittest.main()
