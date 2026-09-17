"""Import/construction smoke tests for the Postgres and Redis adapters.

These do NOT exercise real database behavior -- no PostgreSQL or Redis
instance is available in this environment (see loomhash/storage/postgres.py
and redis_cache.py). They only confirm the drivers import and the adapter
classes construct without attempting a connection, since psycopg.connect()
and redis.Redis() are both lazy. Integration coverage against live services
remains Pending in docs/verification-checklist.md.
"""

import unittest

import redis

from loomhash.storage.postgres import PostgresStorageBackend
from loomhash.storage.redis_cache import RedisEnrollmentCache


class TestAdapterConstruction(unittest.TestCase):
    def test_postgres_backend_constructs_without_connecting(self):
        backend = PostgresStorageBackend(conninfo="postgresql://localhost/does-not-exist")
        self.assertIsInstance(backend, PostgresStorageBackend)

    def test_redis_cache_constructs_without_connecting(self):
        client = redis.Redis(host="localhost", port=6379)
        cache = RedisEnrollmentCache(client)
        self.assertIsInstance(cache, RedisEnrollmentCache)

    def test_redis_cache_key_format(self):
        self.assertEqual(
            RedisEnrollmentCache._key("alice"), "loomhash:enrollment:alice"
        )


if __name__ == "__main__":
    unittest.main()
