"""Tests for loomhash.auth.rate_limiter."""

import time
import unittest

from loomhash.auth.rate_limiter import RateLimiter


class TestRateLimiter(unittest.TestCase):
    def test_under_limit_passes(self):
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        for _ in range(3):
            self.assertTrue(limiter.check("k1"))
            limiter.record("k1")

    def test_over_limit_blocked(self):
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        limiter.record("k1")
        limiter.record("k1")
        self.assertFalse(limiter.check("k1"))

    def test_different_keys_independent(self):
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        limiter.record("k1")
        self.assertFalse(limiter.check("k1"))
        self.assertTrue(limiter.check("k2"))  # k2 is unaffected

    def test_window_expiry_reopens(self):
        limiter = RateLimiter(max_requests=1, window_seconds=0.1)
        limiter.record("k1")
        self.assertFalse(limiter.check("k1"))
        time.sleep(0.15)
        self.assertTrue(limiter.check("k1"))

    def test_retry_after_is_positive_when_limited(self):
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        limiter.record("k1")
        self.assertGreater(limiter.retry_after("k1"), 0)

    def test_retry_after_is_zero_when_under_limit(self):
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        self.assertEqual(limiter.retry_after("k1"), 0.0)


if __name__ == "__main__":
    unittest.main()
