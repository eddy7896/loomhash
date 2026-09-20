"""In-memory sliding-window rate limiter for authentication attempts.

Per-API-key rate limiting on /v1/authenticate to prevent brute-force attacks.
Uses a simple sliding-window counter: track timestamps of recent requests and
count those within the current window.

This is an in-memory implementation — state is lost on restart and not shared
across processes. For a multi-process deployment, replace with a Redis-backed
implementation sharing the existing Redis dependency.
"""

from __future__ import annotations

import time
from collections import defaultdict


class RateLimiter:
    """Sliding-window rate limiter.

    Args:
        max_requests: Maximum allowed requests per window.
        window_seconds: Window duration in seconds.
    """

    def __init__(
        self,
        max_requests: int = 10,
        window_seconds: float = 60.0,
    ) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._timestamps: dict[str, list[float]] = defaultdict(list)

    def check(self, key_id: str) -> bool:
        """Return True if the request is within rate limits, False if exceeded."""
        now = time.monotonic()
        cutoff = now - self.window_seconds
        # Prune expired timestamps
        timestamps = self._timestamps[key_id]
        self._timestamps[key_id] = [t for t in timestamps if t > cutoff]
        return len(self._timestamps[key_id]) < self.max_requests

    def record(self, key_id: str) -> None:
        """Record a request for the given key_id."""
        self._timestamps[key_id].append(time.monotonic())

    def retry_after(self, key_id: str) -> float:
        """Seconds until the next request would be allowed for key_id."""
        timestamps = self._timestamps[key_id]
        if not timestamps or len(timestamps) < self.max_requests:
            return 0.0
        # Earliest timestamp in the window determines when a slot opens
        oldest_in_window = sorted(timestamps)[0]
        return max(0.0, oldest_in_window + self.window_seconds - time.monotonic())
