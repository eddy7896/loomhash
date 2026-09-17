"""Boundary checks for AUT-03/AUT-04 (docs/requirements.md).

51/256 = 0.19921875 <= 0.20 -> match. 52/256 = 0.203125 > 0.20 -> no match.
This is the exact boundary derived in docs/requirements.md from the
specified `distance <= 0.20` rule.
"""

import unittest

from loomhash.cryptography import HASH_BITS, hamming_distance, is_match


def hash_with_n_bits_set(n: int) -> int:
    return (1 << n) - 1  # lowest n bits set, n <= HASH_BITS


class TestHammingDistance(unittest.TestCase):
    def test_identical_hashes_have_zero_distance(self):
        self.assertEqual(hamming_distance(12345, 12345), 0.0)

    def test_known_bit_difference(self):
        h_a = 0
        h_b = hash_with_n_bits_set(51)
        self.assertAlmostEqual(hamming_distance(h_a, h_b), 51 / HASH_BITS)

    def test_fully_different_hashes_have_distance_one(self):
        h_a = 0
        h_b = (1 << HASH_BITS) - 1
        self.assertEqual(hamming_distance(h_a, h_b), 1.0)


class TestIsMatch(unittest.TestCase):
    def test_51_differing_bits_matches(self):
        h_a = 0
        h_b = hash_with_n_bits_set(51)
        self.assertAlmostEqual(hamming_distance(h_a, h_b), 0.19921875)
        self.assertTrue(is_match(h_a, h_b))

    def test_52_differing_bits_does_not_match(self):
        h_a = 0
        h_b = hash_with_n_bits_set(52)
        self.assertAlmostEqual(hamming_distance(h_a, h_b), 0.203125)
        self.assertFalse(is_match(h_a, h_b))

    def test_exact_threshold_boundary_is_inclusive(self):
        # distance <= 0.20 must accept; 51/256 is the largest bit-count <= 0.20.
        h_a = 0
        h_b = hash_with_n_bits_set(51)
        self.assertLessEqual(hamming_distance(h_a, h_b), 0.20)
        self.assertTrue(is_match(h_a, h_b, threshold=0.20))


if __name__ == "__main__":
    unittest.main()
