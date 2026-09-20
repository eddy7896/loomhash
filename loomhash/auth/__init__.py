"""Caller authentication: API key management and rate limiting.

Provides the auth dependency for the API Gateway and the key store
backends. PostgresAPIKeyStore is intentionally not imported here to avoid
requiring psycopg at import time (same pattern as loomhash.storage).
"""

from .auth import APIKey, generate_api_key, parse_key_id, verify_api_key
from .key_store import APIKeyStore, InMemoryAPIKeyStore
from .rate_limiter import RateLimiter

__all__ = [
    "APIKey",
    "APIKeyStore",
    "InMemoryAPIKeyStore",
    "RateLimiter",
    "generate_api_key",
    "parse_key_id",
    "verify_api_key",
]
